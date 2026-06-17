import os
import platform
from pathlib import Path
from pydub import AudioSegment
import shutil


def get_ffmpeg_bin():
    system = platform.system()

    if system == "Darwin":
        possible_paths = [
            Path("/opt/homebrew/bin"),  # Apple Silicon
            Path("/usr/local/bin"),     # Intel
        ]

        for p in possible_paths:
            if (p / "ffmpeg").exists() and (p / "ffprobe").exists():
                return p

        # fallback: PATH 탐색
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")

        if ffmpeg and ffprobe:
            return Path(ffmpeg).parent

        raise RuntimeError("ffmpeg not found on macOS")


    elif system == "Windows":
        base = Path(".") / "lib" / "ffmpeg" / "bin"

        ffmpeg = base / "ffmpeg.exe"
        ffprobe = base / "ffprobe.exe"

        if ffmpeg.exists() and ffprobe.exists():
            return base

        raise RuntimeError("ffmpeg not found on Windows")


    elif system == "Linux":
        base = Path("/usr/bin")

        if (base / "ffmpeg").exists() and (base / "ffprobe").exists():
            return base

        raise RuntimeError("ffmpeg not found on Linux")

    else:
        raise RuntimeError(system)



def init_ffmpeg():
    bin_path = get_ffmpeg_bin()

    system = platform.system()

    if system == "Windows":
        AudioSegment.converter = str(bin_path / "ffmpeg.exe")
        AudioSegment.ffprobe = str(bin_path / "ffprobe.exe")
    else:

        os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")
        AudioSegment.converter = str(bin_path / "ffmpeg")
        AudioSegment.ffprobe = str(bin_path / "ffprobe")