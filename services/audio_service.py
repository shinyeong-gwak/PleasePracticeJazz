# services/audio_service.py

from pydub import AudioSegment
from pathlib import Path
import uuid
import librosa
import numpy as np
from time import time

from pydub.utils import which
from utils.audio_config import init_ffmpeg

LICKS_DIR = Path("downloads/licks")
OUTPUT_DIR = Path("downloads/processed")
class AudioService:

    def __init__(self):
        init_ffmpeg()

    @staticmethod
    def load(file_name: str) -> AudioSegment:
        path = LICKS_DIR / file_name
        print("which ffprobe =", which("ffprobe"))
        print("which ffmpeg =", which("ffmpeg"))
        return AudioSegment.from_file(path)


    @staticmethod
    def save(audio: AudioSegment) -> str:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cleanup_processed_files(OUTPUT_DIR)

        out_name = f"{uuid.uuid4().hex}_{int(time.time())}.mp3"
        out_path = OUTPUT_DIR / out_name

        audio.export(out_path, format="mp3")
        return out_name


def change_pitch(audio: AudioSegment, semitone: int) -> AudioSegment:
    rate = 2 ** (semitone / 12)
    new_frame_rate = int(audio.frame_rate * rate)

    shifted = audio._spawn(audio.raw_data, overrides={
        "frame_rate": new_frame_rate
    })

    return shifted.set_frame_rate(audio.frame_rate)


def change_tempo(audio: AudioSegment, rate: float) -> AudioSegment:
    import numpy as np
    import librosa

    samples = np.array(audio.get_array_of_samples())

    # Stereo
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))

        y_left = samples[:, 0].astype(np.float32) / 32768.0
        y_right = samples[:, 1].astype(np.float32) / 32768.0

        y_left = librosa.effects.time_stretch(y_left, rate=rate)
        y_right = librosa.effects.time_stretch(y_right, rate=rate)

        y = np.column_stack((y_left, y_right))

        y = np.clip(y, -1.0, 1.0)
        y = (y * 32767).astype(np.int16)

        return AudioSegment(
            y.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=2,
            channels=2
        )

    # Mono
    else:
        y = samples.astype(np.float32) / 32768.0

        y = librosa.effects.time_stretch(y, rate=rate)

        y = np.clip(y, -1.0, 1.0)
        y = (y * 32767).astype(np.int16)

        return AudioSegment(
            y.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=2,
            channels=1
        )

def process_audio(file_name: str, pitch: int, tempo: float) -> str:
    audio = AudioService.load(file_name)

    if tempo != 1.0:
        audio = change_tempo(audio, tempo)

    if pitch != 0:
        audio = change_pitch(audio, pitch)


    return AudioService.save(audio)

from pathlib import Path
import time



def cleanup_processed_files(PROCESSED_DIR, max_age_seconds=600):
    now = time.time()

    for f in PROCESSED_DIR.glob("*.mp3"):
        try:
            if now - f.stat().st_mtime > max_age_seconds:
                f.unlink()
        except Exception:
            pass