"""Playbook series theme (copy-paste cards): fixed series layout, colours/fonts from the design block.
Reuses the adaptive renderer for shared slide types; adds a big-number cover and chat-bubble script cards."""
import re

from themes import adaptive, base
from themes.base import esc

ACCENT = adaptive.ACCENT
ANIM_SEL = ".anim"
TYPE_SEL = ".bubble .text"
DRAW_SEL = ".bar"
CC_ACTIVE = adaptive.CC_ACTIVE
REEL_CSS = adaptive.REEL_CSS + ".foot{display:none}" + ".bigno{font-size:520px!important}.bubble .text{font-size:46px!important}"
CC_CSS = ""

def configure(data):
    global ACCENT, CC_ACTIVE
    adaptive.configure(data)
    ACCENT = CC_ACTIVE = adaptive.ACCENT


EXTRA = """
.bigno{font:800 420px/0.9 var(--dispfont,'Bricolage Grotesque');color:var(--accent);letter-spacing:-.04em}
.deck{position:relative;height:300px;margin:20px 0}.deck i{position:absolute;left:50%;top:40px;width:300px;height:220px;background:var(--surface);
border:3px solid var(--ink);border-radius:26px;transform-origin:50% 120%}
.deck i:nth-child(1){transform:translateX(-50%) rotate(-16deg)}.deck i:nth-child(2){transform:translateX(-50%) rotate(-5deg)}
.deck i:nth-child(3){transform:translateX(-50%) rotate(6deg)}.deck i:nth-child(4){transform:translateX(-50%) rotate(17deg);background:var(--accent)}
.bubble{background:var(--surface);color:var(--ink2);border-radius:36px 36px 36px 8px;padding:40px 44px;position:relative;box-shadow:0 18px 40px rgba(0,0,0,.10)}
.bubble .copy{position:absolute;top:-22px;right:34px;background:var(--accent);color:var(--on-accent);font:700 24px 'JetBrains Mono';padding:8px 18px;border-radius:99px;letter-spacing:.1em}
.bubble .text{font:500 38px/1.4 'DM Sans',sans-serif;white-space:pre-wrap}.bubble .ph{color:var(--accent);font-weight:800}
.tipbox{margin-top:30px;font-size:30px;color:var(--muted);line-height:1.35}
"""


def _fit(text, base_px=52, max_chars=200):
    n = len(text or "")
    return max(32, int(base_px * min(1, (max_chars / max(n, 1)) ** 0.5)))


def render(data):
    configure(data)
    slides = data.get("slides", [])
    out = []
    for i, s in enumerate(slides):
        page = adaptive._slide(data, s if s.get("type") not in ("script", "prompt", "cover") else {"type": "_"}, i, len(slides))
        t = s.get("type")
        if t == "cover":
            m = re.match(r"\s*(\d+)", s.get("title", "") + " " + s.get("kicker", ""))
            num = m.group(1) if m else ""
            rest = re.sub(r"^\s*\d+\s*", "", s.get("title", ""))
            bigno = f'<div class="bigno">{esc(num)}</div>' if num else ""
            body = (f'<div class="label">{esc(s.get("kicker"))}</div>{bigno}'
                    f'<div class="title">{esc(rest)} <em>{esc(s.get("em"))}</em></div>'
                    f'<div class="deck"><i></i><i></i><i></i><i></i></div><div class="sub anim">{esc(s.get("sub"))}</div>')
        elif t in ("script", "prompt"):
            txt = s.get("say") or s.get("prompt") or ""
            ph = re.sub(r"\[([A-Z0-9_ ]+)\]", r'<span class="ph">[\1]</span>', esc(txt))
            body = (f'<div class="label">{esc(s.get("label"))}</div><div class="title" style="font-size:72px">{esc(s.get("name"))}</div>'
                    f'<div class="sub" style="margin-bottom:34px">{esc(s.get("sub") or s.get("note"))}</div>'
                    f'<div class="bubble"><div class="copy">SAY IT</div><div class="text" style="font-size:{_fit(txt)}px">{ph}</div></div>'
                    f'<div class="tipbox anim">{esc(s.get("tip") or "")}</div>')
        else:
            out.append(page.replace("</style>", EXTRA + "</style>", 1))
            continue
        foot = adaptive._foot(data, i, len(slides))
        html_ = (f'<!doctype html><meta charset=utf-8><style>{adaptive._css(data)}{EXTRA}</style>'
                 f'<div class="slide"><div class="body"><div class="main">{body}</div>{foot}</div></div>')
        out.append(html_)
    return out
