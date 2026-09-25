"""Parent Wise carousel look (black + coral). One renderer, slide types decide the layout:
 A stage guide : stagecover (code-drawn art + big caps headline), point (numbered 'tweet' slide), cta
 B problem text: tcover (caps + SWIPE pill), text (big left-aligned text on dark texture), cta
 C single image: quote (centered sentence / letter)
Text auto-shrinks (--k) until it fits. No fake verified badge, no child photos."""
import random, re

import brand
from themes import base
from themes.base import esc

ACCENT = "#ff6a88"
ANIM_SEL = ".anim"
TYPE_SEL = ""
DRAW_SEL = ""
CC_ACTIVE = "#ff6a88"
REEL_CSS = "html,body,.s{height:1920px}.arrow,.swipepill{display:none}"
CC_CSS = ""
FORMATS = ("stage", "problem", "single")

NOISE = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .5 0'/></filter>"
         "<rect width='100%' height='100%' filter='url(%23n)' opacity='.16'/></svg>\")")


def configure(data):
    global ACCENT, CC_ACTIVE
    a = (data.get("design") or {}).get("palette", {}).get("accent")
    ACCENT = CC_ACTIVE = a if isinstance(a, str) and base.HEX.match(a) else brand.DEFAULT_PALETTE["accent"]


def md(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<i>\1</i>", s)
    return s.replace("\n", "<br>")


def art_svg(seed, accent, accent2):
    """Abstract glowing neural-network 'mind' drawing (no people, no logos)."""
    rnd = random.Random(seed)
    pts = []
    while len(pts) < 30:
        x, y = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
        if x * x + y * y < 1:
            pts.append((450 + x * 330, 235 + y * 190))
    lines = ""
    for i, (x, y) in enumerate(pts):
        near = sorted(range(len(pts)), key=lambda j: (pts[j][0] - x) ** 2 + (pts[j][1] - y) ** 2)[1:3]
        for j in near:
            lines += f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{pts[j][0]:.0f}" y2="{pts[j][1]:.0f}" stroke="{accent}" stroke-opacity=".45" stroke-width="2"/>'
    dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([5, 6, 8, 12]):d}" fill="{rnd.choice([accent, accent2, "#fff"])}" filter="url(#g)"/>' for x, y in pts)
    return (f'<svg viewBox="0 0 900 460" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<filter id="g" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4"/></filter>'
            f'<radialGradient id="r"><stop offset="0" stop-color="{accent}" stop-opacity=".55"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs>'
            f'<ellipse cx="450" cy="235" rx="360" ry="215" fill="url(#r)"/>{lines}{dots}</svg>')


def cover_visual(data):
    uri = data.get("_cover_uri")
    if uri:
        return f'<div class="cv"><div class="ph" style="background-image:url({uri})"></div></div>'
    art = base.clean_svg((data.get("design") or {}).get("art")) or art_svg(data.get("topic", "pw"), ACCENT, "#4ecdc4")
    return f'<div class="cv"><div class="art">{art}</div></div>'


def css(data, tex):
    p = (data.get("design") or {}).get("palette", {})
    a2 = p.get("accent2") if isinstance(p.get("accent2"), str) and base.HEX.match(p.get("accent2", "")) else brand.DEFAULT_PALETTE["accent2"]
    g1, g2 = brand.LOGO_GRADIENT
    ff = base.fontface_css(["Inter", "Anton"])
    bgtex = f"{NOISE}," if tex else ""
    return f"""{ff}
:root{{--a:{ACCENT};--a2:{a2};--k:1}}
*{{box-sizing:border-box;margin:0}}html,body{{width:1080px;height:1350px;background:#000;overflow:hidden}}
.s{{position:relative;width:1080px;height:1350px;color:#fff;font-family:'Inter',sans-serif;display:flex;flex-direction:column;
background:{bgtex}radial-gradient(circle at 88% -6%,{ACCENT}33,transparent 46%),{'#15110f' if tex else '#000'}}}
.pad{{padding:92px 84px 0}}.fitbox{{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;justify-content:center}}
.head{{display:flex;align-items:center;gap:24px;margin-bottom:46px}}
.av{{width:92px;height:92px;border-radius:50%;background:linear-gradient(135deg,{g1},{g2});display:grid;place-items:center;font:800 44px Inter;color:#fff;flex:none}}
.nm{{font:700 38px Inter}}.hd{{font:500 29px Inter;color:#8e95a3}}
.n{{font:700 calc(58px*var(--k))/1.16 Inter;margin-bottom:24px}}.n span{{color:var(--a)}}
.p{{font:400 calc(44px*var(--k))/1.34 Inter;color:#f1f3f8;margin-bottom:22px}}
.say{{border-left:7px solid var(--a);padding:2px 0 2px 28px;margin:16px 0 24px;font:600 calc(44px*var(--k))/1.32 Inter}}
.close{{font:italic 400 calc(42px*var(--k))/1.32 Inter;color:#c4c9d4}}
.foot{{padding:0 84px 70px;display:flex;justify-content:space-between;align-items:center;min-height:120px}}
.handle{{font:600 30px Inter;color:#8e95a3}}.arrow{{width:150px;height:34px}}
.cv .ph{{height:760px;background-size:cover;background-position:50% 20%;-webkit-mask-image:linear-gradient(#000 78%,transparent);mask-image:linear-gradient(#000 78%,transparent)}}
.cv .art{{height:610px;-webkit-mask-image:linear-gradient(#000 62%,transparent);mask-image:linear-gradient(#000 62%,transparent)}}.cv .art svg{{width:100%;height:100%;display:block}}
.hl{{padding:0 76px;font:400 calc(88px*var(--k))/1.02 Anton,Impact,sans-serif;text-transform:uppercase;letter-spacing:.005em}}.hl em,.hl b{{font-style:normal;color:var(--a);font-weight:400}}
.hl .sm{{color:#fff}}
.tc{{font:800 calc(78px*var(--k))/1.16 Inter;text-align:center;text-transform:uppercase}}.tc em{{font-style:normal;color:var(--a)}}
.txt{{font:500 calc(60px*var(--k))/1.36 Inter}}.txt b{{color:#fff;font-weight:800}}
.q{{font:600 calc(64px*var(--k))/1.36 Inter}}.q i{{color:var(--a)}}.by{{font:500 34px Inter;color:#8e95a3;margin-top:34px}}
.top{{text-align:center;font:600 34px Inter;color:#cfd4de;padding:84px 0 0}}
.swipepill{{position:absolute;right:0;bottom:120px;background:var(--a);color:#111;font:800 30px Inter;padding:12px 30px 12px 40px;border-radius:99px 0 0 99px;letter-spacing:.08em}}
.ctal{{display:flex;gap:26px;align-items:baseline;margin-bottom:22px}}.ctal .v{{font:700 calc(48px*var(--k)) 'Inter';color:var(--a);min-width:190px}}.ctal .t{{font:500 calc(46px*var(--k)) Inter}}
.cm{{font:700 calc(56px*var(--k))/1.3 Inter;margin:8px 0 26px}}.cm b{{background:var(--a);color:#111;padding:2px 22px;border-radius:14px;font-weight:800;white-space:nowrap}}
.mini{{font:600 calc(34px*var(--k)) Inter;color:#8e95a3;margin-bottom:8px}}
.disc{{font:400 27px/1.35 Inter;color:#8e95a3;margin-top:26px}}
"""


FIT = """<script>(function(){var b=document.querySelector('.fitbox');if(!b)return;var k=1;while(b.scrollHeight>b.clientHeight+1&&k>.42){k-=.03;document.documentElement.style.setProperty('--k',k)}})()</script>"""
ARROW = '<svg class="arrow" viewBox="0 0 150 34"><path d="M2 17H140M124 5l16 12-16 12" fill="none" stroke="#ff6a88" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def _foot(data, last, arrow=True):
    return (f'<div class="foot"><span class="handle">{esc(data.get("handle", brand.HANDLE))}</span>'
            f'{ARROW.replace("#ff6a88", ACCENT) if arrow and not last else ""}</div>')


def _head(data):
    return (f'<div class="head"><div class="av">{brand.LOGO_LETTER}</div><div><div class="nm">{esc(data.get("brand", brand.BRAND))}</div>'
            f'<div class="hd">{esc(data.get("handle", brand.HANDLE))}</div></div></div>')


def slide(data, s, i, n):
    t, last = s.get("type"), i == n - 1
    tex = False
    if t == "tcover":  # same cover look as the stage guide
        body = (f'{cover_visual(data)}<div class="fitbox"><div class="hl">{md(s.get("text"))}</div></div>')
        return f'<style>{css(data, False)}</style><div class="s">{body}{_foot(data, last)}</div>{FIT}'
    if t == "stagecover":
        art = base.clean_svg((data.get("design") or {}).get("art")) or art_svg(data.get("topic", "pw"), ACCENT, "#4ecdc4")
        head = esc(s.get("headline", ""))
        em = s.get("em")
        if em and esc(em) in head:
            head = head.replace(esc(em), f"<em>{esc(em)}</em>", 1)
        body = f'{cover_visual(data)}<div class="fitbox"><div class="hl">{head}</div></div>'
        return f'<style>{css(data, False)}</style><div class="s">{body}{_foot(data, last)}</div>{FIT}'
    if t == "point":
        rows = f'<div class="n"><span>{esc(s.get("n", ""))}.</span> {md(s.get("title"))}</div>'
        for line in s.get("body", []):
            rows += f'<div class="p">{md(line)}</div>'
        if s.get("say"):
            rows += f'<div class="say">{md(s["say"])}</div>'
        if s.get("close"):
            rows += f'<div class="close">{md(s["close"])}</div>'
        body = f'<div class="pad">{_head(data)}</div><div class="fitbox pad" style="padding-top:0">{rows}</div>'
    elif t == "cta" and s.get("keyword"):
        kw = esc(str(s["keyword"]).upper())
        body = (f'<div class="pad">{_head(data)}</div><div class="fitbox pad" style="padding-top:0">'
                f'<div class="p">{md(s.get("intro"))}</div>' + (f'<div class="p">{md(s.get("offer"))}</div>' if s.get("offer") else "") +
                f'<div class="cm">Comment <b>{kw}</b> and I’ll send you the link.</div>'
                f'<div class="mini">Save · Share · Follow {esc(data.get("handle", brand.HANDLE))}</div>'
                f'<div class="disc">{esc(brand.DISCLAIMER)}</div></div>')
    elif t == "cta":
        lines = "".join(f'<div class="ctal"><span class="v">{esc(v)}</span><span class="t">{md(x)}</span></div>' for v, x in s.get("lines", []))
        body = (f'<div class="pad">{_head(data)}</div><div class="fitbox pad" style="padding-top:0"><div class="n">{md(s.get("title"))}</div>{lines}'
                f'<div class="disc">{esc(brand.DISCLAIMER)}</div></div>')
    elif t == "tcover":
        body = (f'<div class="fitbox pad"><div class="tc">{md(s.get("text"))}</div></div><div class="swipepill">SWIPE</div>')
    elif t == "text":
        body = f'<div class="pad">{_head(data)}</div><div class="fitbox pad" style="padding-top:0"><div class="txt">{md(s.get("text"))}</div></div>'
    elif t == "quote":
        by = f'<div class="by">{esc(s.get("by"))}</div>' if s.get("by") else ""
        body = f'<div class="pad">{_head(data)}</div><div class="fitbox pad" style="padding-top:0"><div class="q">{md(s.get("text"))}</div>{by}</div>'
    else:
        body = f'<div class="fitbox pad"><div class="txt">{md(s.get("text") or s.get("title"))}</div></div>'
    return (f'<style>{css(data, tex)}</style><div class="s">{body}{_foot(data, last, arrow=(t not in ("quote", "tcover")))}</div>{FIT}')


def render(data):
    configure(data)
    slides = data.get("slides", [])
    return ["<!doctype html><meta charset=utf-8>" + slide(data, s, i, len(slides)) for i, s in enumerate(slides)]
