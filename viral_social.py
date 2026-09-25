"""Viral video finder for X / TikTok / Instagram. Code verifies everything: views >= min, short duration, recent, not posted before.
Usage: python viral_social.py scan     (TikTok creator scan + verify URLs from research/<day>_viral_raw.json written by the Claude viral scout)
Output: research/viral_social.json  (list, newest verification first, deduplicated, rolling)"""
import json, re, subprocess, sys
import envfix  # noqa: F401
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "research" / "viral_social.json"
NOWIN = 0x08000000 if sys.platform == "win32" else 0
URL_RE = re.compile(r"^https?://(www\.)?(x\.com|twitter\.com|tiktok\.com|instagram\.com)/", re.I)


def cfg():
    return json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))["viral_social"]


def ytdlp(args, timeout=120):
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "--impersonate", "chrome", "--js-runtimes", "node", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, creationflags=NOWIN)
    return r


def platform(url):
    u = url.lower()
    return "tiktok" if "tiktok.com" in u else "instagram" if "instagram.com" in u else "x"


def posted_urls():
    f = ROOT / "publish_log.jsonl"
    return f.read_text(encoding="utf-8") if f.exists() else ""


def scan_tiktok_creator(handle, min_views):
    r = ytdlp(["--flat-playlist", "-j", "--playlist-end", "30", f"https://www.tiktok.com/@{handle.lstrip('@')}"], timeout=150)
    out = []
    for line in r.stdout.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if (d.get("view_count") or 0) >= min_views and d.get("url"):
            out.append(d["url"])
    return out


def verify(url, c):
    """Full metadata for one URL; returns a record or None if it does not qualify."""
    r = ytdlp(["-j", "--skip-download", "--no-playlist", url], timeout=90)
    if r.returncode or not r.stdout.strip():
        return {"url": url, "error": (r.stderr.strip().splitlines() or ["failed"])[-1][:120]}
    d = json.loads(r.stdout.strip().splitlines()[-1])
    views, dur = d.get("view_count") or 0, d.get("duration") or 0
    up = d.get("upload_date") or ""
    if views < c["min_views"] or (dur and dur > c["max_duration"]):
        return None
    if up:
        age = (datetime.now() - datetime.strptime(up, "%Y%m%d")).days
        if age > c["max_age_days"]:
            return None
    return {"url": url, "platform": platform(url), "creator": (d.get("uploader") if platform(url) == "tiktok" else d.get("uploader_id")) or d.get("uploader") or "", "creator_name": d.get("channel") or d.get("uploader") or "",
            "views": views, "likes": d.get("like_count"), "duration": dur, "posted": up,
            "title": re.sub(r"\s+", " ", (d.get("title") or d.get("description") or "")).strip()[:140]}


def load_out():
    return json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"items": [], "checked": {}, "updated": None, "errors": []}


def scan(extra_urls=None, extra_creators=None):
    c = cfg()
    state = load_out()
    known = {i["url"] for i in state["items"]}
    checked = state.setdefault("checked", {})  # url -> "ok" | "no" | "err" so we never re-verify
    posted = posted_urls()
    creators = list(dict.fromkeys(c["tiktok_creators"] + (extra_creators or [])))
    cand = list(dict.fromkeys(extra_urls or []))
    errors = []
    for h in creators:
        try:
            got = scan_tiktok_creator(h, c["min_views"])
            print(f"@{h}: {len(got)} above {c['min_views']:,}")
            cand += got
        except Exception as e:  # noqa: BLE001
            errors.append(f"@{h}: {str(e)[:80]}")
    fresh = [u for u in dict.fromkeys(cand) if URL_RE.match(u) and u not in known and u not in posted and checked.get(u) is None][: c["max_verify_per_run"]]
    print(len(fresh), "urls to verify")
    for u in fresh:
        try:
            rec = verify(u, c)
        except Exception as e:  # noqa: BLE001
            rec = {"url": u, "error": str(e)[:100]}
        if rec is None:
            checked[u] = "no"
        elif rec.get("error"):
            checked[u] = "err"
            errors.append(f"{platform(u)}: {rec['error']}")
        else:
            checked[u] = "ok"
            state["items"].append(rec)
            print(f"  OK {rec['views']:,} {rec['platform']} @{rec['creator']}")
    cutoff = (datetime.now() - timedelta(days=c["max_age_days"])).strftime("%Y%m%d")
    state["items"] = sorted([i for i in state["items"] if not i.get("posted") or i["posted"] >= cutoff and i["url"] not in posted],
                            key=lambda i: -i["views"])
    state["updated"] = datetime.now().isoformat(timespec="minutes")
    state["errors"] = errors[-10:]
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(state['items'])} verified videos -> {OUT}")
    return state


if __name__ == "__main__":
    day = datetime.now().strftime("%Y-%m-%d")
    raw = ROOT / "research" / f"{day}_viral_raw.json"
    urls, creators = [], []
    if raw.exists():
        d = json.loads(raw.read_text(encoding="utf-8"))
        urls, creators = d.get("urls", []), d.get("tiktok_creators", [])
    scan(urls, creators)
