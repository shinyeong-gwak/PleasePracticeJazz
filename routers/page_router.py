from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.render import render_page
from repositories import app_settings_repository

router = APIRouter()


class SettingsPayload(BaseModel):
    country: str = "kr"
    weekStartDay: int = 0


@router.get("/")
def home(request: Request):
    return render_page(request, "music/index.html", "\uc74c\uc545")


@router.get("/music")
def music(request: Request):
    return render_page(request, "music/index.html", "\uc74c\uc545")


@router.get("/account")
def account(request: Request):
    return render_page(request, "account/index.html", "\uac00\uacc4")


@router.get("/dev")
def dev(request: Request):
    return render_page(request, "dev/index.html", "\uac1c\ubc1c")


@router.get("/settings")
def settings(request: Request):
    return render_page(request, "settings/index.html", "\uc124\uc815")


@router.get("/settings/api")
def settings_api():
    return JSONResponse(app_settings_repository.get_settings())


@router.post("/settings/api")
def update_settings_api(payload: SettingsPayload):
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return JSONResponse(
        app_settings_repository.update_settings(data)
    )
