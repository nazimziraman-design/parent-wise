"""Make sure tools installed via winget (ffmpeg, gh) are found even when the process was started before they were added to PATH."""
import os, shutil
from pathlib import Path

_EXTRA = [Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links", Path("C:/Program Files/GitHub CLI")]
for _d in _EXTRA:
    if _d.exists() and str(_d) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + str(_d)
MISSING = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
