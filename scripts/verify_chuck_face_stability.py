"""Regression gate: Chuck's workshop must not blacken over idle time."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageStat

CHROME = Path(r"C:/Program Files/Google/Chrome/Application/chrome.exe")
URL = "http://127.0.0.1:8790/faces/chuck/"


def render(destination: Path, budget_ms: int) -> None:
    subprocess.run(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1792,1008",
            f"--virtual-time-budget={budget_ms}",
            f"--screenshot={destination}",
            f"{URL}?stability={time.time_ns()}",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def workshop_luma(path: Path) -> float:
    with Image.open(path).convert("L") as image:
        # Background/body area below the particle canvas, away from the live
        # face screen and right-side status panel.
        region = image.crop((80, 130, 690, 790))
        return float(ImageStat.Stat(region).mean[0])


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="chuck-face-stability-") as directory:
        root = Path(directory)
        early = root / "early.png"
        late = root / "late.png"
        render(early, 300)
        render(late, 8000)
        early_luma = workshop_luma(early)
        late_luma = workshop_luma(late)
        ratio = late_luma / early_luma if early_luma else 0.0
        result = {
            "early_luma": round(early_luma, 3),
            "late_luma": round(late_luma, 3),
            "retained_ratio": round(ratio, 4),
            "minimum_ratio": 0.9,
        }
        print(json.dumps(result, indent=2))
        return 0 if ratio >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
