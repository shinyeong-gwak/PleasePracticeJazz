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


def parse_browser_cookie_spec(raw_value):

    text = str(raw_value or "").strip()

    if not text:
        return None

    browser_and_keyring, _, profile_and_container = text.partition(":")
    browser, _, keyring = browser_and_keyring.partition("+")
    profile, _, container = profile_and_container.partition("::")

    parts = [browser.strip()]

    if profile or keyring or container:
        parts.append(profile.strip() or None)
    if keyring or container:
        parts.append(keyring.strip() or None)
    if container:
        parts.append(container.strip() or None)

    return tuple(parts)


def build_ytdlp_base_opts():

    opts = {
        "nocheckcertificate": True,
        "http_headers": build_headers(),
        "retries": 3,
        "extractor_retries": 3,
        "fragment_retries": 3,
        "file_access_retries": 3,
        "retry_sleep_functions": {
            "http": lambda attempt: min(2 * attempt, 6),
            "fragment": lambda attempt: min(2 * attempt, 6),
            "file_access": lambda attempt: min(2 * attempt, 6),
            "extractor": lambda attempt: min(2 * attempt, 6),
        },
        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android_vr",
                    "web_safari",
                    "tv_downgraded",
                ]
            }
        },
    }

    cookie_file = str(
        os.getenv("YTDLP_COOKIES_FILE", "")
    ).strip()
    browser_cookie_spec = parse_browser_cookie_spec(
        os.getenv("YTDLP_COOKIES_FROM_BROWSER", "")
    )
    impersonate = str(
        os.getenv("YTDLP_IMPERSONATE", "")
    ).strip()

    if cookie_file:
        opts["cookiefile"] = cookie_file

    if browser_cookie_spec:
        opts["cookiesfrombrowser"] = browser_cookie_spec

    if impersonate:
        opts["impersonate"] = impersonate

    return opts


def extract_playlist_entries(url):

    ydl_opts = {
        **build_ytdlp_base_opts(),
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
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
            "artist": (
                entry.get("artist")
                or entry.get("uploader")
                or entry.get("channel")
                or ""
            ),
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    return entries


def expected_mp3_filename(info):

    source_path = Path(info["requested_downloads"][0]["filepath"])
    return source_path.with_suffix(".mp3").name


def download_youtube_entry(video_url):

    ydl_opts = {
        **build_ytdlp_base_opts(),
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
        "quiet": False,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    return {
        "id": info["id"],
        "title": info.get("title") or info["id"],
        "artist": (
            info.get("artist")
            or info.get("uploader")
            or info.get("channel")
            or ""
        ),
        "url": video_url,
        "filename": expected_mp3_filename(info)
    }


if __name__ == "__main__":
    test_url = input("다운받을 유튜브 링크: ")

    if "playlist" in test_url:
        print(extract_playlist_entries(test_url))
    else:
        print(download_youtube_entry(test_url))
