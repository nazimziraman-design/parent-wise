"""Telegram remote control: long-polling thread inside Studio (no webhook, no open port).
Setup: @BotFather -> TELEGRAM_BOT_TOKEN in .env -> start Studio -> send /start (first chat becomes the owner chat)."""
import json, os, subprocess, sys, time, urllib.parse, urllib.request
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


def send_media(tok, chat, st):
    out = ROOT / "output" / st["post"]
    for name, method, field in (("cover.jpg", "sendPhoto", "photo"), ("reel.mp4", "sendVideo", "video")):
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
        return "Tarama başladı." if studio.start_scan() else "Zaten bir tarama çalışıyor."
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
            return None
        return "Geçersiz numara."
    if t in ("durum", "/durum"):
        return "\n".join(f"{r['kind']} {r.get('post') or ''} — {r['status']}" for r in runs[:5]) or "Çalışma yok."
    if t in ("önizle", "onizle") and waiting:
        send_media(tok, chat, studio.load_run(waiting["id"])); return "Önizleme gönderildi."
    if t in ("yayınla", "yayinla") and waiting:
        yesno(tok, chat, "Yayınlansın mı?", lambda: studio.decide(waiting["id"], "approve")); return None
    if t in ("reddet",) and waiting:
        yesno(tok, chat, "Reddedilsin mi?", lambda: studio.decide(waiting["id"], "reject")); return None
    if t.startswith("revize:") and waiting:
        studio.decide(waiting["id"], "revise", text.split(":", 1)[1].strip()); return "Revizyon başladı."
    if t.startswith("http"):
        yesno(tok, chat, "Bu linkten viral Reel başlatılsın mı?", lambda: studio.enqueue(studio.new_run("clip", url=text.strip())["id"])); return None
    # free chat -> Claude, read-only
    state = json.dumps([{k: r.get(k) for k in ("kind", "status", "post")} for r in runs[:5]], ensure_ascii=False)
    prompt = (ROOT / "prompts" / "chat.md").read_text(encoding="utf-8").format(state=state, message=text)
    r = subprocess.run(["claude", "-p", "--allowedTools", "Read", "Glob", "Grep"], input=prompt, capture_output=True, text=True,
                       encoding="utf-8", cwd=ROOT, shell=(os.name == "nt"), timeout=180)
    return (r.stdout or "").strip()[:3500] or "Cevap alamadım."


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
        except Exception:  # noqa: BLE001
            time.sleep(5)
