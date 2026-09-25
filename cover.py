"""Cover image: licensed Wikimedia Commons photo of an adult expert -> local Flux scene -> code-drawn gradient.
Usage: python cover.py content/<file>.json"""
import base64, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

from brand import USER_AGENT

ROOT = Path(__file__).parent
API = "https://commons.wikimedia.org/w/api.php"
OK_LICENSE = re.compile(r"^(cc[- ]by(-sa)?[- ]\d|cc0|public domain|pd)", re.I)
BAD_LICENSE = re.compile(r"-nc|-nd|non-?commercial|no-?deriv", re.I)
PENALTY = re.compile(r"logo|signature|building|poster|screenshot|cover|book|stamp", re.I)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def commons_photo(name, force_file=None):
    q = force_file or f'filetype:bitmap "{name}"'
    url = API + "?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 25,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1400})
    pages = (get_json(url).get("query") or {}).get("pages", {})
    best, best_score = None, -999
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        if not OK_LICENSE.search(lic) or BAD_LICENSE.search(lic):
            continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if min(w, h) < 700:
            continue
        title = p["title"]
        score = 0
        score += 50 if name and name.split()[-1].lower() in title.lower() else 0
        score += 15 if "crop" in title.lower() else 0
        score += 15 if h >= w * 0.9 else 0
        m = re.search(r"(20\d\d)", title)
        score += (int(m.group(1)) - 2000) if m else 0
        score -= 60 if PENALTY.search(title) else 0
        if score > best_score:
            best_score, best = score, (p, ii, meta, lic)
    if not best:
        return None
    p, ii, meta, lic = best
    author = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "Unknown")).strip()
    return {"url": ii.get("thumburl") or ii["url"], "photo": {
        "file": p["title"], "page": ii.get("descriptionurl", ""), "author": author, "license": lic,
        "license_url": meta.get("LicenseUrl", {}).get("value", "")}}


def flux(scene, out):
    payload = json.dumps({"prompt": scene + ", warm soft lighting, no text, no logos, no watermark, no children faces",
                          "steps": 4, "width": 896, "height": 1120, "cfg_scale": 1, "sampler_name": "Euler"}).encode()
    req = urllib.request.Request("http://127.0.0.1:7860/sdapi/v1/txt2img", payload, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        out.write_bytes(base64.b64decode(json.loads(r.read())["images"][0]))


def gradient(out, palette):
    from PIL import Image, ImageDraw
    import brand
    p = {**brand.DEFAULT_PALETTE, **(palette or {})}
    im = Image.new("RGB", (960, 1120), p["bg2"])
    d = ImageDraw.Draw(im)
    for i in range(0, 1120, 4):
        t = i / 1120
        c = tuple(int(a * (1 - t) + b * t) for a, b in zip(bytes.fromhex(p["accent"][1:]), bytes.fromhex(p["accent2"][1:])))
        d.rectangle([0, i, 960, i + 4], fill=c)
    im.save(out, quality=92)


PW_FORMATS = ("stage", "problem", "single")


def _run_imagegen(out, prompt, w, h, seed):
    import subprocess, sys
    r = subprocess.run([sys.executable, str(ROOT / "imagegen.py"), str(out), prompt, "--w", str(w), "--h", str(h), "--seed", str(seed)],
                       capture_output=True, text=True, creationflags=0x08000000 if sys.platform == "win32" else 0)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout)[-400:])


def pw_cover(data, out_dir, out):
    """AI-generated child / scene image (never a real child) + optional glowing brain overlay -> cover_image.jpg (1080x760)."""
    from PIL import Image, ImageChops, ImageDraw
    c = data.setdefault("cover", {})
    scene = c.get("scene")
    if not scene:
        return None
    seed = abs(hash(data.get("topic", "x"))) % 10000
    base = out_dir / "_scene.jpg"
    _run_imagegen(base, scene, 896, 1024, seed)
    canvas = Image.new("RGB", (1080, 760), "#000")
    im = Image.open(base).convert("RGB")
    left_w = 720 if c.get("overlay") == "brain" else 1080
    ratio = max(left_w / im.width, 760 / im.height)
    im = im.resize((int(im.width * ratio), int(im.height * ratio)))
    x0, y0 = 0, max(0, int((im.height - 760) * 0.25))
    im = im.crop((x0, y0, x0 + left_w, y0 + 760))
    mask = Image.new("L", im.size, 255)
    if left_w < 1080:
        d = ImageDraw.Draw(mask)
        for i in range(160):
            d.line([(left_w - 160 + i, 0), (left_w - 160 + i, 760)], fill=int(255 * (1 - i / 160)))
    canvas.paste(im, (0, 0), mask)
    if c.get("overlay") == "brain":
        bb = out_dir / "_brain.jpg"
        _run_imagegen(bb, "a single glowing blue neural brain hologram, only the brain, luminous synapses, centered, pure black background, no head, no face, no person, no text", 896, 896, seed + 1)
        brain = Image.open(bb).convert("RGB").resize((560, 560))
        fade = ImageChops.invert(Image.radial_gradient("L")).resize((560, 560)).point(lambda v: min(255, int(v * 1.6)))
        brain = ImageChops.multiply(brain, Image.merge("RGB", [fade] * 3))  # feather the square edges
        layer = Image.new("RGB", (1080, 760), "#000")
        layer.paste(brain, (520, 70))
        canvas = ImageChops.screen(canvas, layer)
    canvas.save(out, quality=93)
    c["ai_image"] = True
    cap = data.get("caption", "")
    if cap and "AI-generated" not in cap:
        data["caption"] = cap.rstrip() + "\n\nCover image: AI-generated (not a real child)."
    return "ai"


def main(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    out_dir = ROOT / "output" / path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "cover_image.jpg"
    cover = data.setdefault("cover", {})
    how = None
    if data.get("theme") in PW_FORMATS:
        try:
            how = pw_cover(data, out_dir, out)
        except Exception as e:  # noqa: BLE001
            print("image generation failed:", str(e)[:200])
        if not how and out.exists():
            out.unlink()  # theme falls back to the code-drawn cover art
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("cover via", how or "code-drawn art (no image)")
        return out
    if cover.get("person") or cover.get("photo_file"):
        try:
            got = commons_photo(cover.get("person"), cover.get("photo_file"))
            if got:
                req = urllib.request.Request(got["url"], headers={"User-Agent": USER_AGENT})
                out.write_bytes(urllib.request.urlopen(req, timeout=60).read())
                cover["photo"] = got["photo"]
                how = "commons"
        except Exception as e:  # noqa: BLE001
            print("commons failed:", e)
    if not how and cover.get("scene"):
        try:
            flux(cover["scene"], out)
            cover.pop("photo", None)
            how = "flux"
        except Exception as e:  # noqa: BLE001
            print("flux unavailable:", str(e)[:80])
    if not how:
        gradient(out, (data.get("design") or {}).get("palette"))
        cover.pop("photo", None)
        how = "gradient"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"cover via {how} -> {out}")
    return out


if __name__ == "__main__":
    main(sys.argv[1])
