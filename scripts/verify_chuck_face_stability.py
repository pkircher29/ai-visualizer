"""Zero-install regression gate for Chuck's face and idle stability."""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1792, 1008


def find_browser() -> Path:
    candidates = [
        os.getenv("CHROME_BIN", ""),
        shutil.which("google-chrome") or "",
        shutil.which("chrome") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
        shutil.which("msedge") or "",
        r"C:/Program Files/Google/Chrome/Application/chrome.exe",
        r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise FileNotFoundError("No Chrome/Chromium/Edge executable found; set CHROME_BIN")


def configured_port() -> int:
    for name in ("ai-visualizer.json", "ai-visualizer.json.example"):
        try:
            payload = json.loads((ROOT / name).read_text(encoding="utf-8"))
            return int(payload.get("port", 8790))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return 8790


def server_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/config", timeout=1) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def start_server_if_needed(port: int) -> subprocess.Popen | None:
    if server_ready(port):
        return None
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "server.py"), "--no-open"],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if server_ready(port):
            return process
        if process.poll() is not None:
            break
        time.sleep(0.1)
    process.terminate()
    raise RuntimeError("ai-visualizer server did not become ready")


def render(browser: Path, url: str, destination: Path, budget_ms: int) -> None:
    subprocess.run(
        [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--virtual-time-budget={budget_ms}",
            f"--screenshot={destination}",
            f"{url}?stability={time.time_ns()}",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def read_png(path: Path) -> tuple[int, int, int, list[bytes]]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("screenshot is not PNG")
    offset, compressed = 8, bytearray()
    width = height = color_type = bit_depth = 0
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if bit_depth != 8 or color_type not in (2, 6):
        raise ValueError(f"unsupported PNG format: depth={bit_depth} color={color_type}")
    channels = 3 if color_type == 2 else 4
    stride = width * channels
    raw = zlib.decompress(bytes(compressed))
    rows, prior, cursor = [], bytearray(stride), 0
    for _ in range(height):
        filter_type = raw[cursor]
        scan = bytearray(raw[cursor + 1 : cursor + 1 + stride])
        cursor += stride + 1
        for index in range(stride):
            left = scan[index - channels] if index >= channels else 0
            up = prior[index]
            upper_left = prior[index - channels] if index >= channels else 0
            if filter_type == 1:
                scan[index] = (scan[index] + left) & 255
            elif filter_type == 2:
                scan[index] = (scan[index] + up) & 255
            elif filter_type == 3:
                scan[index] = (scan[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                scan[index] = (scan[index] + _paeth(left, up, upper_left)) & 255
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")
        rows.append(bytes(scan))
        prior = scan
    return width, height, channels, rows


def workshop_luma(path: Path) -> float:
    width, height, channels, rows = read_png(path)
    x1, y1 = round(width * 80 / WIDTH), round(height * 130 / HEIGHT)
    x2, y2 = round(width * 690 / WIDTH), round(height * 790 / HEIGHT)
    total = count = 0
    for row in rows[y1:y2]:
        for x in range(x1, x2):
            base = x * channels
            red, green, blue = row[base : base + 3]
            total += (77 * red + 150 * green + 29 * blue) >> 8
            count += 1
    return total / count


def verify_source_contract() -> None:
    source = (ROOT / "faces" / "chuck" / "index.html").read_text(encoding="utf-8")
    required = (
        "AV.init({mic:false,sound:false})",
        "document.documentElement.requestFullscreen",
        'aria-live="polite"',
        "const voiceActive=raw==='speaking'",
    )
    missing = [fragment for fragment in required if fragment not in source]
    if missing:
        raise AssertionError(f"missing face contract fragments: {missing}")
    if "Math.max(s,energy" in source:
        raise AssertionError("voice meter still contains synthetic state-based activity")


def main() -> int:
    verify_source_contract()
    browser = find_browser()
    port = configured_port()
    server = start_server_if_needed(port)
    url = f"http://127.0.0.1:{port}/faces/chuck/"
    try:
        with tempfile.TemporaryDirectory(prefix="chuck-face-stability-") as directory:
            root = Path(directory)
            early, late = root / "early.png", root / "late.png"
            render(browser, url, early, 300)
            render(browser, url, late, 8000)
            early_luma, late_luma = workshop_luma(early), workshop_luma(late)
            ratio = late_luma / early_luma if early_luma else 0.0
            result = {
                "browser": str(browser),
                "port": port,
                "early_luma": round(early_luma, 3),
                "late_luma": round(late_luma, 3),
                "retained_ratio": round(ratio, 4),
                "minimum_ratio": 0.9,
                "source_contract": "passed",
            }
            print(json.dumps(result, indent=2))
            return 0 if ratio >= 0.9 else 1
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
