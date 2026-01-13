import random
import re
import shutil
import subprocess
from pathlib import Path

AUDIO_DIR = Path("output")  # 0.mp3 ~ 99.mp3

def ensure_ffplay() -> None:
    if shutil.which("ffplay") is None:
        raise RuntimeError(
            "找不到 ffplay。\n"
            "請確認 FFmpeg 已安裝且 ffplay 在 PATH。\n"
            "測試：ffplay -version"
        )

def play_mp3(path: Path, volume: int = 100) -> None:
    cmd = [
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel", "quiet",
        "-volume", str(int(volume)),
        str(path),
    ]
    subprocess.run(cmd, check=False)

def check_audio_files() -> None:
    missing = [n for n in range(100) if not (AUDIO_DIR / f"{n}.mp3").exists()]
    if missing:
        raise FileNotFoundError(
            f"{AUDIO_DIR} 缺少音檔：{missing[:10]}{'...' if len(missing)>10 else ''}\n"
            "請確認 output/ 內有 0.mp3 ~ 99.mp3"
        )

def normalize_digits(s: str) -> str:
    return "".join(re.findall(r"\d", s))

def main():
    ensure_ffplay()
    check_audio_files()

    total = 0
    correct = 0

    print("=== 0–99 Number Listening Quiz ===")
    print(f"Audio dir: {AUDIO_DIR.resolve()}")
    print("指令：r=重播, a=顯示答案, s=跳過, q=離開")
    print("直接輸入你聽到的數字（0~99）")
    print()

    while True:
        n = random.randint(0, 99)
        total += 1

        print(f"[Q{total}] Listen...")
        play_mp3(AUDIO_DIR / f"{n}.mp3", volume=100)

        while True:
            ans = input("Your answer: ").strip().lower()

            if ans == "q":
                print()
                print(f"Score: {correct}/{total-1} (已完成題數：{total-1})")
                return

            if ans == "r":
                play_mp3(AUDIO_DIR / f"{n}.mp3", volume=100)
                continue

            if ans == "a":
                print("Answer:", n)
                continue

            if ans == "s":
                print("Skipped. Answer:", n)
                print()
                break

            digits = normalize_digits(ans)
            if digits == "":
                print("沒有偵測到數字輸入。可輸入 r 重播。")
                continue

            try:
                guess = int(digits)
            except ValueError:
                print("輸入無法解析成數字，請輸入 0~99。")
                continue

            if 0 <= guess <= 99:
                if guess == n:
                    correct += 1
                    print("✅ Correct!")
                else:
                    print("❌ Wrong.")
                    print("   Your :", guess)
                    print("   Answer:", n)
                print()
                break
            else:
                print("請輸入 0~99。")

if __name__ == "__main__":
    main()
