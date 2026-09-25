"""Photo + hook cover slide: full-width image on top, fade to black, brand row, big uppercase Anton headline."""
import brand
from themes import base
from themes.base import esc


def render(data, image_uri, reel=False):
    c = data.get("cover", {})
    head, em = c.get("headline", ""), c.get("em", "")
    body = esc(head)
    if em and em in head:
        body = esc(head).replace(esc(em), f'<span class="em">{esc(em)}</span>', 1)
    pos = esc(c.get("focus", "50% 20%"))
    credit = ""
    if c.get("photo"):
        ph = c["photo"]
        credit = f'<div class="credit">Photo: {esc(ph.get("author", ""))} · {esc(ph.get("license", ""))} via Wikimedia Commons</div>'
    ff = base.fontface_css(["Anton", "DM Sans"])
    H, Y0 = (1920, 190) if reel else (1350, 0)
    a, b = brand.LOGO_GRADIENT
    return f"""<!doctype html><meta charset=utf-8><style>{ff}
*{{box-sizing:border-box;margin:0}}html,body{{width:1080px;height:{H}px;background:#000;overflow:hidden}}
.s{{position:relative;width:1080px;height:{H}px;background:#000;color:#fff}}
.img{{position:absolute;top:{Y0}px;left:60px;width:960px;height:800px;background:url('{image_uri}') {pos}/cover;border-radius:0 0 28px 28px}}
.fade{{position:absolute;top:{Y0+400}px;left:0;right:0;height:420px;background:linear-gradient(transparent,#000)}}
.brand{{position:absolute;top:{Y0+760}px;left:60px;right:60px;display:flex;align-items:center;gap:18px;font:700 30px 'DM Sans'}}
.logo{{width:54px;height:54px;border-radius:50%;background:linear-gradient(135deg,{a},{b});display:grid;place-items:center;font:700 28px 'DM Sans'}}
.h{{position:absolute;top:{Y0+830}px;left:60px;right:60px;font:400 84px/1.02 'Anton';text-transform:uppercase;letter-spacing:.01em}}
.em{{color:#ffd23f}}.swipe{{display:{'none' if reel else 'block'};position:absolute;bottom:50px;left:60px;font:700 28px 'DM Sans';letter-spacing:.2em;color:#ffd23f}}
.credit{{position:absolute;bottom:50px;right:60px;font:500 20px 'DM Sans';color:#aaa}}</style>
<div class="s body"><div class="img"></div><div class="fade"></div>
<div class="brand"><div class="logo">{brand.LOGO_LETTER}</div>{esc(data.get('brand', brand.BRAND))} <span style="opacity:.6">{esc(data.get('handle', brand.HANDLE))}</span></div>
<div class="h" id="h">{body}</div><div class="swipe">SWIPE FOR MORE</div>{credit}</div>
<script>let h=document.getElementById('h'),fs=84;while(h.scrollHeight>400&&fs>40){{fs-=2;h.style.fontSize=fs+'px'}}</script>"""
