from contextlib import asynccontextmanager
from utils.audio_config import init_ffmpeg
from repositories.account_repository import ensure_auth_schema

@asynccontextmanager
async def lifespan(app):
    init_ffmpeg()
    ensure_auth_schema()
    yield
