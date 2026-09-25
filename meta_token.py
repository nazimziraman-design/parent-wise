"""One-time: exchange META_SHORT_TOKEN for a non-expiring Page token; writes META_PAGE_TOKEN, FB_PAGE_ID, IG_USER_ID to .env.
Usage: python meta_token.py --page "<Facebook Page name>"   (tokens are never printed)"""
import argparse, json, urllib.parse, urllib.request
from pathlib import Path

from viral import load_env

ENVF = Path(__file__).parent / ".env"
G = "https://graph.facebook.com/v25.0"
NEED = {"instagram_basic", "instagram_content_publish", "pages_show_list", "pages_read_engagement", "pages_manage_posts"}


def get(path, **q):
    return json.loads(urllib.request.urlopen(f"{G}/{path}?" + urllib.parse.urlencode(q), timeout=30).read())


def set_env(k, v):
    lines = ENVF.read_text(encoding="utf-8").splitlines() if ENVF.exists() else []
    lines = [l for l in lines if not l.startswith(k + "=")] + [f"{k}={v}"]
    ENVF.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--page", required=True); a = ap.parse_args()
    e = load_env()
    long = get("oauth/access_token", grant_type="fb_exchange_token", client_id=e["META_APP_ID"], client_secret=e["META_APP_SECRET"],
               fb_exchange_token=e["META_SHORT_TOKEN"])["access_token"]
    pages = get("me/accounts", access_token=long, fields="name,id,access_token,instagram_business_account")["data"]
    page = next((p for p in pages if p["name"].lower() == a.page.lower()), None)
    if not page:
        raise SystemExit("page not found; available: " + ", ".join(p["name"] for p in pages))
    dbg = get("debug_token", input_token=page["access_token"], access_token=f"{e['META_APP_ID']}|{e['META_APP_SECRET']}")["data"]
    missing = NEED - set(dbg.get("scopes", []))
    if missing:
        print("WARNING missing permissions:", ", ".join(sorted(missing)))
    ig = (page.get("instagram_business_account") or {}).get("id")
    if not ig:
        raise SystemExit("no Instagram account linked to this Page")
    set_env("META_PAGE_TOKEN", page["access_token"]); set_env("FB_PAGE_ID", page["id"]); set_env("IG_USER_ID", ig)
    print("ok: page", page["name"], "| IG linked | expires:", dbg.get("expires_at") or "never")


if __name__ == "__main__":
    main()
