# split_numbers_vad_all_assets_ffmpeg.py
# pip install torch torchaudio
# 需要 ffmpeg 在 PATH

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

import torch

ASSETS_DIR = Path("assets")
OUT_DIR = Path("output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class AudioJob:
    path: Path
    start_n: Optional[int]
    end_n: Optional[int]

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def require_ffmpeg() -> None:
    try:
        run(["ffmpeg", "-version"])
    except Exception:
        raise RuntimeError("找不到 ffmpeg。請先安裝 ffmpeg，並確保 ffmpeg 在 PATH 中。")

def ffmpeg_to_wav_16k_mono(src_mp3: Path, dst_wav: Path) -> None:
    run(["ffmpeg", "-y", "-i", str(src_mp3), "-ac", "1", "-ar", "16000", str(dst_wav)])

def ffmpeg_cut_wav_to_mp3(src_wav: Path, start_s: float, end_s: float, dst_mp3: Path) -> None:
    # 用 -ss/-to 切 wav，再輸出 mp3
    run([
        "ffmpeg", "-y",
        "-i", str(src_wav),
        "-ss", f"{start_s:.3f}",
        "-to", f"{end_s:.3f}",
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        str(dst_mp3),
    ])

def parse_range_from_name(stem: str) -> Optional[Tuple[int, int]]:
    s = stem.lower()
    patterns = [
        r"(\d+)\s*[-_~–—]\s*(\d+)",  # 0-19 / 20_39 / 40–59 / 80~99
        r"(\d+)\s*to\s*(\d+)",      # 80to99
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            return (a, b) if a <= b else (b, a)
    return None

def merge_close_segments(segments, sr: int, max_gap_s: float = 0.15):
    if not segments:
        return segments
    max_gap = int(max_gap_s * sr)
    merged = [segments[0].copy()]
    for seg in segments[1:]:
        if seg["start"] - merged[-1]["end"] <= max_gap:
            merged[-1]["end"] = max(merged[-1]["end"], seg["end"])
        else:
            merged.append(seg.copy())
    return merged

def main():
    require_ffmpeg()
    if not ASSETS_DIR.exists():
        raise FileNotFoundError(f"找不到資料夾：{ASSETS_DIR.resolve()}")

    mp3_files = sorted(ASSETS_DIR.glob("*.mp3"))
    if not mp3_files:
        raise FileNotFoundError(f"{ASSETS_DIR.resolve()} 下面沒有 mp3 檔案。")

    jobs: List[AudioJob] = []
    for f in mp3_files:
        r = parse_range_from_name(f.stem)
        jobs.append(AudioJob(f, r[0], r[1]) if r else AudioJob(f, None, None))

    # 有範圍的優先，依 start_n 排序
    jobs.sort(key=lambda j: (j.start_n is None, j.start_n if j.start_n is not None else 10**9, j.path.name))

    # Load Silero VAD
    vad_model, vad_utils = torch.hub.load("snakers4/silero-vad", "silero_vad", force_reload=False)
    (get_speech_timestamps, _, read_audio, _, _) = vad_utils

    known_ends = [j.end_n for j in jobs if j.end_n is not None]
    global_counter = (max(known_ends) + 1) if known_ends else 0

    produced = 0
    for job in jobs:
        mp3_path = job.path
        tmp_wav = OUT_DIR / f"{mp3_path.stem}__tmp16k.wav"
        ffmpeg_to_wav_16k_mono(mp3_path, tmp_wav)

        sr = 16000
        wav = read_audio(str(tmp_wav), sampling_rate=sr)

        segments = get_speech_timestamps(
            wav,
            vad_model,
            sampling_rate=sr,
            threshold=0.5,
            min_speech_duration_ms=200,
            min_silence_duration_ms=150,
            speech_pad_ms=50,
        )
        segments = merge_close_segments(segments, sr=sr, max_gap_s=0.15)

        if job.start_n is not None and job.end_n is not None:
            start_n, end_n = job.start_n, job.end_n
            expected = end_n - start_n + 1
        else:
            expected = len(segments)
            start_n = global_counter

        if expected == 0 or len(segments) == 0:
            print(f"[WARN] {mp3_path.name}: 沒偵測到語音段，跳過。")
            tmp_wav.unlink(missing_ok=True)
            continue

        if len(segments) != expected:
            print(f"[WARN] {mp3_path.name}: 偵測到 {len(segments)} 段，預期 {expected} 段，會輸出可用的最小段數。")

        count = min(len(segments), expected)
        for i in range(count):
            n = start_n + i
            s = segments[i]["start"] / sr
            e = segments[i]["end"] / sr
            ffmpeg_cut_wav_to_mp3(tmp_wav, s, e, OUT_DIR / f"{n}.mp3")
            produced += 1

        if job.start_n is None:
            global_counter = start_n + count

        tmp_wav.unlink(missing_ok=True)

    print(f"Done. Produced {produced} files in {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
