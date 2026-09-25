"""Telegram remote control: long-polling thread inside Studio (no webhook, no open port).
Setup: @BotFather -> TELEGRAM_BOT_TOKEN in .env -> start Studio -> send /start (first chat becomes the owner chat)."""
import json, os, re, subprocess, sys, threading, time, urllib.parse, urllib.request
from pathlib import Path

from viral import load_env

ROOT = Path(__file__).parent
PENDING = {}  # chat confirmation: token -> callable


def api(tok, method, **params):
    data = urllib.parse.urlencode({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in params.items()}).encode()
    return json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/{method}", data, timeout=70).read())


def set_chat(cid):
    f = ROOT / ".env"
    lines = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
    f.write_text("\n".join([l for l in lines if not l.startswith("TELEGRAM_CHAT_ID=")] + [f"TELEGRAM_CHAT_ID={cid}"]) + "\n", encoding="utf-8")


def yesno(tok, chat, text, action):
    key = str(int(time.time() * 1000))
    PENDING[key] = action
    api(tok, "sendMessage", chat_id=chat, text=text, reply_markup={"inline_keyboard": [[
        {"text": "Evet", "callback_data": "y:" + key}, {"text": "Hayır", "callback_data": "n:" + key}]]})


def send_media(tok, chat, st, slides=False):
    out = ROOT / "output" / st["post"]
    items = [("cover.jpg", "sendPhoto", "photo"), ("reel.mp4", "sendVideo", "video")]
    if slides:
        items = [(f.name, "sendPhoto", "photo") for f in sorted(out.glob("slide_*.png"))[:10]]
    for name, method, field in items:
        p = out / name
        if p.exists():
            boundary = "----b" + str(time.time_ns())
            body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat}\r\n"
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{name}\"\r\n\r\n").encode() + p.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
            try:
                urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{tok}/{method}", body,
                                       {"Content-Type": "multipart/form-data; boundary=" + boundary}), timeout=120)
            except Exception:  # noqa: BLE001
                pass


def handle(studio, tok, chat, text):
    t = text.strip().lower()
    runs = studio.list_runs()
    waiting = next((r for r in runs if r["status"] == "waiting" and r["kind"] != "scan"), None)
    if t in ("/start", "yardım", "yardim", "help"):
        return "Komutlar: tara · adaylar · 3 (numara ile seç) · durum · önizle · yayınla · reddet · revize: <not> · bir link (viral Reel)"
    if t in ("tara", "/tara"):
        return "Tarama başladı." if studio.start_scan("Telegram") else "Zaten bir tarama çalışıyor."
    if t in ("adaylar", "/adaylar"):
        cs = studio.latest_candidates().get("candidates", [])[:12]
        return "\n".join(f"{i+1}. [{c['kind']}] {c['title']} ★{c['score']}" for i, c in enumerate(cs)) or "Aday yok."
    if t.isdigit() or t.endswith("seç") or t.endswith("sec"):
        cs = studio.latest_candidates().get("candidates", [])
        idx = int("".join(ch for ch in t if ch.isdigit()) or 0) - 1
        scan = next((r for r in runs if r["kind"] == "scan" and r["status"] in ("waiting", "done")), None)
        if 0 <= idx < len(cs) and scan:
            c = cs[idx]
            yesno(tok, chat, f"Seçilsin mi?\n{c['title']}", lambda: studio.select_candidate(scan["id"], c["id"]))
            return ""
        return "Geçersiz numara."
    if t in ("durum", "/durum"):
        return "\n".join(f"{r['kind']} {r.get('post') or ''} — {r['status']}" for r in runs[:5]) or "Çalışma yok."
    if t in ("önizle", "onizle") and waiting:
        send_media(tok, chat, studio.load_run(waiting["id"])); return "Önizleme gönderildi."
    if t in ("yayınla", "yayinla") and waiting:
        yesno(tok, chat, "Yayınlansın mı?", lambda: studio.decide(waiting["id"], "approve")); return ""
    if t in ("reddet",) and waiting:
        yesno(tok, chat, "Reddedilsin mi?", lambda: studio.decide(waiting["id"], "reject")); return ""
    if t.startswith("revize:") and waiting:
        studio.decide(waiting["id"], "revise", text.split(":", 1)[1].strip()); return "Revizyon başladı."
    if t.startswith("http"):
        yesno(tok, chat, "Bu linkten viral Reel başlatılsın mı?", lambda: studio.enqueue(studio.new_run("clip", url=text.strip())["id"])); return ""
    return None  # free text goes to the conversational agent (converse)


HIST = []  # recent conversation (role, text), kept in memory


def _state(studio):
    from datetime import datetime
    runs = studio.list_runs()
    waiting = next((r for r in runs if r["status"] == "waiting" and r["kind"] != "scan"), None)
    w = None
    if waiting:
        cp = studio.content_path(waiting) if waiting.get("post") else None
        c = json.loads(cp.read_text(encoding="utf-8")) if cp and cp.exists() else {}
        w = {"kind": waiting["kind"], "post": waiting.get("post"), "topic": c.get("topic") or c.get("hook"),
             "headline": (c.get("cover") or {}).get("headline"), "caption": (c.get("caption") or "")[:300], "credit": c.get("credit")}
    cands = studio.latest_candidates().get("candidates", [])[:15]
    vs = ROOT / "research" / "viral_social.json"
    viral = json.loads(vs.read_text(encoding="utf-8")).get("items", [])[:5] if vs.exists() else []
    return {
        "now": datetime.now().strftime("%Y-%m-%d %H:%M"), "next_scan": studio.next_slot(), "approval": studio.settings()["approval"],
        "waiting": json.dumps(w, ensure_ascii=False) if w else "none",
        "runs": json.dumps([{k: r.get(k) for k in ("kind", "status", "post")} for r in runs[:6]], ensure_ascii=False),
        "candidates": "\n".join(f"{i+1}. [{c['kind']}] {c['title']} (score {c['score']}) - {c.get('summary_tr', '')[:120]}" for i, c in enumerate(cands)) or "none",
        "viral": json.dumps([{"platform": v["platform"], "creator": v["creator"], "views": v["views"], "url": v["url"]} for v in viral], ensure_ascii=False),
        "vscan": json.dumps(studio.VSCAN, ensure_ascii=False),
        "errors": json.dumps(_errors(studio, runs), ensure_ascii=False),
        "slots": ", ".join(studio.settings()["slots"]),
    }


def _errors(studio, runs):
    out = []
    for r in runs[:6]:
        if r["status"] == "error":
            st = studio.load_run(r["id"])
            for n, v in st["nodes"].items():
                if v["status"] == "error":
                    out.append({"run": r.get("post") or r["id"], "step": n, "error": (v.get("error") or "")[-160:]})
    return out


def ask_agent(studio, text):
    st = _state(studio)
    hist = "\n".join(f"{r}: {t}" for r, t in HIST[-8:]) or "(new conversation)"
    prompt = (ROOT / "prompts" / "chat.md").read_text(encoding="utf-8").format(history=hist, message=text, **st)
    r = subprocess.run(["claude", "-p", "--model", "haiku", "--allowedTools", "Read"], input=prompt, capture_output=True, text=True,
                       encoding="utf-8", cwd=ROOT, shell=(os.name == "nt"), timeout=120)
    out = (r.stdout or "").strip()
    m = re.search(r"\{.*\}", out, re.S)
    try:
        d = json.loads(m.group(0)) if m else {"reply": out[:1500] or "Bir şey ters gitti, tekrar dener misin?", "action": None}
    except ValueError:
        d = {"reply": out[:1500], "action": None}
    return d


CONFIRM = {"select", "approve", "reject", "clip"}


def run_action(studio, tok, chat, act):
    name, a = act.get("name"), act.get("args") or {}
    runs = studio.list_runs()
    waiting = next((r for r in runs if r["status"] == "waiting" and r["kind"] != "scan"), None)
    scan = next((r for r in runs if r["kind"] == "scan" and r["status"] in ("waiting", "done")), None)
    cs = studio.latest_candidates().get("candidates", [])
    say = lambda t: api(tok, "sendMessage", chat_id=chat, text=t)  # noqa: E731
    if name == "scan":
        studio.start_scan("Telegram")
    elif name == "viral_scan":
        studio.viral_scan()
    elif name == "retry":
        failed = next((r for r in runs if r["status"] == "error"), None)
        studio.decide(failed["id"], "retry") if failed else say("Hatalı bir çalışma yok.")
    elif name == "cancel":
        for r in runs:
            if r["status"] == "running":
                studio.decide(r["id"], "cancel")
    elif name == "set_approval":
        studio.save_settings({"approval": bool(a.get("value"))})
    elif name in ("preview", "send_slides"):
        send_approval_panel(studio, tok, chat)
    elif name == "show_candidates":
        send_candidates(studio, tok, chat)
    elif name == "show_viral":
        send_viral(studio, tok, chat)
    elif name == "history":
        send_history(studio, tok, chat)
    elif name == "performance":
        send_performance(studio, tok, chat)
    elif name == "refresh_metrics":
        threading.Thread(target=lambda: studio.py("metrics.py"), daemon=True).start()
    elif name == "status":
        show_status(studio, tok, chat)
    elif name == "set_slots":
        slots = [x for x in (a.get("slots") or []) if isinstance(x, str) and len(x) == 5]
        if slots:
            studio.save_settings({"slots": slots})
    elif name == "revise":
        studio.decide(waiting["id"], "revise", str(a.get("note", ""))) if waiting else say("Revize edilecek bekleyen içerik yok.")
    elif name == "select":
        idx = int(a.get("index", 0)) - 1
        if scan and 0 <= idx < len(cs):
            c = cs[idx]
            yesno(tok, chat, f"Bunu seçeyim mi?\n{c['title']}", lambda: studio.select_candidate(scan["id"], c["id"]))
        else:
            say("Bu numaralı bir aday bulamadım.")
    elif name in ("approve", "reject"):
        if waiting:
            yesno(tok, chat, "Yayınlayayım mı?" if name == "approve" else "Reddedeyim mi?", lambda: studio.decide(waiting["id"], name))
        else:
            say("Onay bekleyen bir içerik yok.")
    elif name == "clip" and str(a.get("url", "")).startswith("http"):
        yesno(tok, chat, "Bu linkten viral Reel başlatayım mı?",
              lambda: studio.enqueue(studio.new_run("clip", url=a["url"], credit=a.get("credit", ""), file="")["id"]))


def is_exact_command(text):
    t = text.strip().lower()
    return (t.isdigit() or t.endswith("seç") or t.endswith("sec") or t in ("yayınla", "yayinla", "reddet") or t.startswith("http"))


def converse(studio, tok, chat, text):
    api(tok, "sendChatAction", chat_id=chat, action="typing")
    d = ask_agent(studio, text)
    reply = (d.get("reply") or "").strip()
    HIST.append(("owner", text))
    HIST.append(("assistant", reply))
    if reply:
        api(tok, "sendMessage", chat_id=chat, text=reply[:3500])
    act = d.get("action")
    if isinstance(act, dict) and act.get("name"):
        try:
            run_action(studio, tok, chat, act)
        except Exception as e:  # noqa: BLE001
            api(tok, "sendMessage", chat_id=chat, text="İşlemi yaparken hata oldu: " + str(e)[:150])


LISTS_F = ROOT / "runs" / "tg_lists.json"


def _load_lists():
    try:
        return json.loads(LISTS_F.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"cand": [], "vid": []}


class _Lists(dict):
    """What the last shown lists contained (button callbacks refer to positions). Persisted so buttons survive restarts."""
    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        LISTS_F.parent.mkdir(exist_ok=True)
        LISTS_F.write_text(json.dumps(dict(self), ensure_ascii=False), encoding="utf-8")

    def __getitem__(self, k):
        self.update(_load_lists())
        return super().__getitem__(k)


LISTS = _Lists(_load_lists())
MENU = {"keyboard": [["📋 Adaylar", "🎬 Viral videolar"], ["🔎 Tara", "🔍 Viral ara"], ["🖼 Önizle / Onay", "📊 Durum"], ["📈 Performans", "🗂 Geçmiş"]],
        "resize_keyboard": True, "is_persistent": True}
NAMES = {"tiktok": "TikTok", "x": "X", "instagram": "Instagram"}


def fm(n):
    n = n or 0
    return f"{n/1e6:.1f} M" if n >= 1e6 else f"{round(n/1e3)} B" if n >= 1e3 else str(n)


def chunks(lines, limit=3500):
    out, cur = [], ""
    for ln in lines:
        if len(cur) + len(ln) + 1 > limit:
            out.append(cur); cur = ""
        cur += ln + "\n"
    return out + ([cur] if cur else [])


def grid(prefix, n, per=5, label=lambda i: str(i + 1)):
    rows = [[{"text": label(i), "callback_data": f"{prefix}:{i}"} for i in range(r, min(r + per, n))] for r in range(0, n, per)]
    return {"inline_keyboard": rows}


def say(tok, chat, text, **kw):
    return api(tok, "sendMessage", chat_id=chat, text=text[:4000], disable_web_page_preview=True, **kw)


def send_candidates(studio, tok, chat):
    cs = studio.latest_candidates().get("candidates", [])[:15]
    scan = next((r for r in studio.list_runs() if r["kind"] == "scan"), None)
    if not cs:
        return say(tok, chat, "Henüz aday yok. “Tara” de, yeni tarama başlatayım.")
    LISTS["cand"] = [c["id"] for c in cs]
    tag = {"news": "HABER", "stage": "AŞAMA", "problem": "SORUN", "quote": "ALINTI", "evergreen": "İPUCU", "playbook": "PLAYBOOK"}
    lines = [f"📋 Carousel adayları ({scan['created'][5:16].replace('T', ' ') if scan else ''})", ""]
    for i, c in enumerate(cs):
        lines += [f"{i+1}. [{tag.get(c['kind'], c['kind'])}] ★{c['score']} {c['title']}", f"   {c.get('summary_tr', '')[:170]}", ""]
    parts = chunks(lines)
    for k, part in enumerate(parts):
        say(tok, chat, part, **({"reply_markup": grid("c", len(cs))} if k == len(parts) - 1 else {}))
    say(tok, chat, "Seçmek için numaraya dokun ya da “2 numarayı seç” de.")


def send_viral(studio, tok, chat):
    f = ROOT / "research" / "viral_social.json"
    items = json.loads(f.read_text(encoding="utf-8")).get("items", [])[:10] if f.exists() else []
    if not items:
        return say(tok, chat, "Doğrulanmış viral video yok. “Viral ara” de, aratayım (2-3 dk).")
    LISTS["vid"] = items
    lines = ["🎬 Doğrulanmış viral videolar (100 B+ izlenme)", ""]
    for i, v in enumerate(items):
        lines += [f"{i+1}. {NAMES.get(v['platform'], v['platform'])} · {fm(v['views'])} izlenme · {round(v.get('duration') or 0)} sn · @{v['creator']}",
                  f"   {(v.get('title') or '')[:110]}", f"   {v['url']}", ""]
    parts = chunks(lines)
    for k, part in enumerate(parts):
        say(tok, chat, part, **({"reply_markup": grid("v", len(items), label=lambda i: f"🎬 {i+1}")} if k == len(parts) - 1 else {}))


def send_approval_panel(studio, tok, chat):
    waiting = next((r for r in studio.list_runs() if r["status"] == "waiting" and r["kind"] != "scan"), None)
    if not waiting:
        return say(tok, chat, "Şu an onay bekleyen bir içerik yok.")
    st = studio.load_run(waiting["id"])
    send_media(tok, chat, st, slides=(st["kind"] == "post"))
    cp = studio.content_path(st)
    c = json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {}
    qa = {}
    qf = studio.run_dir(st["id"]) / "qa.json"
    if qf.exists():
        qa = json.loads(qf.read_text(encoding="utf-8"))
    body = f"📝 Açıklama:\n{(c.get('caption') or '')[:900]}\n\n" + (f"👁 QA: {'✓ ' if qa.get('ok') else '⚠ '}{qa.get('summary_tr', '')[:400]}" if qa else "")
    say(tok, chat, body, reply_markup={"inline_keyboard": [[{"text": "✅ Yayınla", "callback_data": "a:approve"}, {"text": "❌ Reddet", "callback_data": "a:reject"}]]})
    say(tok, chat, "Değiştirmek istersen yaz ya da söyle, örneğin: “başlığı daha sıcak yap”.")


def send_history(studio, tok, chat):
    f = ROOT / "publish_log.jsonl"
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()][-6:] if f.exists() else []
    if not rows:
        return say(tok, chat, "Henüz yayınlanmış bir şey yok.")
    lines = ["🗂 Son yayınlar", ""]
    for r in reversed(rows):
        links = " · ".join(f"{k.split('_')[0].upper()}: {r[k]}" for k in ("ig_url", "ig_reel_url", "fb_url", "fb_reel_url", "yt_url") if r.get(k))
        lines += [f"• {r['date'][5:16].replace('T', ' ')} — {str(r.get('topic') or r['post'])[:70]}", f"  {links}", ""]
    for part in chunks(lines):
        say(tok, chat, part)


def send_performance(studio, tok, chat):
    f = ROOT / "runs" / "metrics.json"
    m = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    if not m or not m.get("posts"):
        return say(tok, chat, "Henüz performans verisi yok. “Performansı yenile” dersen toplarım (Meta izinleri eksikse bazı sayılar boş kalır).")
    lines = [f"📈 Performans (güncelleme: {m.get('updated', '')[:16]})", ""]
    for p_ in m["posts"][-6:]:
        ig, yt = p_.get("instagram") or {}, p_.get("youtube") or {}
        lines.append(f"• {str(p_.get('topic') or p_['post'])[:50]} — IG erişim {ig.get('reach', '-')}, kayıt {ig.get('saved', '-')}, YT {yt.get('viewCount', '-')}")
    if m.get("needs"):
        lines += ["", "Eksik: " + "; ".join(m["needs"])[:300]]
    say(tok, chat, "\n".join(lines))


def show_status(studio, tok, chat):
    runs = studio.list_runs()[:6]
    icon = {"done": "✅", "error": "❌", "waiting": "⏸", "running": "⏳", "rejected": "🚫", "queued": "🕒", "cancelled": "⛔"}
    lines = ["📊 Durum", f"Sonraki tarama: {studio.next_slot()} · Onay: {'açık' if studio.settings()['approval'] else 'kapalı'}", ""]
    for r in runs:
        lines.append(f"{icon.get(r['status'], '•')} {r['kind']} {r.get('post') or r['id'][-10:]} — {r['status']}")
        if r["status"] == "error":
            node = next((n for n, v in studio.load_run(r["id"])["nodes"].items() if v["status"] == "error"), None)
            if node:
                lines.append(f"   ↳ hata: {node}")
    say(tok, chat, "\n".join(lines))


def on_callback(studio, tok, chat, data):
    kind, _, arg = data.partition(":")
    runs = studio.list_runs()
    waiting = next((r for r in runs if r["status"] == "waiting" and r["kind"] != "scan"), None)
    scan = next((r for r in runs if r["kind"] == "scan" and r["status"] in ("waiting", "done")), None)
    if kind == "c":
        i = int(arg)
        if scan and i < len(LISTS["cand"]):
            cid = LISTS["cand"][i]
            title = next((c["title"] for c in studio.latest_candidates()["candidates"] if c["id"] == cid), cid)
            yesno(tok, chat, f"Bunu seçeyim mi?\n{title}", lambda: studio.select_candidate(scan["id"], cid))
    elif kind == "v":
        v = LISTS["vid"][int(arg)]
        yesno(tok, chat, f"Bu videodan Reel yapayım mı?\n@{v['creator']} · {fm(v['views'])} izlenme",
              lambda: studio.enqueue(studio.new_run("clip", url=v["url"], credit=f"@{v['creator']} on {NAMES.get(v['platform'], '')}", file="")["id"]))
    elif kind == "a" and waiting:
        yesno(tok, chat, "Yayınlayayım mı?" if arg == "approve" else "Reddedeyim mi?", lambda: studio.decide(waiting["id"], arg))


BUTTONS = {"📋 adaylar": send_candidates, "🎬 viral videolar": send_viral, "🖼 önizle / onay": send_approval_panel, "📊 durum": show_status,
           "📈 performans": send_performance, "🗂 geçmiş": send_history}


def press_button(studio, tok, chat, text):
    t = text.strip().lower()
    if t in BUTTONS:
        BUTTONS[t](studio, tok, chat)
        return True
    if t == "🔎 tara":
        say(tok, chat, "Tarama başladı." if studio.start_scan("Telegram") else "Zaten bir tarama çalışıyor.")
        return True
    if t == "🔍 viral ara":
        say(tok, chat, "Viral video araması başladı (2-3 dk)." if studio.viral_scan() else "Zaten bir arama çalışıyor.")
        return True
    return False


def on_notify(studio, tok, chat, m):
    say(tok, chat, m)
    try:
        if m.startswith("Seni bekliyor: pick"):
            send_candidates(studio, tok, chat)
        elif m.startswith("Seni bekliyor: approve"):
            send_approval_panel(studio, tok, chat)
        elif m.startswith("Viral video listesi güncellendi"):
            send_viral(studio, tok, chat)
    except Exception as e:  # noqa: BLE001
        say(tok, chat, "Liste gönderilemedi: " + str(e)[:100])


def run(studio):
    env = load_env()
    tok = env.get("TELEGRAM_BOT_TOKEN")
    if not tok:
        return
    studio._notifier.append(lambda m: env.get("TELEGRAM_CHAT_ID") and on_notify(studio, tok, env["TELEGRAM_CHAT_ID"], m))
    offset = 0
    while True:
        try:
            for u in api(tok, "getUpdates", offset=offset, timeout=50).get("result", []):
                offset = u["update_id"] + 1
                cb = u.get("callback_query")
                msg = u.get("message") or (cb or {}).get("message")
                if not msg:
                    continue
                chat = str(msg["chat"]["id"])
                if not env.get("TELEGRAM_CHAT_ID"):
                    set_chat(chat); env["TELEGRAM_CHAT_ID"] = chat
                if chat != env["TELEGRAM_CHAT_ID"]:
                    continue
                if cb:
                    yn, key = cb["data"].split(":", 1)
                    try:
                        if yn in ("y", "n"):
                            act = PENDING.pop(key, None)
                            if yn == "y" and act:
                                act(); api(tok, "sendMessage", chat_id=chat, text="Tamam, başladı.")
                        else:
                            on_callback(studio, tok, chat, cb["data"])
                    except Exception as e:  # noqa: BLE001
                        say(tok, chat, "İşlem hatası: " + str(e)[:120])
                    api(tok, "answerCallbackQuery", callback_query_id=cb["id"])
                    continue
                text = msg.get("text")
                media = msg.get("voice") or msg.get("audio") or msg.get("video_note")
                if media:
                    api(tok, "sendChatAction", chat_id=chat, action="typing")
                    try:
                        info = api(tok, "getFile", file_id=media["file_id"])["result"]
                        f = ROOT / "runs" / ("voice_in" + Path(info["file_path"]).suffix)
                        f.write_bytes(urllib.request.urlopen(f"https://api.telegram.org/file/bot{tok}/{info['file_path']}", timeout=60).read())
                        import stt
                        text = stt.transcribe(f)
                    except Exception as e:  # noqa: BLE001
                        api(tok, "sendMessage", chat_id=chat, text="Sesi yazıya çeviremedim: " + str(e)[:120])
                        continue
                    if not text:
                        api(tok, "sendMessage", chat_id=chat, text="Sesi anlayamadım, biraz daha net tekrar söyler misin?")
                        continue
                    api(tok, "sendMessage", chat_id=chat, text="🎤 Anladığım: " + text)
                if text and text.strip().lower() in ("/start", "/menu", "menü", "menu"):
                    say(tok, chat, "Merhaba! Aşağıdaki menüden ya da doğrudan yazarak/konuşarak yönetebilirsin.", reply_markup=MENU)
                    continue
                if text and press_button(studio, tok, chat, text):
                    continue
                if text:
                    reply = handle(studio, tok, chat, text)
                    if reply:
                        api(tok, "sendMessage", chat_id=chat, text=reply)
                    elif reply is None:
                        converse(studio, tok, chat, text)
        except Exception:  # noqa: BLE001
            time.sleep(5)
