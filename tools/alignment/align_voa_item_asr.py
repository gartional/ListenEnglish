import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


def vtt_ts(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h = ms // 3_600_000
    ms -= h * 3_600_000
    m = ms // 60_000
    ms -= m * 60_000
    s = ms // 1000
    ms -= s * 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def normalize_text(s: str) -> str:
    s = s.lstrip("\ufeff")
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    s = unicodedata.normalize("NFKC", s)
    return s


def strip_non_content(transcript: str) -> str:
    transcript = normalize_text(transcript)
    lines = [ln.rstrip() for ln in transcript.splitlines()]
    stop_markers = [
        "______________________________________________",
        "Words in This Story",
    ]
    out: list[str] = []
    for ln in lines:
        if any(ln.strip() == m for m in stop_markers):
            break
        out.append(ln)
    return "\n".join(out).strip() + "\n"


WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")


def norm_word(w: str) -> str:
    w = normalize_text(w).lower()
    w = re.sub(r"[^a-z0-9]+", "", w)
    return w


def split_sentences(text: str) -> list[str]:
    text = normalize_text(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


@dataclass(frozen=True)
class WordTS:
    start: float
    end: float
    word: str


def transcribe_words(audio_path: Path, model: str, compute_type: str) -> list[WordTS]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency: faster-whisper. Run: python -m pip install faster-whisper") from e

    wm = WhisperModel(model, device="cpu", compute_type=compute_type)
    segments, _info = wm.transcribe(
        str(audio_path),
        language="en",
        word_timestamps=True,
        vad_filter=True,
    )

    words: list[WordTS] = []
    for seg in segments:
        if not getattr(seg, "words", None):
            continue
        for w in seg.words:
            if w.start is None or w.end is None:
                continue
            t = normalize_text(w.word).strip()
            if not t:
                continue
            words.append(WordTS(float(w.start), float(w.end), t))
    return words


def build_word_mapping(transcript_words: list[str], asr_words: list[str]) -> dict[int, int]:
    import difflib

    sm = difflib.SequenceMatcher(a=transcript_words, b=asr_words, autojunk=False)
    mapping: dict[int, int] = {}
    for a0, b0, size in sm.get_matching_blocks():
        for i in range(size):
            mapping[a0 + i] = b0 + i
    return mapping


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--itemDir", required=True)
    ap.add_argument("--model", default="base.en", help="faster-whisper model (e.g. tiny.en/base.en/small.en)")
    ap.add_argument("--computeType", default="int8", help="ctranslate2 compute type (int8/float32)")
    ap.add_argument("--outVtt", default="captions.vtt")
    ap.add_argument("--outJson", default="cues.json")
    ap.add_argument("--cacheAsr", action="store_true", help="Write asr_words.json for debugging/reuse")
    args = ap.parse_args()

    item_dir = Path(args.itemDir).resolve()
    audio_mp3 = item_dir / "audio.mp3"
    transcript_txt = item_dir / "transcript.txt"
    if not audio_mp3.exists():
        raise FileNotFoundError(audio_mp3)
    if not transcript_txt.exists():
        raise FileNotFoundError(transcript_txt)

    transcript_raw = transcript_txt.read_text(encoding="utf-8", errors="ignore")
    transcript = strip_non_content(transcript_raw)
    paragraphs = [p.strip() for p in transcript.split("\n\n") if p.strip()]
    combined = " ".join(paragraphs)
    sentences = split_sentences(combined)
    if not sentences:
        raise RuntimeError("No sentences found in transcript")

    sentence_word_spans: list[tuple[int, int]] = []
    transcript_words: list[str] = []
    kept_sentences: list[str] = []
    for sent in sentences:
        words = [norm_word(w) for w in WORD_RE.findall(sent)]
        words = [w for w in words if w]
        if not words:
            continue
        start = len(transcript_words)
        transcript_words.extend(words)
        end = len(transcript_words) - 1
        sentence_word_spans.append((start, end))
        kept_sentences.append(sent)

    if not transcript_words:
        raise RuntimeError("No transcript words extracted")

    words_ts = transcribe_words(audio_mp3, args.model, args.computeType)
    if not words_ts:
        raise RuntimeError("ASR produced no word timestamps")

    asr_norm = [norm_word(w.word) for w in words_ts]
    mapping = build_word_mapping(transcript_words, asr_norm)

    cues: list[dict] = []
    for (a_start, a_end), sent in zip(sentence_word_spans, kept_sentences):
        mapped = [mapping[i] for i in range(a_start, a_end + 1) if i in mapping]
        if not mapped:
            continue
        b0 = min(mapped)
        b1 = max(mapped)
        start_t = words_ts[b0].start
        end_t = words_ts[b1].end
        if end_t <= start_t:
            continue
        cues.append({"start": start_t, "end": end_t, "text": sent})

    if not cues:
        raise RuntimeError("No cues produced; transcript/ASR mismatch too large")

    out_vtt = item_dir / args.outVtt
    out_json = item_dir / args.outJson

    vtt_lines = ["WEBVTT", ""]
    for idx, c in enumerate(cues, start=1):
        vtt_lines.append(str(idx))
        vtt_lines.append(f"{vtt_ts(c['start'])} --> {vtt_ts(c['end'])}")
        vtt_lines.append(c["text"])
        vtt_lines.append("")
    out_vtt.write_text("\n".join(vtt_lines).strip() + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.cacheAsr:
        (item_dir / "asr_words.json").write_text(
            json.dumps([w.__dict__ for w in words_ts], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise

