"""Default theme: news + evergreen. Everything comes from the content JSON `design` block."""
import brand
from themes import base
from themes.base import esc, rich

ACCENT = "#ff6a88"
ANIM_SEL = ".anim"
TYPE_SEL = ".say .text"
DRAW_SEL = ".bar"
CC_ACTIVE = "#ff6a88"
REEL_CSS = """
html,body{height:1920px}.slide{height:1920px;padding:260px 90px 420px}
.title{font-size:calc(var(--ts)*1.25)}.swipe,.foot{display:none}.item .d,.step .d,.say .text{font-size:44px}
.item .t,.step .t,.k{font-size:46px}.stat .val{font-size:360px}
"""
CC_CSS = ""


def configure(data):
    global ACCENT, CC_ACTIVE
    ACCENT = CC_ACTIVE = base.palette(data.get("design") or {})["accent"]


def _css(data):
    d = data.get("design") or {}
    p = base.palette(d)
    f = d.get("fonts") or {}
    disp = base.font(f.get("display"), "Bricolage Grotesque")
    body = base.font(f.get("body"), "DM Sans")
    mono = base.font(f.get("mono"), "JetBrains Mono")
    dd = d.get("display") or {}
    sh = d.get("shape") or {}
    bg = d.get("background") or {}
    radius = int(base.clamp(sh.get("radius"), 0, 48, 28))
    border = int(base.clamp(sh.get("border"), 0, 4, 0))
    shadow = {"none": "none", "hard": f"8px 8px 0 {p['ink']}", "glow": f"0 0 40px {p['accent']}88"}.get(
        sh.get("shadow"), "0 18px 40px rgba(0,0,0,.10)")
    pat = base.PATTERNS.get(bg.get("pattern"), "")
    pat_op = base.clamp(bg.get("pattern_opacity"), 0, 0.3, 0.08)
    ts = 96 * base.clamp(dd.get("scale"), 0.8, 1.4, 1.0)
    upper = "uppercase" if dd.get("case") == "upper" else "none"
    ff = base.fontface_css([disp, body, mono])
    glow = f"radial-gradient(circle at 85% 8%,{p['accent']}55,transparent 45%)," if bg.get("glow") else ""
    return f"""{ff}
:root{{--bg:{p['bg']};--bg2:{p['bg2']};--surface:{p['surface']};--ink:{p['ink']};--ink2:{p['ink_on_surface']};
--muted:{p['muted']};--accent:{p['accent']};--accent2:{p['accent2']};--on-accent:{p['on_accent']};--line:{p['ink']}{int(pat_op*255):02x};--ts:{ts}px}}
*{{box-sizing:border-box;margin:0}}html,body{{width:1080px;height:1350px;background:var(--bg);overflow:hidden}}
.slide{{position:relative;width:1080px;height:1350px;padding:110px 80px 120px;color:var(--ink);font-family:'{body}',sans-serif;
background:{glow}linear-gradient(160deg,var(--bg),var(--bg2));overflow:hidden}}
.slide:before{{content:'';position:absolute;inset:0;{pat}pointer-events:none}}
.body{{position:relative;height:100%;display:flex;flex-direction:column}}.main{{flex:1;display:flex;flex-direction:column;justify-content:center}}
.label{{font:600 28px '{mono}',monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-bottom:28px;display:flex;gap:14px;align-items:center}}
.label svg{{width:34px;height:34px;fill:var(--accent)}}
.title{{font:{int(base.clamp(dd.get('weight'),100,900,800))} var(--ts)/1.02 '{disp}',sans-serif;text-transform:{upper};letter-spacing:{esc(dd.get('tracking') or '-0.02em')};margin-bottom:44px}}
.title em{{color:var(--accent);{'font-style:italic;' if dd.get('italic_em') else 'font-style:normal;'}}}
.sub{{font-size:36px;line-height:1.35;color:var(--muted)}}
.card{{background:var(--surface);color:var(--ink2);border-radius:{radius}px;{f'border:{border}px solid var(--ink);' if border else ''}box-shadow:{shadow};padding:34px 40px}}
.item,.step{{display:flex;gap:26px;align-items:flex-start;margin-bottom:22px}}
.item .t,.step .t{{font-weight:700;font-size:36px;line-height:1.15}}.item .d,.step .d{{font-size:30px;line-height:1.3;color:var(--muted);margin-top:6px}}
.num{{flex:none;width:64px;height:64px;border-radius:50%;background:var(--accent);color:var(--on-accent);font:700 32px '{mono}';display:grid;place-items:center}}
.k{{font:700 32px '{mono}',monospace;color:var(--accent)}}.row{{display:flex;justify-content:space-between;gap:30px;padding:22px 0;border-bottom:2px solid var(--line);font-size:34px}}
code{{font-family:'{mono}',monospace;background:var(--bg2);padding:2px 10px;border-radius:8px}}
.cols{{display:flex;gap:26px}}.cols .card{{flex:1}}.cols h3{{font:700 38px '{disp}';margin-bottom:18px;color:var(--accent)}}.cols li{{font-size:30px;line-height:1.3;margin:0 0 14px 24px}}
.stat .val{{font:800 300px/1 '{disp}';color:var(--accent);margin:40px 0}}
.say .text{{font:500 36px/1.4 '{mono}',monospace;white-space:pre-wrap}}.say .ph{{color:var(--accent);font-weight:700}}
.bar{{height:8px;background:var(--accent);width:220px;border-radius:8px;margin:0 0 34px}}
.art{{width:100%;margin:10px 0 36px;border-radius:{radius}px;overflow:hidden}}.art svg{{width:100%;height:auto;display:block}}
.foot{{margin-top:auto;display:flex;justify-content:space-between;font:600 26px '{mono}';color:var(--muted)}}
.swipe{{color:var(--accent)}}.disc{{font-size:24px;color:var(--muted);margin-top:26px;line-height:1.3}}
"""


def _ph(text):
    import re
    return re.sub(r"\[([A-Z0-9_ ]+)\]", r'<span class="ph">[\1]</span>', esc(text))


def _foot(data, i, n):
    return f'<div class="foot"><span>{esc(data.get("handle", brand.HANDLE))}</span><span class="swipe">{"SWIPE →" if i < n - 1 else ""}</span></div>'


def _label(d, s):
    icon = d.get("icon") or ""
    return f'<div class="label">{base.clean_svg(icon)}{esc(s.get("label", ""))}</div>' if s.get("label") else ""


def _slide(data, s, i, n):
    d = data.get("design") or {}
    t = s.get("type")
    art = base.clean_svg(d.get("art"))
    b = ""
    if t == "cover":
        b = (f'{_label(d, {"label": s.get("kicker")})}<div class="title">{esc(s.get("title"))} <em>{esc(s.get("em"))}</em></div>'
             f'{f"<div class=art>{art}</div>" if art else ""}<div class="sub anim">{esc(s.get("sub"))}</div>')
    elif t == "facts":
        rows = "".join(f'<div class="row anim"><span class="k">{esc(k)}</span><span>{rich(v)}</span></div>' for k, v in s.get("items", []))
        b = f'{_label(d, s)}<div class="title">{esc(s.get("title"))}</div><div class="card">{rows}</div>'
    elif t == "steps":
        rows = "".join(f'<div class="step anim"><div class="num">{j+1}</div><div><div class="t">{rich(a)}</div><div class="d">{rich(c)}</div></div></div>'
                       for j, (a, c) in enumerate(s.get("steps", [])))
        b = f'{_label(d, s)}<div class="title">{esc(s.get("title"))}</div><div class="card">{rows}</div>'
    elif t == "list":
        rows = "".join(f'<div class="item anim"><div class="num">•</div><div><div class="t">{rich(a)}</div><div class="d">{rich(c)}</div></div></div>'
                       for a, c in s.get("items", []))
        b = f'{_label(d, s)}<div class="title">{esc(s.get("title"))}</div><div class="card">{rows}</div>'
    elif t == "compare":
        cols = "".join(f'<div class="card anim"><h3>{esc(c.get("name"))}</h3><ul>{"".join(f"<li>{rich(p)}</li>" for p in c.get("points", []))}</ul></div>'
                       for c in s.get("cols", []))
        b = f'{_label(d, s)}<div class="title">{esc(s.get("title"))}</div><div class="cols">{cols}</div>'
    elif t == "stat":
        b = (f'{_label(d, s)}<div class="stat"><div class="val anim">{esc(s.get("value"))}</div>'
             f'<div class="title">{esc(s.get("title"))}</div><div class="sub anim">{esc(s.get("sub"))}</div></div>')
    elif t in ("script", "prompt"):
        b = (f'{_label(d, s)}<div class="title">{esc(s.get("name"))}</div><div class="bar"></div>'
             f'<div class="card say"><div class="text">{_ph(s.get("say") or s.get("prompt"))}</div></div>'
             f'<div class="sub anim" style="margin-top:30px">{esc(s.get("note"))}</div>')
    elif t == "limits":
        rows = "".join(f'<div class="item anim"><div class="num">!</div><div class="t">{rich(x)}</div></div>' for x in s.get("items", []))
        b = f'{_label(d, s)}<div class="title">{esc(s.get("title"))}</div><div class="card">{rows}</div><div class="sub anim" style="margin-top:28px">{esc(s.get("cta"))}</div>'
    elif t == "cta":
        rows = "".join(f'<div class="item anim"><div class="k">{esc(v)}</div><div class="t">{rich(x)}</div></div>' for v, x in s.get("lines", []))
        b = (f'<div class="title">{esc(s.get("title"))} <em>{esc(s.get("title2"))}</em></div><div class="card">{rows}</div>'
             f'<div class="disc">{esc(brand.DISCLAIMER)}</div>')
    return (f'<!doctype html><meta charset=utf-8><style>{_css(data)}</style><div class="slide"><div class="body"><div class="main">{b}</div>{_foot(data, i, n)}</div></div>')


def render(data):
    configure(data)
    slides = data.get("slides", [])
    return [_slide(data, s, i, len(slides)) for i, s in enumerate(slides)]
