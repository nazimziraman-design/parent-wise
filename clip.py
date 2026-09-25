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


def fetch(url, file=None, credit=None):
    """Download the clip with yt-dlp, or take a local video file you saved yourself (file=...). Records views if the platform reports them."""
    import shutil
    posted = ROOT / "publish_log.jsonl"
    if posted.exists() and url in posted.read_text(encoding="utf-8"):
        sys.exit("already posted: " + url)
    cid = re.sub(r"\W+", "-", url.split("//")[-1])[-24:].strip("-").lower()
    out = ROOT / "output" / f"clip-{cid}"
    out.mkdir(parents=True, exist_ok=True)
    info = {}
    if file:
        if not Path(file).exists():
            sys.exit("file not found: " + file)
        shutil.copy2(file, out / "source.mp4")
        info = {"uploader": credit, "uploader_id": credit, "extractor_key": url.split("/")[2] if "//" in url else "local"}
    else:
        r = run([sys.executable, "-m", "yt_dlp", "--no-playlist", "-f", "mp4/bestvideo+bestaudio/best", "--merge-output-format", "mp4",
                 "--write-info-json", "-o", str(out / "source.%(ext)s"), url])
        if r.returncode:
            sys.exit("yt-dlp failed (the platform may need cookies; save the video yourself and pass the file path): " + r.stderr[-300:])
        info = json.loads((out / "source.info.json").read_text(encoding="utf-8"))
    pr = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / "source.mp4")])
    dur = float(info.get("duration") or (pr.stdout.strip() or 0))
    for k in range(8):
        run(["ffmpeg", "-y", "-ss", str(dur * (k + 0.5) / 8), "-i", str(out / "source.mp4"), "-frames:v", "1", "-vf", "scale=540:-1",
             str(out / f"frame_{k}.jpg")])
    meta = {"id": cid, "url": url, "uploader": info.get("uploader"), "handle": info.get("uploader_id"),
            "description": (info.get("description") or "")[:500], "duration": dur, "platform": info.get("extractor_key"),
            "views": info.get("view_count"), "likes": info.get("like_count"), "posted": info.get("upload_date"), "credit_hint": credit}
    (out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    v = meta["views"]
    print("views: %s%s" % (f"{v:,}" if v else "unknown (check it yourself)", "" if v and v >= 100000 else "  [not verified as 100k+]"), file=sys.stderr)
    print(json.dumps(meta))
    return out


def frame(path):
    """Reel frame like the reference: brand row (logo + name + handle), bold hook, video window with a logo watermark and a credit
    in the corner, and "Source: @creator on X" underneath. Renders an opaque frame.png and a transparent overlay.png."""
    path = Path(path)
    c = json.loads(path.read_text(encoding="utf-8"))
    cid = c["id"]
    out = ROOT / "output" / f"clip-{cid}"
    fit, pos = c.get("fit", "auto"), float(c.get("crop_pos", 0.5))
    vw, vh, vy = 1080, 1000, 600  # video window
    hook = html.escape(c["hook"])
    credit = html.escape(c.get("credit", ""))
    title = html.escape(c.get("title", ""))
    from playwright.sync_api import sync_playwright
    from themes import base
    ff = base.fontface_css(["Inter"])
    g1, g2 = brand.LOGO_GRADIENT
    logo = f'<div class="logo">{brand.LOGO_LETTER}</div>'
    page = f"""<!doctype html><meta charset=utf-8><style>{ff}*{{margin:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;background:#000;color:#fff;overflow:hidden;font-family:Inter,sans-serif}}
.logo{{width:64px;height:64px;border-radius:18px;background:linear-gradient(135deg,{g1},{g2});display:grid;place-items:center;font:800 36px Inter;color:#fff;flex:none}}
.b{{position:absolute;top:170px;left:60px;right:60px;display:flex;align-items:center;gap:18px;font:800 40px Inter}}.b span{{font:500 30px Inter;color:#9aa1b0}}
.t{{font:800 62px/1.08 Inter;margin-bottom:14px}}
.h{{position:absolute;top:270px;left:60px;right:60px;height:300px;overflow:hidden}}
.hk{{font:500 54px/1.18 Inter}}
.src{{position:absolute;top:{vy+vh+34}px;left:60px;font:500 30px Inter;color:#9aa1b0}}</style>
<div class="b">{logo}{html.escape(brand.BRAND)} <span>{html.escape(brand.HANDLE)}</span></div>
<div class="h" id="h">{f'<div class="t">{title}</div>' if title else ''}<div class="hk">{hook}</div></div>
<div class="src">Source: {credit}</div>
<script>let h=document.getElementById('h'),k=1;while(h.scrollHeight>h.clientHeight+1&&k>.5){{k-=.04;h.style.fontSize=(k*100)+'%'}}
h.querySelectorAll('.t').forEach(e=>e.style.fontSize=(62*k)+'px');h.querySelectorAll('.hk').forEach(e=>e.style.fontSize=(54*k)+'px')</script>"""
    ov = f"""<!doctype html><meta charset=utf-8><style>{ff}*{{margin:0}}html,body{{width:1080px;height:1920px;background:transparent}}
.wm{{position:absolute;top:{vy+22}px;right:{22}px;display:flex;align-items:center;gap:12px;background:#0009;border-radius:16px;padding:8px 16px 8px 8px;font:700 28px Inter;color:#fff}}
.wm .logo{{width:46px;height:46px;border-radius:13px;background:linear-gradient(135deg,{g1},{g2});display:grid;place-items:center;font:800 26px Inter}}
.cr{{position:absolute;left:22px;bottom:{1920 - (vy + vh) + 22}px;background:#0009;border-radius:12px;padding:8px 16px;font:600 26px Inter;color:#fff}}</style>
<div class="wm"><div class="logo">{brand.LOGO_LETTER}</div>{html.escape(brand.HANDLE)}</div><div class="cr">Credit: {credit}</div>"""
    (out / "frame.html").write_text(page, encoding="utf-8")
    (out / "overlay.html").write_text(ov, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto((out / "frame.html").resolve().as_uri()); pg.wait_for_timeout(250)
        pg.screenshot(path=str(out / "frame.png"))
        pg.goto((out / "overlay.html").resolve().as_uri()); pg.wait_for_timeout(250)
        pg.screenshot(path=str(out / "overlay.png"), omit_background=True)
        b.close()
    scale = (f"scale={vw}:{vh}:force_original_aspect_ratio=decrease,pad={vw}:{vh}:(ow-iw)/2:(oh-ih)/2:black" if fit == "contain" else
             f"scale={vw}:-2,crop={vw}:min(ih\,{vh}):0:(ih-min(ih\,{vh}))*{pos},pad={vw}:{vh}:0:(oh-ih)/2:black")
    fc = f"[1:v]{scale}[v];[0:v][v]overlay=0:{vy}:shortest=1[o];[o][2:v]overlay=0:0[o2]"
    r = run(["ffmpeg", "-y", "-loop", "1", "-i", str(out / "frame.png"), "-i", str(out / "source.mp4"), "-loop", "1", "-i", str(out / "overlay.png"),
             "-t", "90", "-filter_complex", fc, "-map", "[o2]", "-map", "1:a?", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-r", "30", "-c:v", "libx264",
             "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", str(out / "reel.mp4")])
    if r.returncode:
        sys.exit("ffmpeg failed: " + r.stderr[-400:])
    run(["ffmpeg", "-y", "-i", str(out / "reel.mp4"), "-frames:v", "1", str(out / "cover.jpg")])
    print("clip reel ->", out / "reel.mp4")


if __name__ == "__main__":
    a = sys.argv
    if a[1] == "fetch":
        opt = {a[k]: a[k + 1] for k in range(3, len(a) - 1, 2)}
        fetch(a[2], opt.get("--file"), opt.get("--credit"))
    else:
        frame(a[2])
