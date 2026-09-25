"""Official-API publishing: Meta Graph API v25.0 (Instagram + Facebook Page) and YouTube Data API v3.
Usage: python publish.py content/<file>.json --steps prepare,upload,ig_carousel,fb_photos,yt_short,log   |   --dry-run
Idempotent: every intermediate id is written to output/<post>/publish.json immediately; retries resume, never double-post.
Clips: python publish.py content/clips/<file>.json --steps prepare,upload,ig_reel,fb_reel,log"""
import argparse, json, mimetypes, os, sys, time, subprocess, shutil, urllib.error, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

from viral import load_env

ROOT = Path(__file__).parent
GRAPH = "https://graph.facebook.com/v25.0"
ENV = load_env()
PAGES_URL = ENV.get("PAGES_URL", "").rstrip("/")
NOWIN = 0x08000000 if os.name == "nt" else 0


class ApiError(Exception):
    pass


def http(method, url, data=None, headers=None, timeout=120):
    """Never logs URL or tokens; raises ApiError with Meta/Google message + code only."""
    body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
    req = urllib.request.Request(url, body, headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw and raw[:1] in b"{[" else {"_raw": raw.decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error", {})
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise ApiError(f"HTTP {e.code}: {msg} (code {err.get('code')}/{err.get('error_subcode')})" if isinstance(err, dict) else f"HTTP {e.code}: {msg}") from None
        except (ValueError, AttributeError):
            raise ApiError(f"HTTP {e.code}") from None


def graph(method, path, **params):
    params.setdefault("access_token", ENV["META_PAGE_TOKEN"])
    if method == "GET":
        return http("GET", f"{GRAPH}/{path}?" + urllib.parse.urlencode(params))
    return http("POST", f"{GRAPH}/{path}", params)


class Post:
    def __init__(self, path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.out = ROOT / "output" / self.path.stem
        self.state_f = self.out / "publish.json"
        self.state = json.loads(self.state_f.read_text(encoding="utf-8")) if self.state_f.exists() else {}
        self.is_clip = "hook" in self.data

    def save(self, **kw):
        self.state.update(kw)
        self.state_f.write_text(json.dumps(self.state, indent=1), encoding="utf-8")

    @property
    def caption(self):
        return self.data["caption"]

    def url(self, name):
        return f"{PAGES_URL}/media/{self.path.stem}/{name}"


def step_prepare(p):
    from PIL import Image
    if p.is_clip:
        assert (p.out / "reel.mp4").exists(), "run clip.py frame first"
        p.save(prepared=True, media=["reel.mp4", "cover.jpg"])
        return
    slides = sorted(p.out.glob("slide_*.png"))
    assert 0 < len(slides) <= 10, f"need 1-10 slides, found {len(slides)}"
    names = []
    for s in slides:
        j = s.with_suffix(".jpg")
        Image.open(s).convert("RGB").save(j, quality=92)
        names.append(j.name)
    base = Image.open(slides[0]).convert("RGB")
    from PIL import ImageFilter
    bg = base.resize((1080, 1920)).filter(ImageFilter.GaussianBlur(40))
    h = int(1080 * base.height / base.width)
    bg.paste(base, (0, (1920 - h) // 2))
    bg.save(p.out / "cover.jpg", quality=92)
    media = names + (["reel.mp4", "cover.jpg"] if (p.out / "reel.mp4").exists() else [])
    assert p.caption, "empty caption"
    p.save(prepared=True, media=media)


def git(*a, cwd):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, creationflags=NOWIN)
    if r.returncode:
        raise ApiError("git " + a[0] + " failed: " + r.stderr[-300:])
    return r.stdout


def step_upload(p):
    wt = ROOT / ".pages"
    if not wt.exists():
        git("worktree", "add", str(wt), "gh-pages", cwd=ROOT)
    dest = wt / "media" / p.path.stem
    dest.mkdir(parents=True, exist_ok=True)
    for name in p.state["media"]:
        shutil.copy2(p.out / name, dest / name)
    git("add", "-A", cwd=wt)
    if git("status", "--porcelain", cwd=wt).strip():
        git("commit", "-m", f"media {p.path.stem}", cwd=wt)
        git("push", "origin", "gh-pages", cwd=wt)
    deadline = time.time() + 600
    for name in p.state["media"]:
        size = (p.out / name).stat().st_size
        while True:
            try:
                req = urllib.request.Request(p.url(name), method="HEAD")
                with urllib.request.urlopen(req, timeout=30) as r:
                    if r.status == 200 and int(r.headers.get("Content-Length", -1)) == size:
                        break
            except Exception:  # noqa: BLE001
                pass
            if time.time() > deadline:
                raise ApiError(f"Pages did not serve {name} in time")
            time.sleep(15)
    p.save(uploaded=True)


def wait_container(cid, tries=60):
    for _ in range(tries):
        s = graph("GET", cid, fields="status_code,status")
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise ApiError(f"container {s.get('status_code')}: {s.get('status')}")
        time.sleep(10)
    raise ApiError("container timeout")


def permalink(media_id):
    return graph("GET", media_id, fields="permalink").get("permalink")


def step_ig_carousel(p):
    ig = ENV["IG_USER_ID"]
    if p.state.get("ig_media_id"):
        return
    kids = p.state.setdefault("ig_children", [])
    names = [n for n in p.state["media"] if n.startswith("slide_")]
    for n in names[len(kids):]:
        kids.append(graph("POST", f"{ig}/media", image_url=p.url(n), is_carousel_item="true")["id"])
        p.save()
    for k in kids:
        wait_container(k)
    if not p.state.get("ig_container"):
        p.save(ig_container=graph("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(kids), caption=p.caption)["id"])
    wait_container(p.state["ig_container"])
    mid = graph("POST", f"{ig}/media_publish", creation_id=p.state["ig_container"])["id"]
    p.save(ig_media_id=mid)  # written immediately: a later failure never re-publishes
    p.save(ig_url=permalink(mid))


def step_ig_reel(p):
    ig = ENV["IG_USER_ID"]
    if p.state.get("ig_reel_id"):
        return
    if not p.state.get("ig_reel_container"):
        p.save(ig_reel_container=graph("POST", f"{ig}/media", media_type="REELS", video_url=p.url("reel.mp4"),
                                       cover_url=p.url("cover.jpg"), caption=p.caption, share_to_feed="true")["id"])
    wait_container(p.state["ig_reel_container"])
    mid = graph("POST", f"{ig}/media_publish", creation_id=p.state["ig_reel_container"])["id"]
    p.save(ig_reel_id=mid)
    p.save(ig_reel_url=permalink(mid))


def step_fb_photos(p):
    page = ENV["FB_PAGE_ID"]
    if p.state.get("fb_post_id"):
        return
    ids = p.state.setdefault("fb_photo_ids", [])
    names = [n for n in p.state["media"] if n.startswith("slide_")]
    for n in names[len(ids):]:
        ids.append(graph("POST", f"{page}/photos", url=p.url(n), published="false")["id"])
        p.save()
    params = {f"attached_media[{i}]": json.dumps({"media_fbid": i_}) for i, i_ in enumerate(ids)}
    pid = graph("POST", f"{page}/feed", message=p.caption, **params)["id"]
    p.save(fb_post_id=pid, fb_url=f"https://www.facebook.com/{pid}")


def step_fb_reel(p):
    page = ENV["FB_PAGE_ID"]
    if p.state.get("fb_reel_id") and p.state.get("fb_reel_done"):
        return
    if not p.state.get("fb_reel_id"):
        vid = graph("POST", f"{page}/video_reels", upload_phase="start")["video_id"]
        p.save(fb_reel_id=vid)
        http("POST", f"https://rupload.facebook.com/video-upload/v25.0/{vid}", b"",
             {"Authorization": "OAuth " + ENV["META_PAGE_TOKEN"], "file_url": p.url("reel.mp4")})
    graph("POST", f"{page}/video_reels", upload_phase="finish", video_id=p.state["fb_reel_id"], video_state="PUBLISHED",
          description=p.caption)
    for _ in range(60):
        st = graph("GET", p.state["fb_reel_id"], fields="status").get("status", {})
        if st.get("publishing_phase", {}).get("status") == "complete":
            break
        time.sleep(10)
    p.save(fb_reel_done=True, fb_reel_url=f"https://www.facebook.com/reel/{p.state['fb_reel_id']}")


def yt_token():
    data = {"client_id": ENV["YT_CLIENT_ID"], "client_secret": ENV["YT_CLIENT_SECRET"], "refresh_token": ENV["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}
    return http("POST", "https://oauth2.googleapis.com/token", data)["access_token"]


def step_yt_short(p):
    if p.state.get("yt_id"):
        return
    d = p.data
    tok = yt_token()
    title = (d.get("cover", {}).get("headline", d.get("topic", "")).rstrip(":")[:80] + " #Shorts")[:100]
    desc = d["caption"] + "\n\nSources:\n" + "\n".join(d.get("sources", [])[:3]) + "\n\n#Shorts"
    tags = [w.strip("#") for w in d["caption"].split() if w.startswith("#")][:15]
    meta = json.dumps({"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "26"},
                       "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}).encode()
    size = (p.out / "reel.mp4").stat().st_size
    req = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", meta,
                                 {"Authorization": f"Bearer {tok}", "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4",
                                  "X-Upload-Content-Length": str(size)}, method="POST")
    try:
        loc = urllib.request.urlopen(req, timeout=60).headers["Location"]
    except urllib.error.HTTPError as e:
        raise ApiError(f"YouTube init HTTP {e.code}") from None
    vid = http("PUT", loc, (p.out / "reel.mp4").read_bytes(), {"Content-Type": "video/mp4"}, timeout=600)["id"]
    p.save(yt_id=vid, yt_url=f"https://youtube.com/shorts/{vid}")
    try:
        http("POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", (p.out / "cover.jpg").read_bytes(),
             {"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"})
    except ApiError:
        pass  # thumbnail permission missing: not fatal


def step_log(p):
    row = {"date": datetime.now().isoformat(timespec="seconds"), "post": p.path.stem, "topic": p.data.get("topic") or p.data.get("hook"),
           "theme": p.data.get("theme"), "sources": p.data.get("sources", []),
           **{k: p.state[k] for k in ("ig_url", "ig_reel_url", "fb_url", "fb_reel_url", "yt_url") if k in p.state}}
    with open(ROOT / "publish_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    p.save(logged=True)


def dry_run(p):
    print("post:", p.path.stem, "| steps done:", [k for k in p.state if k.endswith(("_id", "_url", "uploaded", "prepared"))])
    try:
        print("IG:", graph("GET", ENV["IG_USER_ID"], fields="username").get("username"))
        print("IG quota:", graph("GET", f"{ENV['IG_USER_ID']}/content_publishing_limit", fields="quota_usage,config").get("data"))
        print("FB page:", graph("GET", ENV["FB_PAGE_ID"], fields="name").get("name"))
    except (KeyError, ApiError) as e:
        print("Meta check failed:", e)
    try:
        r = http("GET", "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", headers={"Authorization": f"Bearer {yt_token()}"})
        print("YouTube:", r["items"][0]["snippet"]["title"])
    except (KeyError, ApiError, IndexError) as e:
        print("YouTube check failed:", e)


STEPS = {"prepare": step_prepare, "upload": step_upload, "ig_carousel": step_ig_carousel, "ig_reel": step_ig_reel,
         "fb_photos": step_fb_photos, "fb_reel": step_fb_reel, "yt_short": step_yt_short, "log": step_log}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("--steps", default="prepare,upload,ig_carousel,fb_photos,yt_short,log")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    p = Post(a.json)
    if a.dry_run:
        return dry_run(p)
    for s in a.steps.split(","):
        print("->", s)
        try:
            STEPS[s](p)
        except ApiError as e:
            sys.exit(f"{s} failed: {e}")
    print("done")


if __name__ == "__main__":
    main()
