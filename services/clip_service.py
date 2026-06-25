import subprocess
from pathlib import Path
import os

from pydub import AudioSegment

ROOT_DIR = Path(__file__).resolve().parent.parent

FFMPEG_BIN = (
        ROOT_DIR /
        "lib" /
        "ffmpeg" /
        "bin"
)

# ffmpeg, ffprobe 경로 등록
os.environ["PATH"] += ";" + str(FFMPEG_BIN)

LICKS_DIR = ROOT_DIR / "downloads" / "licks"
MP3_DIR = ROOT_DIR / "downloads" / "mp3"


def create_clip(
        file_name: str,
        start_sec: float,
        end_sec: float,
        clip_name: str = ""):

    source_file = MP3_DIR / file_name

    print("SOURCE =", source_file)
    print("EXISTS =", source_file.exists())

    audio = AudioSegment.from_mp3(
        str(source_file)
    )

    clip = audio[
           int(start_sec * 1000):
           int(end_sec * 1000)
           ]

    output_file = next_lick_name(
        file_name,
        clip_name
    )

    clip.export(
        str(output_file),
        format="mp3"
    )

    return output_file


def next_lick_name(
        original_file_name: str,
        clip_name: str = ""):

    LICKS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    stem = Path(
        original_file_name
    ).stem
    custom_name = (clip_name or "").strip()

    if custom_name:
        safe_name = (
            custom_name
            .replace(" ", "-")
            .replace("/", "_")
            .replace("\\", "_")
        )
        candidate = LICKS_DIR / f"{stem}-{safe_name}.mp3"

        if not candidate.exists():
            return candidate

        index = 2

        while True:
            candidate = LICKS_DIR / f"{stem}-{safe_name}-{index}.mp3"

            if not candidate.exists():
                return candidate

            index += 1

    index = 1

    while True:

        candidate = (
                LICKS_DIR /
                f"{stem}-lick-{index}.mp3"
        )

        if not candidate.exists():
            return candidate

        index += 1


def create_pitch_version(
        file_name: str,
        semitones: int):

    source_file = MP3_DIR / file_name

    output_file = (
        next_pitch_file_name(
            file_name,
            semitones
        )
    )

    pitch_factor = (
            2 ** (semitones / 12)
    )

    subprocess.run([
        "ffmpeg",
        "-i",
        str(source_file),

        "-af",
        f"rubberband=pitch={pitch_factor}",

        str(output_file),

        "-y"
    ], check=True)

    return output_file
def next_pitch_file_name(
        original_file_name: str,
        semitones: int):

    stem = Path(
        original_file_name
    ).stem

    sign = (
        "+"
        if semitones >= 0
        else ""
    )

    return (
            LICKS_DIR /
            f"{stem}-pitch{sign}{semitones}.mp3"
    )
