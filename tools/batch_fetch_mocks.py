"""
批量抓取 48 个听力链接到 content/mock01 .. content/mock48。
Usage:
  阶段一（只下载音频，断点续传）:
    python tools/batch_fetch_mocks.py --download-only
  阶段二（全部下完后，再做字幕/分段/翻译）:
    python tools/batch_fetch_mocks.py --skip-fetch
  其他: [--workers N] [--skip-cues] [--skip-translate] [--start N] [--end N]
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URLS = [
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqTIestY",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqxRawKh",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqL1mv7f",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FquEHoJM",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq2o1NYz",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq05ttST&lid=sa2dayotv6tbmg67&rlid=sa2dayotv6tbmg67",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqqBfcH3&lid=cnw67uqdy8btbmg76&rlid=cnw67uqdy8btbmg76",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqVtN1Rx",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq0EqEG5",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqWbGABy",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqJs2332",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqGIf9e2",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fqmu1uFp",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fql4glAI&lid=iuhyxeh7abtbmgba&rlid=iuhyxeh7abtbmgba",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqEePPQu&lid=9aqgu8611dtbmgbv&rlid=9aqgu8611dtbmgbv",
    "https://h5.clewm.net/?url=h.qr61.cn/obzgrD/qfx5a58",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqSp4L7Y&lid=j97u8hjhcbtbmgcq&rlid=j97u8hjhcbtbmgcq",
    "https://h5.clewm.net/?url=h.qr61.cn/obzgrD/quFB1OG",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq5QSBSZ",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqGOAYNN",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqDcUwIn",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqmmCijf",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqecacR1",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqQXPJVW&lid=trks8x61k1tbmh2q&rlid=trks8x61k1tbmh2q",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq2vkNH9",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq9DVgON&lid=8ek2r1qgn5ftbmh4h&rlid=8ek2r1qgn5ftbmh4h",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq84Bjdd&lid=lm1gkj5pgntbmh4u&rlid=lm1gkj5pgntbmh4u",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq0HZgIq",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqZD02IL",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq2cJS9K",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq9FzJ41",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqNG0MmU",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqqK7FlZ",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqDTnmNu",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fqk4jqwT",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqGn3Lp0",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FquUeRT7&lid=hxvgbq60a3ltbmh8f&rlid=hxvgbq60a3ltbmh8f",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqLzsaZc",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqiAIDBv",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqhLouBn",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2Fq9lHpMp",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqeZjEJK",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqVG64Kn",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqsnHQYm",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqNwZuL2",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqzW9mZZ",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqTXeBy0",
    "https://h5.clewm.net/?url=h.qr61.cn%2FobzgrD%2FqJXXZt0",
]


def _has_audio(out_dir: Path) -> bool:
    return (out_dir / "audio.mp3").exists() or (out_dir / "audio.m4a").exists()


def run_one(args, i, capture_output=False):
    """跑完一条：抓取 -> cues -> 翻译。返回 (num, None) 成功，(num, 'fetch'|'cues'|'translate') 失败。"""
    num = i + 1
    out_dir = ROOT / "content" / f"mock{num:02d}"
    url = URLS[i]
    kw = {"cwd": str(ROOT)}
    if capture_output:
        kw["capture_output"] = True
        kw["text"] = True
        print("\n[worker] mock{:02d} 开始".format(num), flush=True)
    else:
        print("\n========== mock{:02d} ==========".format(num), flush=True)

    if getattr(args, "download_only", False):
        if _has_audio(out_dir):
            print("mock{:02d} 已有音频，跳过".format(num), flush=True)
            return (num, None)
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "fetch_listening_from_url.py"), "--url", url, "--out-dir", str(out_dir), "--download-only"],
            **kw,
        )
        if r.returncode != 0:
            if capture_output:
                print("[worker] mock{:02d} 下载失败".format(num), flush=True)
            return (num, "fetch")
        if capture_output:
            print("[worker] mock{:02d} 下载完成".format(num), flush=True)
        return (num, None)

    if not args.skip_fetch:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "fetch_listening_from_url.py"), "--url", url, "--out-dir", str(out_dir)],
            **kw,
        )
        if r.returncode != 0:
            if capture_output:
                print("[worker] mock{:02d} fetch 失败".format(num), flush=True)
            return (num, "fetch")
    if args.skip_fetch and not _has_audio(out_dir):
        if not capture_output:
            print("mock{:02d} 无音频，跳过".format(num), flush=True)
        return (num, None)
    if not args.skip_cues:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_cues_from_audio.py"), "--dir", str(out_dir)],
            **kw,
        )
        if r.returncode != 0:
            if capture_output:
                print("[worker] mock{:02d} cues 失败".format(num), flush=True)
            return (num, "cues")
    if not args.skip_translate:
        cmd = [sys.executable, str(ROOT / "tools" / "translate_mock17_cues.py"), "--dir", str(out_dir), "--no-api"]
        if args.key:
            cmd = [sys.executable, str(ROOT / "tools" / "translate_mock17_cues.py"), "--dir", str(out_dir), "--key", args.key]
        r = subprocess.run(cmd, **kw)
        if r.returncode != 0:
            if capture_output:
                print("[worker] mock{:02d} translate 失败".format(num), flush=True)
            return (num, "translate")
    if capture_output:
        print("[worker] mock{:02d} 完成".format(num), flush=True)
    return (num, None)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=1, help="同时跑几条（默认 1=一条接一条，2 或 3=多线程）")
    p.add_argument("--download-only", action="store_true", help="只下载音频（已有音频的 mock 会跳过，断点续传）")
    p.add_argument("--skip-fetch", action="store_true", help="跳过抓取，只做 cues + 翻译（用于全部下完后做字幕/分段）")
    p.add_argument("--skip-cues", action="store_true", help="跳过 generate_cues")
    p.add_argument("--skip-translate", action="store_true", help="跳过翻译（--no-api）")
    p.add_argument("--start", type=int, default=1, help="从第几条开始（1-based）")
    p.add_argument("--end", type=int, default=len(URLS), help="到第几条结束（含）")
    p.add_argument("--key", default=None, help="OpenAI API key，用于翻译；不传则用 --no-api")
    args = p.parse_args()
    start = max(1, args.start)
    end = min(len(URLS), args.end)
    workers = max(1, min(args.workers, 4))
    indices = list(range(start - 1, end))
    failed = []
    if workers <= 1:
        for i in indices:
            num, err = run_one(args, i, capture_output=False)
            if err:
                failed.append((err, num))
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(run_one, args, i, True): i for i in indices}
            for fut in as_completed(futures):
                num, err = fut.result()
                if err:
                    failed.append((err, num))
    if failed:
        print("\n失败:", failed)
    else:
        print("\n全部完成。")


if __name__ == "__main__":
    main()
