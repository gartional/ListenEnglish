"""
Generate cues-i18n.json with Chinese translation (.zh) for each cue.
Uses OpenAI API to translate cue.text to Chinese. Requires OPENAI_API_KEY in env
or --key. Skips cues that are already mainly Chinese.
Usage: python tools/translate_mock17_cues.py [--dir content/mock17] [--key sk-...]
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MOCK_DIR = ROOT / "content" / "mock17"


def is_mainly_chinese(text: str) -> bool:
    if not text or not text.strip():
        return False
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    total = sum(1 for c in text if c.isalnum() or "\u4e00" <= c <= "\u9fff")
    return total > 0 and cjk / total >= 0.5


def to_simplified(text: str) -> str:
    """Convert Traditional Chinese to Simplified."""
    try:
        from opencc import OpenCC
        return OpenCC("t2s").convert(text)
    except Exception:
        return text


def translate_batch(texts: list[str], api_key: str) -> list[str]:
    try:
        import requests
    except ImportError:
        raise SystemExit("pip install requests")
    url = "https://api.openai.com/v1/chat/completions"
    prompt = "将以下英文句子翻译成简体中文，只输出简体中文，不要序号或解释。每行一句：\n\n" + "\n".join(texts)
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}]},
        timeout=90,
    )
    r.raise_for_status()
    out = r.json()["choices"][0]["message"]["content"].strip()
    lines = [ln.strip() for ln in re.split(r"[\n]+", out) if ln.strip()]
    if len(lines) == len(texts):
        return lines
    # 行数不一致时按顺序尽量对齐：前 n 条用返回的，不足则逐条补翻
    result: list[str] = []
    for i, raw in enumerate(lines):
        if i < len(texts):
            result.append(raw)
    while len(result) < len(texts):
        # 缺的逐条请求
        idx = len(result)
        single = translate_batch([texts[idx]], api_key)
        result.append(single[0] if single else "")
    return result[: len(texts)]


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=DEFAULT_MOCK_DIR, help="Content dir (e.g. content/mock17 or content/mock30)")
    p.add_argument("--key", default=os.environ.get("OPENAI_API_KEY"), help="OpenAI API key")
    p.add_argument("--no-api", action="store_true", help="Only add zh for Chinese cues (no translation API)")
    args = p.parse_args()
    mock_dir = args.dir if args.dir.is_absolute() else ROOT / args.dir
    cues_path = mock_dir / "cues.json"
    out_path = mock_dir / "cues-i18n.json"
    key = (args.key or "").strip() if not args.no_api else ""
    if not key and not args.no_api:
        print("Set OPENAI_API_KEY or pass --key, or use --no-api to generate without translating English", file=sys.stderr)
        sys.exit(1)
    cues = json.loads(cues_path.read_text(encoding="utf-8"))
    if not isinstance(cues, list):
        print("cues.json must be an array", file=sys.stderr)
        sys.exit(1)
    out = [dict(c) for c in cues]
    need_tr: list[tuple[int, str]] = []
    for i, c in enumerate(out):
        text = (c.get("text") or "").strip()
        if not text:
            c["zh"] = ""
        elif is_mainly_chinese(text):
            c["zh"] = to_simplified(text)
        else:
            if args.no_api:
                c["zh"] = ""
            else:
                need_tr.append((i, text))
    if not args.no_api:
        batch_size = 10
        for start in range(0, len(need_tr), batch_size):
            batch = need_tr[start : start + batch_size]
            tr = translate_batch([t for _, t in batch], key)
            for k, (idx, _) in enumerate(batch):
                out[idx]["zh"] = tr[k] if k < len(tr) else ""
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", out_path, "with", len(out), "cues (with .zh)")


if __name__ == "__main__":
    main()
