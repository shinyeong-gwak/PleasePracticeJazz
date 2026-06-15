from contextlib import asynccontextmanager
from utils.audio_config import init_ffmpeg

@asynccontextmanager
async def lifespan(app):
    init_ffmpeg()
    yield