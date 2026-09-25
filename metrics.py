"""Performance metrics from publish_log.jsonl ids -> runs/metrics.json (local only, 30-day history).
Privacy-policy promise enforced here: YouTube API data older than 30 days is deleted."""
import json, re, time, urllib.parse, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from viral import load_env

ROOT = Path(__file__).parent
ENV = load_env()
G = "https://graph.facebook.com/v25.0"


def jget(url, headers=None):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=30).read())


def ig_metrics(url, needs):
    try:
        mid = re.search(r"/(?:p|reel)/([\w-]+)", url or "")
        media = jget(f"{G}/{ENV['IG_USER_ID']}/media?fields=id,permalink,like_count,comments_count&limit=50&access_token={ENV['META_PAGE_TOKEN']}")["data"]
        m = next((x for x in media if mid and mid.group(1) in x.get("permalink", "")), None)
        if not m:
            return {}
        ins = jget(f"{G}/{m['id']}/insights?metric=reach,saved,shares,views,total_interactions&access_token={ENV['META_PAGE_TOKEN']}")["data"]
        return {"likes": m.get("like_count"), "comments": m.get("comments_count"), **{i["name"]: i["values"][0]["value"] for i in ins}}
    except Exception as e:  # noqa: BLE001
        needs.append(f"instagram: {str(e)[:80]} (instagram_manage_insights?)")
        return {}


def yt_metrics(url, needs):
    try:
        vid = url.rsplit("/", 1)[-1]
        tok = json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", urllib.parse.urlencode({
            "client_id": ENV["YT_CLIENT_ID"], "client_secret": ENV["YT_CLIENT_SECRET"], "refresh_token": ENV["YT_REFRESH_TOKEN"],
            "grant_type": "refresh_token"}).encode())).read())["access_token"]
        it = jget(f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={vid}", {"Authorization": "Bearer " + tok})["items"]
        return it[0]["statistics"] if it else {}
    except Exception as e:  # noqa: BLE001
        needs.append(f"youtube: {str(e)[:80]}")
        return {}


def main():
    f = ROOT / "publish_log.jsonl"
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []
    needs, posts = [], []
    for r in rows[-30:]:
        posts.append({"post": r["post"], "date": r["date"], "topic": r.get("topic"),
                      "instagram": ig_metrics(r.get("ig_url") or r.get("ig_reel_url"), needs) if (r.get("ig_url") or r.get("ig_reel_url")) else {},
                      "youtube": yt_metrics(r["yt_url"], needs) if r.get("yt_url") else {}})
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    posts = [p for p in posts if p["date"] >= cutoff]  # 30-day retention promise
    out = {"updated": datetime.now().isoformat(timespec="minutes"), "posts": posts, "needs": sorted(set(needs))}
    (ROOT / "runs").mkdir(exist_ok=True)
    (ROOT / "runs" / "metrics.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(posts), "posts,", len(out["needs"]), "notes")


if __name__ == "__main__":
    main()
