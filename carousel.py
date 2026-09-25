"""Render content JSON -> output/<post>/slide_NN.png + contact.png.  Usage: python carousel.py content/<file>.json"""
import importlib, json, sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent


def load_theme(data):
    name = data.get("theme", "adaptive")
    try:
        return importlib.import_module(f"themes.{name}")
    except ModuleNotFoundError:
        return importlib.import_module("themes.adaptive")


def render_pages(data, out_dir, reel=False):
    theme = load_theme(data)
    if hasattr(theme, "configure"):
        theme.configure(data)
    pages = theme.render(data)
    img = out_dir / "cover_image.jpg"
    if data.get("cover", {}).get("headline") and img.exists():
        from themes import hookcover
        pages[0] = hookcover.render(data, img.resolve().as_uri(), reel)
    return pages


def main(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    out_dir = ROOT / "output" / path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = render_pages(data, out_dir)
    files = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, html in enumerate(pages, 1):
            hf = out_dir / f"slide_{i:02d}.html"
            hf.write_text(html, encoding="utf-8")
            pg.goto(hf.resolve().as_uri())
            pg.wait_for_timeout(250)
            png = out_dir / f"slide_{i:02d}.png"
            pg.screenshot(path=str(png))
            files.append(png)
        b.close()
    from PIL import Image
    thumbs = [Image.open(f).resize((270, 337)) for f in files]
    cols = min(5, len(thumbs))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 280, rows * 347), "#222")
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % cols) * 280 + 5, (i // cols) * 347 + 5))
    sheet.save(out_dir / "contact.png")
    print(f"{len(files)} slides -> {out_dir}")


if __name__ == "__main__":
    main(sys.argv[1])
