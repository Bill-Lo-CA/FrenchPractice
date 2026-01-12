import yt_dlp
import sys
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: python download_youtube.py <YouTube_URL> <output_file_path>")
    sys.exit(1)

video_url = f"https://www.youtube.com/watch?v={sys.argv[1]}"
base_name = sys.argv[2]

output_dir = Path("assets")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / f"{base_name}.mp3"
counter = 1

while output_path.exists():
    output_path = output_dir / f"{base_name}_{counter}.mp3"
    counter += 1

outtmpl = str(output_path.with_suffix('.%(ext)s'))

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': outtmpl,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'no_warnings': True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])

print(f"Downloaded and converted to MP3: {output_path}")