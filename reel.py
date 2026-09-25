"""Voiced 1080x1920 video (YouTube Short).  Usage: python reel.py content/<file>.json [--voice am_liam] [--speed 1.1] [--no-voice] [--music f.wav]
Frame-by-frame Playwright screenshots -> ffmpeg (H.264 CRF18 + AAC, -14 LUFS)."""
import argparse, json, os, subprocess, sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import carousel

ROOT = Path(__file__).parent
FPS = 30
VOICES = ["af_sarah", "af_jessica", "am_liam", "am_fenrir", "am_puck", "am_eric", "am_adam"]
NOWIN = 0x08000000 if os.name == "nt" else 0


def pick_voice(data, path):
    if data.get("voice") in VOICES:
        return data["voice"]
    used = []
    for f in sorted((ROOT / "content").glob("*.json")):  # oldest first
        try:
            v = json.loads(f.read_text(encoding="utf-8")).get("voice")
        except Exception:  # noqa: BLE001
            continue
        if v in VOICES:
            used.append(v)
    voice = min(VOICES, key=lambda v: (max([i for i, u in enumerate(used) if u == v], default=-1)))
    data["voice"] = voice
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return voice


def run_tts(out_dir, voice, speed, texts):
    py = os.environ.get("KOKORO_PYTHON") or sys.executable
    env = {**os.environ, "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE", "0"), "PYTHONIOENCODING": "utf-8"}
    if os.environ.get("KOKORO_HF_HOME"):
        env["HF_HOME"] = os.environ["KOKORO_HF_HOME"]
        env["HF_HUB_OFFLINE"] = "1"
    r = subprocess.run([py, str(ROOT / "voice.py"), str(out_dir), voice, str(speed), *texts], env=env,
                       capture_output=True, text=True, creationflags=NOWIN)
    if r.returncode:
        raise RuntimeError("TTS failed: " + (r.stderr or "")[-600:])
    return json.loads((out_dir / "voice.json").read_text(encoding="utf-8"))


def slide_duration(s, vo, i):
    if vo and vo["dur"]:
        return max(3.0, 0.15 + vo["dur"] + 0.25)
    if i == 0:
        return 3.6
    txt = s.get("say") or s.get("prompt") or ""
    return max(4.8, min(9.0, 3.0 + len(txt) / 60)) if txt else 5.0


def phrases(words, maxw=4, maxc=22):
    out, cur = [], []
    for w in words:
        cur.append(w)
        line = " ".join(x[0] for x in cur)
        if len(cur) >= maxw or len(line) >= maxc or w[0][-1:] in ".,!?;:":
            out.append(cur)
            cur = []
    if cur:
        if out and len(cur) == 1 and len(out[-1]) < maxw:
            out[-1] += cur
        else:
            out.append(cur)
    return out


JS = """
window.__cfg=%s;
const A=[...document.querySelectorAll(__cfg.anim)],D=[...document.querySelectorAll(__cfg.draw||'#none')],
      T=__cfg.type?document.querySelector(__cfg.type):null,B=document.querySelector('.body');
let TN=[];if(T){const w=document.createTreeWalker(T,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode())TN.push([n,n.textContent]);}
if(T){T.parentElement.style.minHeight=T.parentElement.offsetHeight+'px';}
const TOTAL=TN.reduce((a,x)=>a+x[1].length,0);
window.setT=function(t,dur){
 const first=__cfg.first;
 A.forEach((e,i)=>{const p=first?1:Math.min(1,Math.max(0,(t-0.15-i*0.16)/0.4));e.style.opacity=p;e.style.transform=`translateY(${(1-p)*36}px)`});
 D.forEach(e=>{const p=first?1:Math.min(1,Math.max(0,(t-0.2)/0.6));e.style.transformOrigin='left';e.style.transform=`scaleX(${p})`});
 if(T&&!first){const n=Math.min(TOTAL,Math.floor(Math.max(0,t-0.4)*__cfg.cps));let k=n;TN.forEach(([node,txt])=>{node.textContent=txt.slice(0,Math.max(0,k));k-=txt.length});}
 const out=Math.min(1,Math.max(0,(t-(dur-0.3))/0.3));B.style.opacity=1-out;B.style.transform=`translateY(${-out*30}px)`;
 document.getElementById('pg').style.width=(__cfg.p0+(__cfg.p1-__cfg.p0)*t/dur)*100+'%%';
 const c=window.__cc.find(x=>t>=x.s&&t<x.e);const box=document.getElementById('cc');
 box.innerHTML=c?c.w.map((w,i)=>`<span style="${t>=w[1]&&t<w[2]?'color:'+__cfg.act:''}">${w[0]}</span>`).join(' '):'';box.style.opacity=c?1:0;};
"""


def build_page(html, theme, cfg, cc):
    css = (f"{theme.REEL_CSS}{getattr(theme, 'CC_CSS', '')}"
           "#pgw{position:fixed;left:0;right:0;top:120px;height:10px;background:rgba(255,255,255,.25);z-index:9}"
           f"#pg{{height:100%;width:0;background:{theme.ACCENT}}}"
           "#cc{position:fixed;left:70px;right:70px;bottom:400px;text-align:center;font:800 62px/1.15 'DM Sans',sans-serif;color:#fff;"
           "text-shadow:0 4px 18px rgba(0,0,0,.85);z-index:9;min-height:140px}")
    extra = (f"<style>{css}</style><div id='pgw'><div id='pg'></div></div><div id='cc'></div>"
             f"<script>window.__cc={json.dumps(cc)};{JS % json.dumps(cfg)}</script>")
    return html.replace("</style>", "</style>", 1) + extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("--voice"); ap.add_argument("--speed", type=float)
    ap.add_argument("--no-voice", action="store_true"); ap.add_argument("--music")
    a = ap.parse_args()
    path = Path(a.json)
    data = json.loads(path.read_text(encoding="utf-8"))
    out_dir = ROOT / "output" / path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    theme = carousel.load_theme(data)
    if hasattr(theme, "configure"):
        theme.configure(data)
    pages = carousel.render_pages(data, out_dir, reel=True)
    slides = data.get("slides", [])
    voices = [{"words": [], "dur": 0}] * len(slides)
    if not a.no_voice and any(s.get("voiceover") for s in slides):
        voice = a.voice or pick_voice(data, path)
        speed = a.speed or float(data.get("voice_speed", 1.1))
        voices = run_tts(out_dir, voice, speed, [s.get("voiceover", "") for s in slides])
    durs = [slide_duration(s, v, i) for i, (s, v) in enumerate(zip(slides, voices))]
    total = sum(durs)
    frames = out_dir / "frames"
    frames.mkdir(exist_ok=True)
    for f in frames.glob("*.jpg"):
        f.unlink()
    n = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        t_acc = 0.0
        for i, (html, d) in enumerate(zip(pages, durs)):
            words = voices[i]["words"]
            off = 0.15
            cc = [{"s": off + ph[0][1], "e": off + ph[-1][2] + 0.05, "w": [[w[0], off + w[1], off + w[2]] for w in ph]} for ph in phrases(words)]
            cfg = {"anim": theme.ANIM_SEL, "draw": theme.DRAW_SEL, "type": theme.TYPE_SEL, "first": i == 0,
                   "cps": min(180, max(75, 75)), "p0": t_acc / total, "p1": (t_acc + d) / total, "act": getattr(theme, "CC_ACTIVE", "#ffd23f")}
            hf = out_dir / f"reel_{i:02d}.html"
            hf.write_text(build_page(html, theme, cfg, cc), encoding="utf-8")
            pg.goto(hf.resolve().as_uri())
            pg.wait_for_timeout(250)
            for k in range(int(d * FPS)):
                pg.evaluate(f"setT({k / FPS},{d})")
                pg.screenshot(path=str(frames / f"{n:05d}.jpg"), type="jpeg", quality=90)
                n += 1
            t_acc += d
        b.close()
    # audio
    music = a.music or str(out_dir / "music.wav")
    if not a.music:
        subprocess.run([sys.executable, str(ROOT / "music.py"), str(total), music], check=True)
    inputs = ["-framerate", str(FPS), "-i", str(frames / "%05d.jpg"), "-i", music]
    if any(v["dur"] for v in voices):
        cat = out_dir / "vo_all.wav"
        lst = out_dir / "vo_list.txt"
        segs = []
        for i, (v, d) in enumerate(zip(voices, durs)):
            seg = out_dir / f"seg_{i:02d}.wav"
            src = out_dir / f"vo_{i:02d}.wav"
            if v["dur"]:
                subprocess.run(["ffmpeg", "-y", "-i", str(src), "-af", f"adelay=150:all=1,apad=whole_dur={d}", "-ar", "48000", "-ac", "1", str(seg)],
                               check=True, capture_output=True)
            else:
                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(d), str(seg)], check=True, capture_output=True)
            segs.append(seg)
        lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(cat)], check=True, capture_output=True)
        inputs += ["-i", str(cat)]
        fc = ("[1:a]volume=0.45[m];[2:a]asplit=2[v1][v2];[m][v2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[md];"
              "[md][v1]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        fc = "[1:a]volume=0.6,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    out = out_dir / "reel.mp4"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", str(total), str(out)],
                   check=True, capture_output=True)
    print(f"video {total:.1f}s -> {out}")


if __name__ == "__main__":
    main()
