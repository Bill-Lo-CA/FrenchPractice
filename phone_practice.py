import re
import random
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Tuple

AUDIO_DIR = Path("output")  # 你的 0.mp3 ~ 99.mp3 在這裡

# ---------- Playback (ffplay) ----------
def ensure_ffplay() -> None:
    if shutil.which("ffplay") is None:
        raise RuntimeError(
            "找不到 ffplay。\n"
            "請確認你有安裝 FFmpeg，且 ffplay 在 PATH 裡。\n"
            "測試：ffplay -version"
        )

def play_mp3(path: Path, volume: int = 100) -> None:
    """
    用 ffplay 播放 mp3（阻塞式，播完才回來）
    volume: 0~100
    """
    cmd = [
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel", "quiet",
        "-volume", str(int(volume)),
        str(path),
    ]
    subprocess.run(cmd, check=False)

# ---------- Utilities ----------
def normalize_digits(s: str) -> str:
    """把使用者輸入裡所有非數字字元拿掉，只保留 0-9。"""
    return "".join(re.findall(r"\d", s))

def check_audio_files() -> None:
    missing = []
    for n in range(100):
        if not (AUDIO_DIR / f"{n}.mp3").exists():
            missing.append(n)
    if missing:
        raise FileNotFoundError(
            f"{AUDIO_DIR} 缺少音檔：{missing[:10]}{'...' if len(missing)>10 else ''}\n"
            "請確認 output/ 內有 0.mp3 ~ 99.mp3"
        )

# ---------- French phone number generation ----------
def gen_fr_phone() -> str:
    """
    產生法國常見 10 碼手機號：0[6/7]xxxxxxxx
    例：0612345678
    """
    first = "0"
    second = random.choice(["6", "7"])
    rest = "".join(str(random.randint(0, 9)) for _ in range(8))
    return first + second + rest

def split_into_pairs(phone: str) -> List[str]:
    """把 10 碼拆成 5 組兩位數字字串：['06','12','34','56','78']"""
    return [phone[i:i+2] for i in range(0, len(phone), 2)]

def play_pair_group(g: str, pause_s: float, volume: int) -> None:
    """
    播放兩位數 group（'00'~'99'）
    - 如果有前導 0（例如 '06'），會播 0.mp3 再播 6.mp3（比較接近 'zéro six'）
    - 否則直接播 10~99（例如 '34' 就播 34.mp3）
    """
    assert len(g) == 2 and g.isdigit()
    if g[0] == "0":
        play_mp3(AUDIO_DIR / "0.mp3", volume=volume)
        time.sleep(pause_s)
        play_mp3(AUDIO_DIR / f"{int(g[1])}.mp3", volume=volume)
    else:
        play_mp3(AUDIO_DIR / f"{int(g)}.mp3", volume=volume)

def play_phone_fr(phone: str, pause_s: float = 0.25, volume: int = 100) -> None:
    """
    以法文電話常見「兩位一組」方式播放：06 12 34 56 78
    """
    groups = split_into_pairs(phone)
    for idx, g in enumerate(groups):
        play_pair_group(g, pause_s=pause_s, volume=volume)
        if idx != len(groups) - 1:
            time.sleep(pause_s)

def diff_positions(target: str, got: str) -> List[int]:
    """回傳不相同的位數 index（0-based）"""
    m = min(len(target), len(got))
    wrong = [i for i in range(m) if target[i] != got[i]]
    # 長度不一也算錯
    if len(target) != len(got):
        wrong.extend(list(range(m, max(len(target), len(got)))))
    return wrong

def format_fr(phone: str) -> str:
    """顯示成 0X XX XX XX XX"""
    groups = split_into_pairs(phone)
    return " ".join(groups)

# ---------- Main loop ----------
def main():
    ensure_ffplay()
    check_audio_files()

    total = 0
    correct = 0
    pause_s = 1.0
    print("=== French Phone Dictation Practice ===")
    print(f"Audio dir: {AUDIO_DIR.resolve()}")
    print("指令：r=重播, a=顯示答案, s=跳過下一題, q=離開")
    print("直接輸入你聽到的電話號碼（可含空格/破折號/括號都沒差）")
    print()

    while True:
        phone = gen_fr_phone()
        total += 1

        print(f"[Q{total}] Listen...")
        play_phone_fr(phone, pause_s=pause_s, volume=100)

        while True:
            ans = input("Your answer: ").strip().lower()

            if ans == "q":
                print()
                print(f"Score: {correct}/{total-1} (已完成題數：{total-1})")
                return

            if ans == "r":
                play_phone_fr(phone, pause_s=pause_s, volume=100)
                continue

            if ans == "a":
                print("Answer:", format_fr(phone))
                continue

            if ans == "s":
                print("Skipped. Answer:", format_fr(phone))
                print()
                break

            got = normalize_digits(ans)
            if not got:
                print("你沒有輸入任何數字。可輸入 r 重播。")
                continue

            if got == phone:
                correct += 1
                print("✅ Correct!", "Answer:", format_fr(phone))
            else:
                wrong = diff_positions(phone, got)
                show_wrong = ", ".join(str(i+1) for i in wrong[:12])
                extra = "..." if len(wrong) > 12 else ""
                print("❌ Not quite.")
                print("   Your :", got)
                print("   Answer:", format_fr(phone))
                print(f"   Wrong positions (1-based): {show_wrong}{extra}")
            print()
            break

if __name__ == "__main__":
    main()
