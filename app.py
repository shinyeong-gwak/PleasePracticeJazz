from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager

import core.lifespan
from core.auth import AUTH_COOKIE_NAME, extract_bearer_token, verify_access_token
from routers.auth_router import router as auth_router
from routers.music_router import router as music_router
from routers.audio_router import router as audio_router
from routers.clip_router import router as clip_router
from routers.page_router import router as page_router
from routers.lick_router import router as  lick_router
from routers.render_router import router as  render_router

from core.lifespan import lifespan
from fastapi.staticfiles import StaticFiles
from repositories.db import current_user_id


app = FastAPI(lifespan=lifespan)

PUBLIC_PATH_PREFIXES = (
    "/static",
    "/auth/login",
    "/auth/signup",
    "/auth/logout",
    "/login",
    "/signup",
    "/openapi.json",
    "/docs",
    "/redoc",
)


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATH_PREFIXES or path.startswith("/static")


def _looks_like_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept or not accept


def _is_uuid_like(value: str | None) -> bool:
    text = str(value or "")
    return len(text) == 36 and text.count("-") == 4


@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path

    if _is_public_path(path):
        return await call_next(request)

    auth_header = request.headers.get("authorization")
    token = extract_bearer_token(auth_header)

    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)

    payload = verify_access_token(token) if token else None
    if not token or not payload:
        if _looks_like_html(request):
            return RedirectResponse("/login", status_code=303)

        return JSONResponse(
            {"message": "인증이 필요해요."},
            status_code=401,
        )

    request.state.authenticated = True
    request.state.access_token = token
    user_id = payload.get("sub") if _is_uuid_like(payload.get("sub")) else None
    request.state.user_id = user_id
    token_handle = current_user_id.set(user_id)
    try:
        return await call_next(request)
    finally:
        current_user_id.reset(token_handle)


app.include_router(auth_router)
app.include_router(page_router)
app.include_router(music_router)
app.include_router(clip_router)
app.include_router(audio_router)
app.include_router(render_router)
app.include_router(lick_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
