"""
Fetch a listening practice page (e.g. from QR code URL), download audio, transcribe to 原文.
Usage: python fetch_listening_from_url.py --url "https://..." --out-dir "content/mock17"
"""
import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Add project root for optional local imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def find_audio_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Collect all candidate audio URLs from page."""
    urls = []
    # <audio src="..."> or <audio><source src="...">
    for tag in soup.find_all("audio"):
        src = tag.get("src")
        if src:
            urls.append(urljoin(base_url, src))
        for s in tag.find_all("source"):
            src = s.get("src")
            if src:
                urls.append(urljoin(base_url, src))
    # Links to audio files
    for a in soup.find_all("a", href=True):
        h = a["href"].strip().lower()
        if h.endswith((".mp3", ".m4a", ".wav", ".ogg")) or "audio" in a.get("class", []) or "mp3" in h:
            urls.append(urljoin(base_url, a["href"]))
    # data-src, data-audio, etc.
    for tag in soup.find_all(attrs={"data-src": True}):
        urls.append(urljoin(base_url, tag["data-src"]))
    for tag in soup.find_all(attrs={"data-audio": True}):
        urls.append(urljoin(base_url, tag["data-audio"]))
    # JS-like: full URLs including ?auth_key= etc.
    html = str(soup)
    for m in re.finditer(r'["\']?(https?://[^"\'\s]+\.(?:mp3|m4a|wav)(?:\?[^"\'\s]*)?)["\']?', html, re.I):
        urls.append(m.group(1))
    return list(dict.fromkeys(urls))  # dedup keep order


def download_audio(url: str, out_path: Path, session: requests.Session, referer: str | None = None) -> Path:
    headers = {}
    if referer:
        headers["Referer"] = referer
    # 连接 15 秒超时，读流每 600 秒超时（国内 CDN 可能较慢，避免中途断掉）
    timeout = (15, 600)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    last_err = None
    for attempt in range(3):
        try:
            if attempt > 0:
                print("  重试 {}/3 ...".format(attempt + 1), flush=True)
            r = session.get(url, stream=True, timeout=timeout, headers=headers)
            r.raise_for_status()
            total = 0
            last_mb = -1
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=262144):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
                        mb = total // (1024 * 1024)
                        if mb > last_mb:
                            print(".", end="", flush=True)
                            last_mb = mb
            print(" {} MB".format(last_mb + 1) if last_mb >= 0 else "", flush=True)
            return out_path
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, OSError) as e:
            last_err = e
            if attempt < 2:
                print("  超时/断线，5 秒后重试 ...", flush=True)
                time.sleep(5)
                continue
            raise last_err
    return out_path


def transcribe_audio(audio_path: Path) -> str:
    """Use faster_whisper to get full transcript (原文)."""
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        raise RuntimeError(
            "Install: pip install faster-whisper. Then run again."
        ) from e
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language="en", vad_filter=True)
    lines = [s.text.strip() for s in segments if s.text.strip()]
    return "\n".join(lines)


def _existing_audio_path(out_dir: Path) -> Path | None:
    """若目录里已有 audio.mp3 或 audio.m4a 则返回路径，否则 None。"""
    for name in ("audio.mp3", "audio.m4a"):
        p = out_dir / name
        if p.exists():
            return p
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch listening page, download audio, transcribe.")
    parser.add_argument("--url", required=True, help="Page URL (e.g. from QR code)")
    parser.add_argument("--out-dir", type=Path, default=Path("content/mock17"), help="Output directory")
    parser.add_argument("--download-only", action="store_true", help="只下载音频，不转写")
    args = parser.parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = _existing_audio_path(out_dir)
    if args.download_only and existing:
        print("已有音频，跳过:", existing, flush=True)
        return

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })

    if not existing:
        print("Fetching page:", args.url)
        r = session.get(args.url, timeout=15)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        audio_urls = find_audio_urls(soup, args.url)
        if not audio_urls:
            print("No audio URL found on page. Saving HTML for inspection.", file=sys.stderr)
            (out_dir / "page.html").write_text(r.text, encoding="utf-8")
            sys.exit(1)

        chosen = None
        for u in audio_urls:
            if re.search(r"\.(mp3|m4a)(\?|$)", u, re.I):
                chosen = u
                break
        if not chosen:
            chosen = audio_urls[0]

        ext = "mp3" if "mp3" in chosen.lower() else "m4a" if "m4a" in chosen.lower() else "audio"
        if not ext.endswith(("3", "a")):
            ext = "mp3"
        audio_path = out_dir / f"audio.{ext}"
        print("Downloading (超时10分钟，失败自动重试3次):", chosen[:60] + "..." if len(chosen) > 60 else chosen, flush=True)
        download_audio(chosen, audio_path, session, referer=args.url)
        print("Saved:", audio_path, flush=True)
    else:
        audio_path = existing
        print("已有音频，跳过下载:", audio_path, flush=True)

    if args.download_only:
        return

    print("Transcribing (faster-whisper，约 1～2 分钟)...", flush=True)
    transcript = transcribe_audio(audio_path)
    print("Transcribe 完成.", flush=True)
    transcript_path = out_dir / "transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")
    print("Transcript saved:", transcript_path)
    print("--- 原文 ---")
    print(transcript)


if __name__ == "__main__":
    main()
