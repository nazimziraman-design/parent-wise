"""Studio: local workflow engine + web UI (http://localhost:8787), standard library only.
Flows: scan (collect -> scout -> pick) | post (write -> ... -> log) | clip (fetch -> ... -> log). State lives in files (runs/<id>/)."""
import json, os, re, subprocess, sys, threading, time, traceback, urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import brand

ROOT = Path(__file__).parent
RUNS = ROOT / "runs"
NOWIN = 0x08000000 if os.name == "nt" else 0
PORT = 8787
LOCK = threading.RLock()
TOOLS = ["WebSearch", "WebFetch", "Read", "Write", "Edit", "Glob", "Grep", "Bash(python carousel.py:*)", "Bash(python reel.py:*)",
         "Bash(python news.py:*)", "Bash(python cover.py:*)", "Bash(python clip.py:*)"]

SCAN = [("trigger", "code"), ("collect", "code"), ("scout", "ai"), ("pick", "human")]
POST = [("write", "ai"), ("cover", "code"), ("carousel", "code"), ("video", "code"), ("qa", "ai"), ("approve", "human"),
        ("prepare", "publish"), ("upload", "publish"), ("ig_carousel", "publish"), ("fb_photos", "publish"), ("yt_short", "publish"), ("log", "code")]
CLIP = [("fetch", "code"), ("hook", "ai"), ("frame", "code"), ("qa", "ai"), ("approve", "human"), ("prepare", "publish"),
        ("upload", "publish"), ("ig_reel", "publish"), ("fb_reel", "publish"), ("log", "code")]
FLOWS = {"scan": SCAN, "post": POST, "clip": CLIP}
CANCEL = {}
_notifier = []


# ---------- settings / helpers ----------
def settings():
    f = RUNS / "settings.json"
    d = {"slots": brand.TIMEZONE_SLOTS, "approval": True, "last_slot": ""}
    if f.exists():
        d.update(json.loads(f.read_text(encoding="utf-8")))
    return d


def save_settings(d):
    RUNS.mkdir(exist_ok=True)
    (RUNS / "settings.json").write_text(json.dumps({**settings(), **d}, indent=1), encoding="utf-8")


def notify(msg):
    print("[notify]", msg)
    for fn in _notifier:
        try:
            fn(msg)
        except Exception:  # noqa: BLE001
            pass


def write_json_safe(path, data, tries=8):
    for i in range(tries):  # Windows file locks
        try:
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            return
        except OSError:
            time.sleep(0.2 * (i + 1))
    raise OSError("cannot write " + str(path))


def run_dir(rid):
    return RUNS / rid


def load_run(rid):
    return json.loads((run_dir(rid) / "state.json").read_text(encoding="utf-8"))


def save_run(st):
    with LOCK:
        write_json_safe(run_dir(st["id"]) / "state.json", st)


def new_run(kind, **extra):
    rid = f"{datetime.now():%Y%m%d-%H%M%S}-{kind}"
    run_dir(rid).mkdir(parents=True, exist_ok=True)
    st = {"id": rid, "kind": kind, "status": "queued", "created": datetime.now().isoformat(timespec="seconds"),
          "nodes": {n: {"type": t, "status": "idle", "attempts": [], "dur": None} for n, t in FLOWS[kind]}, "notes": "", **extra}
    save_run(st)
    return st


def list_runs():
    RUNS.mkdir(exist_ok=True)
    out = []
    for d in sorted(RUNS.iterdir(), reverse=True):
        if (d / "state.json").exists():
            out.append(load_run(d.name))
    return out


# ---------- candidates / repeat filter ----------
def posted_slugs():
    out = {"ids": set(), "urls": set(), "lines": []}
    for f in (ROOT / "content").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        out["ids"].add(f.stem.split("_", 1)[-1])
        out["urls"].update(u for u in d.get("sources", []) if not re.search(r"/(changelog|release-notes|news)/?$", u))
        out["lines"].append(f"{f.stem[:10]} · {d.get('topic')} · {d.get('cover', {}).get('headline', '')[:70]} · {f.stem} · keyword {d.get('cta_keyword', '-')}")
    return out


def load_candidates(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    seen = posted_slugs()
    keep = []
    for c in d.get("candidates", []):
        if c["id"] in seen["ids"]:
            continue
        if c.get("kind") == "news" and any(u in seen["urls"] for u in c.get("sources", [])):
            continue
        keep.append(c)
    d["candidates"] = keep
    return d


def latest_candidates():
    fs = sorted((ROOT / "research").glob("*_candidates.json"))
    return load_candidates(fs[-1]) if fs else {"candidates": []}


# ---------- claude ----------
def fill(name, **kw):
    return (ROOT / "prompts" / f"{name}.md").read_text(encoding="utf-8").format(**kw)


def run_claude(st, node, prompt, expect):
    d = run_dir(st["id"])
    (d / f"{node}.prompt.md").write_text(prompt, encoding="utf-8")
    cmd = ["claude", "-p", "--output-format", "stream-json", "--verbose", "--permission-mode", "acceptEdits", "--allowedTools", *TOOLS]
    log = open(d / f"{node}.log", "a", encoding="utf-8")
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                         cwd=ROOT, creationflags=NOWIN, shell=(os.name == "nt"))
    CANCEL[st["id"]] = p
    p.stdin.write(prompt); p.stdin.close()
    for line in p.stdout:
        try:
            ev = json.loads(line)
        except ValueError:
            log.write(line); continue
        for blk in (ev.get("message") or {}).get("content", []) if isinstance(ev.get("message"), dict) else []:
            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                arg = next(iter(blk.get("input", {}).values()), "")
                log.write(f"🔧 {blk['name']}: {str(arg)[:140]}\n")
            elif isinstance(blk, dict) and blk.get("type") == "text":
                log.write(blk["text"][:400] + "\n")
        log.flush()
    p.wait(); log.close()
    CANCEL.pop(st["id"], None)
    for path in ([expect] if not isinstance(expect, list) else expect):
        if not Path(path).exists():
            raise RuntimeError(f"claude did not write {path}")
        json.loads(Path(path).read_text(encoding="utf-8"))


def py(*args, log=None):
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       creationflags=NOWIN, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if log:
        Path(log).open("a", encoding="utf-8").write((r.stdout or "") + (r.stderr or ""))
    if r.returncode:
        raise RuntimeError(((r.stderr or "") + (r.stdout or ""))[-500:])
    return r.stdout


# ---------- node implementations ----------
def content_path(st):
    return ROOT / ("content/clips" if st["kind"] == "clip" else "content") / f"{st['post']}.json"


def set_info(st, name, text):
    st["nodes"][name]["info"] = str(text)[:160]


def pub_info(st):
    f = ROOT / "output" / str(st.get("post")) / "publish.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def do_node(st, name):
    d, day = run_dir(st["id"]), datetime.now().strftime("%Y-%m-%d")
    lg = d / f"{name}.log"
    k = st["kind"]
    if k == "scan":
        if name == "trigger":
            set_info(st, name, st.get("source", "Elle başlatıldı"))
            return "done"
        if name == "collect":
            py("news.py", log=lg)
            rf = json.loads((ROOT / "research" / f"{day}.json").read_text(encoding="utf-8"))
            set_info(st, name, f"{len(rf['items'])} haber · {len(rf['errors'])} hata")
            try:
                py("viral.py", log=lg)
            except Exception:  # noqa: BLE001
                pass
        elif name == "scout":
            slot = datetime.now().strftime("%H%M")
            out = ROOT / "research" / f"{day}_{slot}_candidates.json"
            posted = "\n".join(posted_slugs()["lines"]) or "(none yet)"
            prev = [c["id"] for f in (ROOT / "research").glob(f"{day}_*_candidates.json") for c in json.loads(f.read_text(encoding="utf-8")).get("candidates", [])]
            run_claude(st, name, fill("scout", date=day, research=ROOT / "research" / f"{day}.json", out=out, posted=posted, previous=prev), out)
            st["candidates_file"] = str(out)
            set_info(st, name, f"{len(json.loads(out.read_text(encoding='utf-8')).get('candidates', []))} aday")
        elif name == "pick":
            return "waiting"
    elif k == "post":
        post, cpath = st["post"], content_path(st)
        if name == "write":
            cand = st["candidate"]
            run_claude(st, name, fill("write", date=day, candidate=json.dumps(cand, ensure_ascii=False), out=cpath, proof=d / "write.json",
                                      note=st.get("notes", ""), recent_designs="\n".join(posted_slugs()["lines"][-6:])), [cpath, d / "write.json"])
            set_info(st, name, f"{len(json.loads(cpath.read_text(encoding='utf-8')).get('slides', []))} slayt")
        elif name == "cover":
            py("cover.py", cpath, log=lg)
            set_info(st, name, (json.loads(cpath.read_text(encoding="utf-8")).get("cover", {}).get("photo") or {}).get("file", "Flux / gradyan"))
        elif name == "carousel":
            py("carousel.py", cpath, log=lg)
        elif name == "video" and json.loads(cpath.read_text(encoding="utf-8")).get("video") is False:
            set_info(st, name, "bu format için kapalı")
        elif name == "video":
            py("reel.py", cpath, log=lg)
            set_info(st, name, json.loads(cpath.read_text(encoding="utf-8")).get("voice", ""))
        elif name == "qa":
            run_claude(st, name, fill("qa", content=cpath, outdir=ROOT / "output" / post, qa_out=d / "qa.json"), d / "qa.json")
            qa = json.loads((d / "qa.json").read_text(encoding="utf-8"))
            set_info(st, name, "sorun yok" if qa.get("ok") else "sorun var: " + str(qa.get("summary_tr", "")))
        elif name == "approve":
            qa = json.loads((d / "qa.json").read_text(encoding="utf-8")) if (d / "qa.json").exists() else {"ok": True}
            if settings()["approval"] or not qa.get("ok", True):
                if st["nodes"][name]["status"] != "approved":
                    return "waiting"
    elif k == "clip":
        cpath = content_path(st)
        if name == "fetch":
            out = py("clip.py", "fetch", st["url"], log=lg)
            st["post"] = "clip-" + json.loads(out.strip().splitlines()[-1])["id"]
            cpath = content_path(st)
        elif name == "hook":
            cid = st["post"]
            o = ROOT / "output" / cid
            run_claude(st, name, fill("hook", info=o / "meta.json", frames=o, out=cpath), cpath)
            c = json.loads(cpath.read_text(encoding="utf-8"))
            c.setdefault("id", cid.replace("clip-", "")); write_json_safe(cpath, c)
            if c.get("reject"):
                raise RuntimeError("rejected by hook step: " + c["reject"])
        elif name == "frame":
            py("clip.py", "frame", cpath, log=lg)
        elif name == "qa":
            run_claude(st, name, fill("clipqa", outdir=ROOT / "output" / st["post"], content=cpath, qa_out=d / "qa.json"), d / "qa.json")
        elif name == "approve":
            if settings()["approval"] and st["nodes"][name]["status"] != "approved":
                return "waiting"
    if name == "yt_short" and k == "post" and json.loads(content_path(st).read_text(encoding="utf-8")).get("video") is False:
        set_info(st, name, "video yok, atlandı")
        return "done"
    if name in ("prepare", "upload", "ig_carousel", "fb_photos", "yt_short", "ig_reel", "fb_reel"):
        py("publish.py", content_path(st), "--steps", name, log=lg)
        pi = pub_info(st)
        set_info(st, name, {"ig_carousel": pi.get("ig_url"), "ig_reel": pi.get("ig_reel_url"), "fb_photos": pi.get("fb_url"),
                            "fb_reel": pi.get("fb_reel_url"), "yt_short": pi.get("yt_url"),
                            "upload": "gh-pages'e yüklendi", "prepare": "JPEG + kapak hazır"}.get(name) or "tamam")
    elif name == "log":
        py("publish.py", content_path(st), "--steps", "log", log=lg)
        git_commit(st)
        with (ROOT / "stats" / "timings.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"run": st["id"], "kind": k, **{n: v["dur"] for n, v in st["nodes"].items()}}) + "\n")
        notify(f"Paylaşıldı: {st.get('post')}")
    return "done"


def git_commit(st):
    if not (ROOT / ".git").exists():
        return
    try:
        subprocess.run(["git", "add", "content", "research", "stats", "publish_log.jsonl"], cwd=ROOT, creationflags=NOWIN)
        subprocess.run(["git", "commit", "-m", f"post {st.get('post')}"], cwd=ROOT, creationflags=NOWIN, capture_output=True)
        subprocess.run(["git", "push"], cwd=ROOT, creationflags=NOWIN, capture_output=True)
    except Exception:  # noqa: BLE001
        pass


# ---------- engine ----------
def execute(rid):
    st = load_run(rid)
    st["status"] = "running"; save_run(st)
    for name, _t in FLOWS[st["kind"]]:
        node = st["nodes"][name]
        if node["status"] in ("done",):
            continue
        node.update(status="running"); t0 = time.time(); save_run(st)
        try:
            res = do_node(st, name)
        except Exception as e:  # noqa: BLE001
            node.update(status="error", error=str(e)[-400:]); node["attempts"].append({"error": str(e)[-200:], "dur": round(time.time() - t0, 1)})
            st["status"] = "error"; save_run(st)
            notify(f"Hata: {name} ({st['id']}) — {str(e)[-120:]}")
            return
        node["dur"] = round(time.time() - t0, 1)
        if res == "waiting":
            node["status"] = "waiting"; st["status"] = "waiting"; save_run(st)
            notify(f"Seni bekliyor: {name} ({st['id']})")
            return
        node["status"] = "done"; save_run(st)
    st["status"] = "done"; save_run(st)


QUEUE, QLOCK = [], threading.Condition()


def enqueue(rid):
    with QLOCK:
        if rid not in QUEUE:
            QUEUE.append(rid)
        QLOCK.notify()


def worker():
    while True:
        with QLOCK:
            while not QUEUE:
                QLOCK.wait()
            rid = QUEUE.pop(0)
        try:
            execute(rid)
        except Exception:  # noqa: BLE001
            traceback.print_exc()


def start_scan(source="Elle başlatıldı"):
    if any(r["kind"] == "scan" and r["status"] == "running" for r in list_runs()):
        return None
    st = new_run("scan", source=source)
    threading.Thread(target=execute, args=(st["id"],), daemon=True).start()
    return st["id"]


def recover():
    for r in list_runs():
        if r["status"] == "running":
            for n in r["nodes"].values():
                if n["status"] == "running":
                    n["status"] = "idle"
            r["status"] = "queued"; save_run(r)
            (threading.Thread(target=execute, args=(r["id"],), daemon=True).start() if r["kind"] == "scan" else enqueue(r["id"]))
        elif r["status"] == "queued" and r["kind"] != "scan":
            enqueue(r["id"])


def next_slot():
    now = datetime.now()
    slots = sorted(settings()["slots"])
    nxt = next((x for x in slots if x > now.strftime("%H:%M")), None)
    return (f"{now:%Y-%m-%d} " + nxt) if nxt else ("yarın " + slots[0])


def scheduler():
    while True:
        try:
            s = settings()
            now = datetime.now()
            due = [x for x in s["slots"] if x <= now.strftime("%H:%M")]
            if due:
                slot = f"{now:%Y-%m-%d} {max(due)}"
                if s.get("last_slot", "") < slot:
                    save_settings({"last_slot": slot})
                    start_scan("Zamanlayıcı · " + max(due))
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        time.sleep(30)


def select_candidate(scan_id, cand_id):
    scan = load_run(scan_id)
    cf = scan.get("candidates_file")
    cand = next((c for c in load_candidates(cf)["candidates"] if c["id"] == cand_id), None)
    if not cand:
        raise ValueError("candidate not available (already posted?)")
    post = f"{datetime.now():%Y-%m-%d}_{cand['id']}"
    st = new_run("post", post=post, candidate=cand, scan=scan_id)
    scan["nodes"]["pick"]["status"] = "done"; scan["status"] = "done"; save_run(scan)
    enqueue(st["id"])
    return st["id"]


def decide(rid, action, note=""):
    st = load_run(rid)
    if action == "approve":
        st["nodes"]["approve"]["status"] = "approved"; save_run(st); enqueue(rid)
    elif action == "revise":
        st["notes"] = note
        first = "write" if st["kind"] == "post" else "hook"
        seen = False
        for n, _ in FLOWS[st["kind"]]:
            seen = seen or n == first
            if seen:
                st["nodes"][n].update(status="idle", error=None)
        st["status"] = "queued"; save_run(st); enqueue(rid)
    elif action == "reject":
        cp = content_path(st)
        if cp.exists():
            cp.rename(run_dir(rid) / cp.name)
        st["status"] = "rejected"; save_run(st)
    elif action == "retry":
        for n in st["nodes"].values():
            if n["status"] == "error":
                n.update(status="idle", error=None)
        st["status"] = "queued"; save_run(st); enqueue(rid)
    elif action == "cancel":
        p = CANCEL.get(rid)
        if p:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], creationflags=NOWIN, capture_output=True)
        st["status"] = "cancelled"; save_run(st)


# ---------- HTTP ----------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, obj, code=200, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8" if "json" in ctype or "html" in ctype else ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/":
                return self.send((ROOT / "studio" / "index.html").read_bytes(), ctype="text/html")
            if u.path == "/api/state":
                return self.send({"runs": [{k: r.get(k) for k in ("id", "kind", "status", "created", "post", "scan")} for r in list_runs()[:30]],
                                  "settings": settings(), "brand": brand.BRAND, "next_scan": next_slot()})
            if u.path == "/api/scans":
                out = []
                for f in sorted((ROOT / "research").glob("*_candidates.json"), reverse=True):
                    d = json.loads(f.read_text(encoding="utf-8"))
                    out.append({"file": f.name, "label": f.name[5:10] + " " + f.name[11:13] + ":" + f.name[13:15], "count": len(d.get("candidates", []))})
                return self.send(out)
            if u.path == "/api/candidates":
                return self.send(load_candidates(ROOT / "research" / Path(q["file"][0]).name))
            if u.path == "/api/research":
                fs = sorted(p for p in (ROOT / "research").glob("????-??-??.json"))
                return self.send(json.loads(fs[-1].read_text(encoding="utf-8")) if fs else {"items": []})
            if u.path == "/api/timings":
                agg = {}
                for r in list_runs():
                    for n, v in r["nodes"].items():
                        if v.get("dur"):
                            agg.setdefault(r["kind"] + "/" + n, []).append(v["dur"])
                return self.send({k: {"avg": round(sum(v) / len(v), 1), "n": len(v)} for k, v in agg.items()})
            if u.path == "/api/artifacts":
                r = load_run(q["id"][0])
                post = r.get("post")
                out, d = {"files": [], "write": None, "qa": None}, run_dir(r["id"])
                if post:
                    od = ROOT / "output" / post
                    out["files"] = sorted(f.name for f in od.glob("*") if f.suffix in (".png", ".mp4", ".jpg") and not f.name.startswith("frame_"))
                    cp = content_path(r)
                    out["content"] = json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else None
                for k in ("write", "qa"):
                    f = d / f"{k}.json"
                    out[k] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
                return self.send(out)
            if u.path == "/api/run":
                return self.send(load_run(q["id"][0]))
            if u.path == "/api/log":
                f = run_dir(q["id"][0]) / f"{q['node'][0]}.log"
                return self.send({"log": f.read_text(encoding="utf-8")[-8000:] if f.exists() else ""})
            if u.path == "/api/metrics":
                f = RUNS / "metrics.json"
                return self.send(json.loads(f.read_text(encoding="utf-8")) if f.exists() else {})
            if u.path == "/api/viral":
                fs = sorted((ROOT / "research").glob("*_viral.json"))
                return self.send(json.loads(fs[-1].read_text(encoding="utf-8")) if fs else [])
            if u.path == "/api/history":
                f = ROOT / "publish_log.jsonl"
                return self.send([json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else [])
            if u.path.startswith("/file/"):  # output previews
                p = (ROOT / "output" / urllib.parse.unquote(u.path[6:])).resolve()
                if ROOT / "output" in p.parents and p.exists():
                    ct = {"png": "image/png", "jpg": "image/jpeg", "mp4": "video/mp4"}.get(p.suffix[1:], "application/octet-stream")
                    return self.send(p.read_bytes(), ctype=ct)
            self.send({"error": "not found"}, 404)
        except Exception as e:  # noqa: BLE001
            self.send({"error": str(e)}, 500)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        b = json.loads(self.rfile.read(n) or b"{}")
        p = urllib.parse.urlparse(self.path).path
        try:
            if p == "/api/scan":
                return self.send({"id": start_scan()})
            if p == "/api/select":
                return self.send({"id": select_candidate(b["scan"], b["candidate"])})
            if p == "/api/clip":
                st = new_run("clip", url=b["url"]); enqueue(st["id"]); return self.send({"id": st["id"]})
            if p in ("/api/approve", "/api/revise", "/api/reject", "/api/retry", "/api/cancel"):
                decide(b["id"], p.split("/")[-1], b.get("note", ""))
                if p.endswith("retry") and load_run(b["id"])["kind"] == "scan":
                    threading.Thread(target=execute, args=(b["id"],), daemon=True).start()
                return self.send({"ok": True})
            if p == "/api/settings":
                save_settings(b); return self.send(settings())
            if p == "/api/metrics/refresh":
                threading.Thread(target=lambda: py("metrics.py"), daemon=True).start(); return self.send({"ok": True})
            self.send({"error": "not found"}, 404)
        except Exception as e:  # noqa: BLE001
            self.send({"error": str(e)}, 400)


def main():
    RUNS.mkdir(exist_ok=True)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError:
        print("Studio already running"); return
    recover()
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=scheduler, daemon=True).start()
    try:
        import telegram_bot
        threading.Thread(target=telegram_bot.run, args=(sys.modules[__name__],), daemon=True).start()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    if "--no-browser" not in sys.argv:
        import webbrowser; webbrowser.open(f"http://localhost:{PORT}")
    print(f"Studio on http://localhost:{PORT}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
