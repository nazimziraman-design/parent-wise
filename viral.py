"""Viral signal: trending YouTube videos for the niche (YouTube Data API, uses the OAuth refresh token in .env).
Writes research/<day>_viral.json. Signal only: nothing is downloaded."""
import json, os, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent


def load_env():
    env = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return {**env, **os.environ}


def token(env):
    data = urllib.parse.urlencode({"client_id": env["YT_CLIENT_ID"], "client_secret": env["YT_CLIENT_SECRET"],
                                   "refresh_token": env["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data), timeout=30).read())["access_token"]


def api(path, params, tok):
    req = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/{path}?" + urllib.parse.urlencode(params),
                                 headers={"Authorization": f"Bearer {tok}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def main():
    env = load_env()
    cfg = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))["viral"]
    tok = token(env)
    after = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = {}
    for q in cfg["youtube_queries"]:
        ids = [i["id"]["videoId"] for i in api("search", {"part": "id", "q": q, "type": "video", "order": "viewCount",
                                                           "publishedAfter": after, "maxResults": 10}, tok).get("items", [])]
        if not ids:
            continue
        for v in api("videos", {"part": "snippet,statistics", "id": ",".join(ids)}, tok).get("items", []):
            views = int(v["statistics"].get("viewCount", 0))
            if views >= cfg["youtube_min_views"]:
                found[v["id"]] = {"title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"], "views": views,
                                  "url": f"https://www.youtube.com/watch?v={v['id']}", "published": v["snippet"]["publishedAt"]}
    out = ROOT / "research" / f"{datetime.now():%Y-%m-%d}_viral.json"
    out.write_text(json.dumps(sorted(found.values(), key=lambda x: -x["views"]), indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(found), "viral signals ->", out)


if __name__ == "__main__":
    main()
