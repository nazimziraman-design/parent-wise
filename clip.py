"""Viral clip -> Reel frame (1080x1920): brand row + hook on top, video in the middle, "Source: @creator" at the bottom.
Steps: python clip.py fetch <url> | python clip.py frame content/clips/<file>.json"""
import json, os, re, subprocess, sys, html
from datetime import date
from pathlib import Path

import brand

ROOT = Path(__file__).parent
NOWIN = 0x08000000 if os.name == "nt" else 0
HEADER = f"{brand.BRAND}  {brand.HANDLE}"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, creationflags=NOWIN)


def fetch(url):
    posted = ROOT / "publish_log.jsonl"
    if posted.exists() and url in posted.read_text(encoding="utf-8"):
        sys.exit("already posted: " + url)
    cid = re.sub(r"\W+", "-", url.split("//")[-1])[-24:].strip("-").lower()
    out = ROOT / "output" / f"clip-{cid}"
    out.mkdir(parents=True, exist_ok=True)
    r = run([sys.executable, "-m", "yt_dlp", "--no-playlist", "-f", "mp4/bestvideo+bestaudio/best", "--merge-output-format", "mp4",
             "--write-info-json", "-o", str(out / "source.%(ext)s"), url])
    if r.returncode:
        sys.exit("yt-dlp failed: " + r.stderr[-400:])
    info = json.loads((out / "source.info.json").read_text(encoding="utf-8"))
    dur = float(info.get("duration") or 0)
    for k in range(8):
        run(["ffmpeg", "-y", "-ss", str(dur * (k + 0.5) / 8), "-i", str(out / "source.mp4"), "-frames:v", "1", "-vf", "scale=540:-1",
             str(out / f"frame_{k}.jpg")])
    meta = {"id": cid, "url": url, "uploader": info.get("uploader"), "handle": info.get("uploader_id"),
            "description": (info.get("description") or "")[:500], "duration": dur, "platform": info.get("extractor_key")}
    (out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta))
    return out


def frame(path):
    path = Path(path)
    c = json.loads(path.read_text(encoding="utf-8"))
    cid = c["id"]
    out = ROOT / "output" / f"clip-{cid}"
    fit, pos = c.get("fit", "auto"), float(c.get("crop_pos", 0.5))
    vw, vh = 1080, 1000  # video window
    hook = html.escape(c["hook"])
    credit = html.escape(c.get("credit", ""))
    title = html.escape(c.get("title", ""))
    from playwright.sync_api import sync_playwright
    from themes import base
    ff = base.fontface_css(["Anton", "DM Sans"])
    page = f"""<!doctype html><meta charset=utf-8><style>{ff}*{{margin:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;background:#000;color:#fff;overflow:hidden}}
.b{{position:absolute;top:150px;left:60px;font:700 30px 'DM Sans';opacity:.85}}
.t{{position:absolute;top:210px;left:60px;right:60px;font:400 64px/1.05 'Anton';text-transform:uppercase}}
.h{{position:absolute;top:210px;left:60px;right:60px;font:700 46px/1.2 'DM Sans'}}
.src{{position:absolute;bottom:250px;left:60px;font:600 28px 'DM Sans';color:#bbb}}</style>
<div class="b">{html.escape(HEADER)}</div><div class="h" id="h">{f'<b style="font:400 58px Anton;text-transform:uppercase;display:block;margin-bottom:12px">{title}</b>' if title else ''}{hook}</div>
<div class="src">Source: {credit}</div>
<script>let h=document.getElementById('h'),fs=46;while(h.scrollHeight>330&&fs>26){{fs-=2;h.style.fontSize=fs+'px'}}</script>"""
    hf = out / "frame.html"
    hf.write_text(page, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(hf.resolve().as_uri())
        pg.wait_for_timeout(250)
        pg.screenshot(path=str(out / "frame.png"))
        b.close()
    scale = (f"scale={vw}:{vh}:force_original_aspect_ratio=decrease,pad={vw}:{vh}:(ow-iw)/2:(oh-ih)/2:black" if fit == "contain" else
             f"scale={vw}:-2,crop={vw}:min(ih\\,{vh}):0:(ih-min(ih\\,{vh}))*{pos},pad={vw}:{vh}:0:(oh-ih)/2:black")
    fc = f"[1:v]{scale}[v];[0:v][v]overlay=0:{1920 - vh - 330}:shortest=1[o]"
    r = run(["ffmpeg", "-y", "-loop", "1", "-i", str(out / "frame.png"), "-i", str(out / "source.mp4"), "-t", "90", "-filter_complex", fc,
             "-map", "[o]", "-map", "1:a?", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-r", "30", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", str(out / "reel.mp4")])
    if r.returncode:
        sys.exit("ffmpeg failed: " + r.stderr[-400:])
    run(["ffmpeg", "-y", "-i", str(out / "reel.mp4"), "-frames:v", "1", str(out / "cover.jpg")])
    print("clip reel ->", out / "reel.mp4")


if __name__ == "__main__":
    {"fetch": lambda: fetch(sys.argv[2]), "frame": lambda: frame(sys.argv[2])}[sys.argv[1]]()
