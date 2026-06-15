from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from navigation import NAVIGATION
from core.render import render_page

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
def home(request: Request):
    return render_page(request, "music/index.html", "음악")


@router.get("/music")
def music(request: Request):
    return render_page(request, "music/index.html", "음악")


@router.get("/account")
def account(request: Request):
    return render_page(request, "account/index.html", "가계")


@router.get("/dev")
def dev(request: Request):
    return render_page(request, "dev/index.html", "개발")