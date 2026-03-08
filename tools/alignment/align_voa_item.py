import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")


def vtt_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
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
    # Remove common VOA footer/glossary sections that should not be in synced subtitles.
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
    w = re.sub(r"[^a-z0-9]+", "", w)  # remove punctuation incl apostrophes for matching robustness
    return w


def split_sentences(text: str) -> list[str]:
    # Keep it simple and deterministic; good enough for VOA learning scripts.
    text = normalize_text(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    # Split on sentence-ending punctuation, keeping punctuation.
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentences = [p.strip() for p in parts if p.strip()]
    return sentences


@dataclass(frozen=True)
class WordInterval:
    start: float
    end: float
    word: str


def read_textgrid_words(textgrid_path: Path) -> list[WordInterval]:
    # Use praatio if available; fall back to a minimal parser would be too fragile.
    try:
        from praatio import textgrid  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("praatio is required in the alignment environment") from e

    tg = textgrid.openTextgrid(str(textgrid_path), includeEmptyIntervals=False)
    tier_names = {t.lower(): t for t in tg.tierNames}

    # MFA typically outputs tiers named "words" and "phones" (sometimes with speaker prefix).
    word_tier_name = None
    for key in ("words", "word", "aligned_words"):
        if key in tier_names:
            word_tier_name = tier_names[key]
            break
    if word_tier_name is None:
        # Try any tier containing "word"
        for t in tg.tierNames:
            if "word" in t.lower():
                word_tier_name = t
                break
    if word_tier_name is None:
        raise RuntimeError(f"No word tier found in TextGrid: {textgrid_path}")

    tier = tg.getTier(word_tier_name)
    intervals: list[WordInterval] = []
    for start, end, label in tier.entries:
        lab = normalize_text(label).strip()
        if not lab:
            continue
        if lab in {"<eps>", "sil", "sp"}:
            continue
        intervals.append(WordInterval(float(start), float(end), lab))
    return intervals


def build_word_mapping(transcript_words: list[str], aligned_words: list[str]) -> dict[int, int]:
    # Map transcript word index -> aligned word index using difflib matching blocks.
    import difflib

    sm = difflib.SequenceMatcher(a=transcript_words, b=aligned_words, autojunk=False)
    mapping: dict[int, int] = {}
    for a0, b0, size in sm.get_matching_blocks():
        for i in range(size):
            mapping[a0 + i] = b0 + i
    return mapping


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--itemDir", required=True, help="VOA item folder containing audio.mp3 and transcript.txt")
    ap.add_argument("--outVtt", default="captions.vtt", help="Output VTT filename (relative to itemDir)")
    ap.add_argument("--outJson", default="cues.json", help="Output cues json filename (relative to itemDir)")
    ap.add_argument("--acousticModel", default="english_us_arpa", help="MFA acoustic model name")
    ap.add_argument("--dictionary", default="english_us_arpa", help="MFA dictionary name")
    ap.add_argument("--beam", type=int, default=100, help="MFA beam")
    ap.add_argument("--retryBeam", type=int, default=400, help="MFA retry beam")
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
    if not transcript.strip():
        raise RuntimeError("Transcript is empty after cleaning")

    # Build a single combined text; subtitles will be sentence-level.
    paragraphs = [p.strip() for p in transcript.split("\n\n") if p.strip()]
    combined = " ".join(paragraphs)
    sentences = split_sentences(combined)
    if not sentences:
        raise RuntimeError("No sentences found in transcript")

    # Build transcript word stream with sentence boundaries.
    sentence_word_spans: list[tuple[int, int]] = []
    transcript_words: list[str] = []
    sentences_for_alignment: list[str] = []
    for sent in sentences:
        words = [norm_word(w) for w in WORD_RE.findall(sent)]
        words = [w for w in words if w]
        if not words:
            continue
        start_idx = len(transcript_words)
        transcript_words.extend(words)
        end_idx = len(transcript_words) - 1
        sentence_word_spans.append((start_idx, end_idx))
        sentences_for_alignment.append(sent)

    if not transcript_words:
        raise RuntimeError("No transcript words extracted")

    with tempfile.TemporaryDirectory(prefix="listenenglish_mfa_") as td:
        td_path = Path(td)
        corpus_dir = td_path / "corpus"
        out_dir = td_path / "out"
        corpus_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        base = "item"
        wav_path = corpus_dir / f"{base}.wav"
        txt_path = corpus_dir / f"{base}.txt"

        # Convert MP3 -> WAV 16k mono (MFA friendly)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(audio_mp3),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(wav_path),
            ]
        )

        # MFA does better when we provide multiple utterances (one sentence per line),
        # letting it map text sequentially over detected speech segments.
        txt_path.write_text("\n".join(sentences_for_alignment).strip() + "\n", encoding="utf-8")

        # Ensure models exist (cached by MFA)
        run(["mfa", "model", "download", "acoustic", args.acousticModel])
        run(["mfa", "model", "download", "dictionary", args.dictionary])
        run(["mfa", "model", "download", "g2p", args.dictionary])

        # Align
        run(
            [
                "mfa",
                "align",
                str(corpus_dir),
                args.dictionary,
                args.acousticModel,
                str(out_dir),
                "--clean",
                "--beam",
                str(args.beam),
                "--retry_beam",
                str(args.retryBeam),
                "--use_g2p",
                "--g2p_model",
                args.dictionary,
                "--single_speaker",
            ]
        )

        tg_path = out_dir / f"{base}.TextGrid"
        if not tg_path.exists():
            # MFA sometimes nests by speaker; try to find any TextGrid.
            tgs = list(out_dir.rglob("*.TextGrid"))
            if not tgs:
                raise RuntimeError("No TextGrid output found")
            tg_path = tgs[0]

        intervals = read_textgrid_words(tg_path)
        aligned_words = [norm_word(w.word) for w in intervals]
        mapping = build_word_mapping(transcript_words, aligned_words)

        cues: list[dict] = []
        for (a_start, a_end), sent in zip(sentence_word_spans, sentences):
            # Find first/last mapped word index for this sentence span.
            mapped = [mapping[i] for i in range(a_start, a_end + 1) if i in mapping]
            if not mapped:
                continue
            b_start = min(mapped)
            b_end = max(mapped)
            start_t = intervals[b_start].start
            end_t = intervals[b_end].end
            if end_t <= start_t:
                continue
            cues.append(
                {
                    "start": start_t,
                    "end": end_t,
                    "text": sent,
                }
            )

    if not cues:
        raise RuntimeError("No cues produced (alignment mismatch too large)")

    # Write VTT + JSON
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
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise

