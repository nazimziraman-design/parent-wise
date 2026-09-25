"""Layer 1: collect the last N hours from sources.json into research/YYYY-MM-DD.json.
No AI, no API keys, standard library only. Collects; the scout decides."""
import gzip, html, json, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from brand import USER_AGENT

ROOT = Path(__file__).parent
TIER_ORDER = {"official": 0, "signal": 1, "community": 2}
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def fetch(url, retries=1):
    last = None
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                    data = gzip.decompress(data)
                return data.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5)
    raise last


def clean(s, n=400):
    s = re.sub(r"<(script|style).*?</\1>", " ", s or "", flags=re.S | re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", s).strip()[:n]


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except Exception:  # noqa: BLE001
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            return None
    return d.astimezone(timezone.utc) if d.tzinfo else d.replace(tzinfo=timezone.utc)


def strip_ns(root):
    for el in root.iter():
        el.tag = el.tag.split("}")[-1]
    return root


def collect_feed(src, since):
    root = strip_ns(ET.fromstring(fetch(src["url"]).lstrip()))
    out = []
    for it in list(root.iter("item")) + list(root.iter("entry")):
        g = lambda t: (it.findtext(t) or "").strip()  # noqa: E731
        link = g("link")
        if not link:
            le = it.find("link")
            link = le.get("href", "") if le is not None else ""
        title = clean(g("title"), 200)
        d = parse_date(g("pubDate") or g("published") or g("updated") or g("date"))
        if not d or d < since or d > datetime.now(timezone.utc) + timedelta(hours=2):
            continue
        summary = clean(g("description") or g("summary") or g("content"))
        if src.get("skip") and re.search(src["skip"], title):
            continue
        if src.get("match") and not re.search(src["match"], title + " " + summary):
            continue
        out.append({"source": src["name"], "tier": src["tier"], "title": title, "url": link,
                    "date": d.isoformat(), "summary": summary})
    return out


DATE_RES = [
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), lambda m: (int(m[1]), int(m[2]), int(m[3]))),
    (re.compile(r"\b([A-Z][a-z]{2})[a-z]*\.? (\d{1,2}),? (\d{4})\b"),
     lambda m: (int(m[3]), MONTHS.get(m[1].lower(), 0), int(m[2]))),
]


def collect_dated_sections(src, since):
    text = clean(fetch(src["url"]), 200000)
    hits = []
    for rx, conv in DATE_RES:
        for m in rx.finditer(text):
            try:
                y, mo, d = conv(m)
                hits.append((m.start(), datetime(y, mo, d, tzinfo=timezone.utc)))
            except Exception:  # noqa: BLE001
                pass
    hits.sort()
    by_day = {}
    now = datetime.now(timezone.utc)
    for i, (pos, dt) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        if dt < since - timedelta(days=1) or dt > now:
            continue
        by_day.setdefault(dt.date(), []).append(text[pos:end])
    out = []
    for day, parts in by_day.items():
        body = " ".join(parts)
        if src.get("match") and not re.search(src["match"], body):
            continue
        out.append({"source": src["name"], "tier": src["tier"], "title": f"{src['name']} — {day}",
                    "url": src["url"], "date": datetime(day.year, day.month, day.day, tzinfo=timezone.utc).isoformat(),
                    "summary": body[:400]})
    return out


def collect_hn(cfg, since):
    out, seen = [], set()
    for q in cfg["queries"]:
        url = ("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=20&query="
               + urllib.parse.quote(q) + f"&numericFilters=created_at_i>{int(since.timestamp())},points>={cfg['min_points']}")
        for h in json.loads(fetch(url)).get("hits", []):
            if h["objectID"] in seen:
                continue
            seen.add(h["objectID"])
            out.append({"source": "Hacker News", "tier": "community", "title": h.get("title", ""),
                        "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                        "date": h["created_at"], "summary": f"{h.get('points')} points, {h.get('num_comments')} comments"})
    return out


def main(hours=36):
    cfg = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    items, errors = [], []
    jobs = ([(s["name"], collect_feed, s) for s in cfg.get("feeds", [])]
            + [(s["name"], collect_dated_sections, s) for s in cfg.get("pages", [])]
            + ([("Hacker News", lambda c, s: collect_hn(c, s), cfg["hn"])] if cfg.get("hn") else []))
    for name, fn, arg in jobs:
        try:
            got = fn(arg, since)
            items += got
            print(f"  {name}: {len(got)}")
        except Exception as e:  # noqa: BLE001
            errors.append({"source": name, "error": str(e)[:200]})
            print(f"  {name}: ERROR {e}")
    items.sort(key=lambda i: i["date"], reverse=True)
    items.sort(key=lambda i: TIER_ORDER.get(i["tier"], 9))
    out = {"generated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "hours": hours,
           "items": items, "errors": errors, "manual": cfg.get("manual", [])}
    path = ROOT / "research" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(items)} items, {len(errors)} errors -> {path}")
    return path


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 36)
