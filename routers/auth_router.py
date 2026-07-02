from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from core.auth import (
    AUTH_COOKIE_NAME,
    AUTH_SECRET,
    create_access_token,
    verify_access_token,
)
from core.render import templates


router = APIRouter()


class LoginPayload(BaseModel):
    accessKey: str


@router.get("/login")
def login_page(request: Request):
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token and verify_access_token(token):
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "page_title": "로그인",
        },
    )


@router.post("/auth/login")
def login_api(payload: LoginPayload):
    key = str(payload.accessKey or "").strip()
    if key != AUTH_SECRET:
        return JSONResponse(
            {"message": "키가 맞지 않아요."},
            status_code=401,
        )

    token = create_access_token()
    response = JSONResponse(
        {
            "accessToken": token,
            "tokenType": "bearer",
        }
    )
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=60 * 60 * 24 * 14,
    )
    return response


@router.get("/auth/token")
def token_api(request: Request):
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token or not verify_access_token(token):
        return JSONResponse(
            {"message": "인증이 필요해요."},
            status_code=401,
        )

    return JSONResponse(
        {
            "accessToken": token,
            "tokenType": "bearer",
        }
    )


@router.post("/auth/logout")
def logout_api():
    response = JSONResponse({"success": True})
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return response
