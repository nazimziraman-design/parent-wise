"""Shared helpers for themes: fonts, palette validation, contrast, SVG sanitising, escaping."""
import html, json, re
from pathlib import Path

import brand

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
POOL = ["Inter", "Manrope", "DM Sans", "Outfit", "Sora", "Space Grotesk", "Unbounded", "Syne", "Bricolage Grotesque",
        "Archivo", "Anton", "Bebas Neue", "Fraunces", "Playfair Display", "DM Serif Display", "Instrument Serif",
        "JetBrains Mono", "Space Mono", "IBM Plex Mono"]
_MANIFEST = FONT_DIR / "manifest.json"
FILES = json.loads(_MANIFEST.read_text(encoding="utf-8")) if _MANIFEST.exists() else {}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def rich(s):
    """Escape, then render `code` spans."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(s))


def fontface_css(families):
    out = []
    for fam in dict.fromkeys(families):
        f = FILES.get(fam)
        if f:
            out.append(f"@font-face{{font-family:'{fam}';src:url('{(FONT_DIR / f).as_uri()}');font-weight:100 900;}}")
    return "\n".join(out)


def font(name, default):
    return name if name in POOL else default


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def lum(h):
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in _rgb(h)]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def fix_contrast(fg, bg, minimum):
    if contrast(fg, bg) >= minimum:
        return fg
    return "#111111" if lum(bg) > 0.4 else "#ffffff"


def palette(design):
    p = dict(brand.DEFAULT_PALETTE)
    for k, v in (design.get("palette") or {}).items():
        if k in p and isinstance(v, str) and HEX.match(v):
            p[k] = v
    p["ink"] = fix_contrast(p["ink"], p["bg"], 7)
    p["muted"] = fix_contrast(p["muted"], p["bg"], 4.5)
    p["ink_on_surface"] = fix_contrast(p["ink"], p["surface"], 7)
    p["on_accent"] = "#111111" if lum(p["accent"]) > 0.35 else "#ffffff"
    return p


def clean_svg(svg, maxlen=6000):
    if not isinstance(svg, str) or not svg.strip().startswith("<svg"):
        return ""
    svg = svg[:maxlen]
    svg = re.sub(r"<(script|foreignObject|image|iframe)[\s\S]*?(</\1>|/>)", "", svg, flags=re.I)
    svg = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*')", "", svg, flags=re.I)
    svg = re.sub(r"(href|xlink:href)\s*=\s*(\"[^\"]*\"|'[^']*')", "", svg, flags=re.I)
    return svg


def clamp(v, lo, hi, default):
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return default


PATTERNS = {
    "grid": "background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:60px 60px;",
    "dots": "background-image:radial-gradient(var(--line) 2px,transparent 2px);background-size:34px 34px;",
    "lines": "background-image:repeating-linear-gradient(0deg,var(--line) 0 1px,transparent 1px 28px);",
    "diagonal": "background-image:repeating-linear-gradient(45deg,var(--line) 0 2px,transparent 2px 26px);",
    "waves": "background-image:radial-gradient(circle at 50% 120%,transparent 40%,var(--line) 41%,transparent 42%);background-size:120px 60px;",
    "rings": "background-image:radial-gradient(circle,transparent 30%,var(--line) 31%,transparent 32%);background-size:200px 200px;",
    "scanlines": "background-image:repeating-linear-gradient(0deg,var(--line) 0 1px,transparent 1px 4px);",
    "noise": "background-image:radial-gradient(var(--line) 1px,transparent 1px);background-size:7px 7px;",
    "plus": "background-image:linear-gradient(var(--line) 2px,transparent 2px),linear-gradient(90deg,var(--line) 2px,transparent 2px);background-size:80px 80px;background-position:39px 39px;",
}
