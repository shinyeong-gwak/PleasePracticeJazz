import os
import platform
import ssl
import subprocess
from pathlib import Path

import yt_dlp

ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).resolve().parent.parent
MP3_DIR = BASE_DIR / "downloads" / "mp3"
MP3_DIR.mkdir(parents=True, exist_ok=True)


def get_ffmpeg_location():

    system = platform.system()

    if system == "Darwin":
        brew_prefix = subprocess.check_output(
            ["brew", "--prefix"],
            text=True
        ).strip()
        return str(Path(brew_prefix) / "bin")

    if system == "Windows":
        return str(Path(".") / "lib" / "ffmpeg" / "bin")

    if system == "Linux":
        return "/usr/bin/ffmpeg"

    raise RuntimeError(f"Unsupported OS: {system}")


FFMPEG_LOCATION = get_ffmpeg_location()


def build_headers():

    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }


def extract_playlist_entries(url):

    ydl_opts = {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "http_headers": build_headers(),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = []

    for entry in info.get("entries", []):
        if not entry:
            continue

        video_id = entry.get("id")

        if not video_id:
            continue

        entries.append({
            "id": video_id,
            "title": entry.get("title") or video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    return entries


def expected_mp3_filename(info):

    source_path = Path(info["requested_downloads"][0]["filepath"])
    return source_path.with_suffix(".mp3").name


def download_youtube_entry(video_url):

    ydl_opts = {
        "format": "bestaudio/best",
        "ffmpeg_location": FFMPEG_LOCATION,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": os.path.join(MP3_DIR, "%(title)s.%(ext)s"),
        "nocheckcertificate": True,
        "quiet": False,
        "no_warnings": True,
        "http_headers": build_headers(),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    return {
        "id": info["id"],
        "title": info.get("title") or info["id"],
        "url": video_url,
        "filename": expected_mp3_filename(info)
    }


if __name__ == "__main__":
    test_url = input("다운받을 유튜브 링크: ")

    if "playlist" in test_url:
        print(extract_playlist_entries(test_url))
    else:
        print(download_youtube_entry(test_url))
