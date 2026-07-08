from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from core.auth import (
    AUTH_COOKIE_NAME,
    AUTH_SECRET,
    create_access_token,
    verify_access_token,
)
from core.render import render_page
from repositories.account_repository import authenticate_user, create_user
from repositories.db import get_or_create_user_id


router = APIRouter()


class LoginPayload(BaseModel):
    identifier: str = ""
    password: str = ""
    accessKey: str = ""


class SignupPayload(BaseModel):
    email: str
    username: str
    password: str
    country: str = "kr"
    weekStartDay: int = 1
    acceptedTerms: bool = False


def _set_auth_cookie(response, token):
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


@router.get("/login")
def login_page(request: Request):
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token and verify_access_token(token):
        return RedirectResponse("/", status_code=303)

    return render_page(request, "auth/login.html", "로그인")


@router.get("/signup")
def signup_page(request: Request):
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token and verify_access_token(token):
        return RedirectResponse("/", status_code=303)

    return render_page(request, "auth/signup.html", "회원가입")


@router.post("/auth/login")
def login_api(payload: LoginPayload):
    user = authenticate_user(payload.identifier, payload.password)

    if user:
        token = create_access_token(user["id"])
    else:
        key = str(payload.accessKey or "").strip()
        if not key or key != AUTH_SECRET:
            return JSONResponse(
                {"message": "아이디 또는 비밀번호를 확인해주세요."},
                status_code=401,
            )
        token = create_access_token(get_or_create_user_id())

    response = JSONResponse(
        {
            "accessToken": token,
            "tokenType": "bearer",
        }
    )
    return _set_auth_cookie(response, token)


@router.post("/auth/signup")
def signup_api(payload: SignupPayload):
    if not payload.acceptedTerms:
        return JSONResponse({"message": "이용약관에 동의해주세요."}, status_code=400)

    try:
        user = create_user(
            payload.email,
            payload.username,
            payload.password,
            payload.country,
            payload.weekStartDay,
        )
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)

    token = create_access_token(user["id"])
    response = JSONResponse(
        {
            "accessToken": token,
            "tokenType": "bearer",
            "user": user,
        },
        status_code=201,
    )
    return _set_auth_cookie(response, token)


@router.get("/auth/token")
def token_api(request: Request):
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token or not verify_access_token(token):
        return JSONResponse({"message": "인증이 필요해요."}, status_code=401)

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
