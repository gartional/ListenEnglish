"""
Generate cues.json (start, end, text per segment) from an audio file using faster_whisper.
Usage: python tools/generate_cues_from_audio.py [--dir content/mock17]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate_cues(audio_path: Path, out_path: Path) -> None:
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        raise RuntimeError("Install: pip install faster-whisper") from e

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language="en", vad_filter=True)
    cues = []
    for s in segments:
        text = (s.text or "").strip()
        if not text:
            continue
        cues.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": text})
    out_path.write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", len(cues), "cues to", out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path("content/mock17"), help="Directory with audio.mp3")
    args = parser.parse_args()
    dir_path = args.dir if args.dir.is_absolute() else ROOT / args.dir
    audio_path = dir_path / "audio.mp3"
    if not audio_path.exists():
        print("Not found:", audio_path, file=sys.stderr)
        sys.exit(1)
    out_path = dir_path / "cues.json"
    generate_cues(audio_path, out_path)


if __name__ == "__main__":
    main()
