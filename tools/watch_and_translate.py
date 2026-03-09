"""
定时检查 mock01..mock48 是否都抓取完成；全部完成后自动执行翻译步骤。
Usage: python tools/watch_and_translate.py [--interval 300] [--key sk-...]
  不传 --key 则翻译用 --no-api（仅中文转简体，英文不翻）。
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
NEED = 48  # mock01..mock48


def all_mocks_done():
    """检查是否 mock01..mock48 都有 cues.json 且存在音频。"""
    for n in range(1, NEED + 1):
        d = CONTENT / f"mock{n:02d}"
        if not (d / "cues.json").exists():
            return False
        if not (d / "audio.mp3").exists() and not (d / "audio.m4a").exists():
            return False
    return True


def run_translate(api_key=None):
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "batch_fetch_mocks.py"),
        "--skip-fetch",
        "--skip-cues",
    ]
    if api_key:
        cmd += ["--key", api_key]
    return subprocess.run(cmd, cwd=str(ROOT))


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=int, default=120, help="检查间隔秒数，默认 120（2 分钟）")
    p.add_argument("--key", default=None, help="OpenAI API key，翻译英文用；不传则用 --no-api")
    args = p.parse_args()
    interval = max(60, args.interval)
    api_key = (args.key or "").strip() or None
    print("每 {} 秒检查一次，共 {} 条。全部抓完后将自动执行翻译。".format(interval, NEED))
    while True:
        if all_mocks_done():
            print("已全部抓取完成，开始执行翻译...")
            r = run_translate(api_key)
            sys.exit(r.returncode)
        done = sum(1 for n in range(1, NEED + 1) if (CONTENT / f"mock{n:02d}" / "cues.json").exists())
        print("{} 检查: 已完成 {}/{} 条，{} 秒后再查。".format(
            time.strftime("%H:%M:%S"), done, NEED, interval))
        time.sleep(interval)


if __name__ == "__main__":
    main()
