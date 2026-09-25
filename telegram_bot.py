"""Telegram remote control: long-polling thread inside Studio (no webhook, no open port).
Setup: @BotFather -> TELEGRAM_BOT_TOKEN in .env -> start Studio -> send /start (first chat becomes the owner chat)."""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request
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
    }


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
        if waiting:
            send_media(tok, chat, studio.load_run(waiting["id"]), slides=(name == "send_slides"))
        else:
            say("Şu an onay bekleyen bir içerik yok.")
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


def run(studio):
    env = load_env()
    tok = env.get("TELEGRAM_BOT_TOKEN")
    if not tok:
        return
    studio._notifier.append(lambda m: env.get("TELEGRAM_CHAT_ID") and api(tok, "sendMessage", chat_id=env["TELEGRAM_CHAT_ID"], text=m))
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
                    act = PENDING.pop(key, None)
                    if yn == "y" and act:
                        act(); api(tok, "sendMessage", chat_id=chat, text="Tamam.")
                    api(tok, "answerCallbackQuery", callback_query_id=cb["id"])
                    continue
                text = msg.get("text")
                if msg.get("voice"):
                    fid = api(tok, "getFile", file_id=msg["voice"]["file_id"])["result"]["file_path"]
                    f = ROOT / "runs" / "voice.oga"
                    f.write_bytes(urllib.request.urlopen(f"https://api.telegram.org/file/bot{tok}/{fid}").read())
                    text = subprocess.run([sys.executable, str(ROOT / "stt.py"), str(f)], capture_output=True, text=True, encoding="utf-8").stdout.strip()
                if text:
                    reply = handle(studio, tok, chat, text)
                    if reply:
                        api(tok, "sendMessage", chat_id=chat, text=reply)
                    elif reply is None:
                        converse(studio, tok, chat, text)
        except Exception:  # noqa: BLE001
            time.sleep(5)
