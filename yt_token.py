"""One-time YouTube OAuth (desktop client, loopback + PKCE). Needs client_secret.json in this folder.
Writes YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, YT_CHANNEL_ID to .env."""
import base64, hashlib, http.server, json, secrets, threading, urllib.parse, urllib.request, webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly"


def set_env(k, v):
    f = ROOT / ".env"
    lines = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
    f.write_text("\n".join([l for l in lines if not l.startswith(k + "=")] + [f"{k}={v}"]) + "\n", encoding="utf-8")


def main():
    cs = json.loads((ROOT / "client_secret.json").read_text(encoding="utf-8"))
    cs = cs.get("installed") or cs.get("web")
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            self.send_response(200); self.end_headers(); self.wfile.write(b"You can close this tab.")
        def log_message(self, *a): pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    webbrowser.open("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cs["client_id"], "redirect_uri": redirect, "response_type": "code", "scope": SCOPES,
        "code_challenge": challenge, "code_challenge_method": "S256", "access_type": "offline", "prompt": "consent"}))
    t = threading.Thread(target=srv.handle_request); t.start(); t.join(300)
    tok = json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", urllib.parse.urlencode({
        "code": got["code"][0], "client_id": cs["client_id"], "client_secret": cs["client_secret"], "redirect_uri": redirect,
        "grant_type": "authorization_code", "code_verifier": verifier}).encode())).read())
    ch = json.loads(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
                                                                  headers={"Authorization": "Bearer " + tok["access_token"]})).read())["items"][0]["id"]
    for k, v in {"YT_CLIENT_ID": cs["client_id"], "YT_CLIENT_SECRET": cs["client_secret"], "YT_REFRESH_TOKEN": tok["refresh_token"], "YT_CHANNEL_ID": ch}.items():
        set_env(k, v)
    print("ok: channel", ch)


if __name__ == "__main__":
    main()
