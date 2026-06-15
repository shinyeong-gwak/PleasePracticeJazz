from fastapi import FastAPI
from contextlib import asynccontextmanager

from routers.music_router import router as music_router
from routers.audio_router import router as audio_router
from routers.clip_router import router as clip_router
from routers.page_router import router as page_router
from routers.lick_router import router as  lick_router

from core.lifespan import lifespan
from fastapi.staticfiles import StaticFiles


app = FastAPI(lifespan=lifespan)

app.include_router(page_router)
app.include_router(music_router)
app.include_router(clip_router)
app.include_router(audio_router)
# app.include_router(render_router)
app.include_router(lick_router)

app.mount("/static", StaticFiles(directory="static"), name="static")