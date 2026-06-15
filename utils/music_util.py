import os
import ssl
import yt_dlp
import platform
import subprocess


# ---- HTTPS 인증 문제 우회 ----
ssl._create_default_https_context = ssl._create_unverified_context
from pathlib import Path
# ---- 저장 경로 ----
BASE_DIR = Path(__file__).resolve().parent.parent

FILE_PATH = BASE_DIR / "downloads" / "mp3"
os.makedirs(str(FILE_PATH), exist_ok=True)

ffmpeg_loc=""
if platform.system() == "Darwin":  # macOS
    # brew prefix 가져오기 (Intel / Apple Silicon 모두 대응)
    brew_prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
    ffmpeg_loc = str(Path(brew_prefix) / "bin")

elif platform.system() == "windows":
    ffmpeg_loc = str(Path(".") / "lib" / "ffmpeg" / "bin")

else:
    print(platform.system())
    raise RuntimeError(f"Unsupported OS: {platform.system()}")


def youtube_to_mp3(url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "ffmpeg_location": ffmpeg_loc,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": os.path.join(FILE_PATH, "%(title)s.%(ext)s"),
            "nocheckcertificate": True,
            "quiet": False,
            "no_warnings": True,

            # ---- 차단 우회용 User-Agent 세팅 ----
            "http_headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                              ' AppleWebKit/537.36 (KHTML, like Gecko)'
                              ' Chrome/120.0 Safari/537.36'
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("변환 완료!")
    except Exception as e:
        print("에러 발생:", e)


if __name__ == "__main__":
    test_url = input("다운받을 유튜브 링크: ")
    youtube_to_mp3(test_url)
