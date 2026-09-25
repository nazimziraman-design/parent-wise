"""Download the 19 OFL fonts (google/fonts) + license into fonts/. Run once."""
import json, urllib.parse, urllib.request
from pathlib import Path

FONTS = Path(__file__).parent / "fonts"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
# family -> (folder, file)
POOL = {
    "Inter": ("inter", "Inter[opsz,wght].ttf"),
    "Manrope": ("manrope", "Manrope[wght].ttf"),
    "DM Sans": ("dmsans", "DMSans[opsz,wght].ttf"),
    "Outfit": ("outfit", "Outfit[wght].ttf"),
    "Sora": ("sora", "Sora[wght].ttf"),
    "Space Grotesk": ("spacegrotesk", "SpaceGrotesk[wght].ttf"),
    "Unbounded": ("unbounded", "Unbounded[wght].ttf"),
    "Syne": ("syne", "Syne[wght].ttf"),
    "Bricolage Grotesque": ("bricolagegrotesque", "BricolageGrotesque[opsz,wdth,wght].ttf"),
    "Archivo": ("archivo", "Archivo[wdth,wght].ttf"),
    "Anton": ("anton", "Anton-Regular.ttf"),
    "Bebas Neue": ("bebasneue", "BebasNeue-Regular.ttf"),
    "Fraunces": ("fraunces", "Fraunces[SOFT,WONK,opsz,wght].ttf"),
    "Playfair Display": ("playfairdisplay", "PlayfairDisplay[wght].ttf"),
    "DM Serif Display": ("dmserifdisplay", "DMSerifDisplay-Regular.ttf"),
    "Instrument Serif": ("instrumentserif", "InstrumentSerif-Regular.ttf"),
    "JetBrains Mono": ("jetbrainsmono", "JetBrainsMono[wght].ttf"),
    "Space Mono": ("spacemono", "SpaceMono-Regular.ttf"),
    "IBM Plex Mono": ("ibmplexmono", "IBMPlexMono-Regular.ttf"),
}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fonts"}), timeout=60) as r:
        return r.read()


def main():
    FONTS.mkdir(exist_ok=True)
    manifest = {}
    for fam, (folder, fn) in POOL.items():
        local = FONTS / (fn.split("[")[0].replace("-Regular", "").replace(".ttf", "") + ".ttf")
        try:
            if not local.exists():
                local.write_bytes(get(BASE + folder + "/" + urllib.parse.quote(fn)))
            try:
                (FONTS / f"OFL-{folder}.txt").write_bytes(get(BASE + folder + "/OFL.txt"))
            except Exception:  # noqa: BLE001
                pass
            manifest[fam] = local.name
            print("ok ", fam)
        except Exception as e:  # noqa: BLE001
            print("ERR", fam, e)
    (FONTS / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
