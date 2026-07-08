import re

from core.auth import hash_password, verify_password
from repositories import app_settings_repository
from repositories.db import execute, query_one


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")


def ensure_auth_schema():
    execute(
        """
        ALTER TABLE app_user
            ADD COLUMN IF NOT EXISTS email text,
            ADD COLUMN IF NOT EXISTS username text,
            ADD COLUMN IF NOT EXISTS password_hash text,
            ADD COLUMN IF NOT EXISTS terms_accepted_at timestamp with time zone
        """
    )
    execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS app_user_email_lower_key
            ON app_user (lower(email))
            WHERE email IS NOT NULL
        """
    )
    execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS app_user_username_lower_key
            ON app_user (lower(username))
            WHERE username IS NOT NULL
        """
    )


def normalize_email(value):
    return str(value or "").strip().lower()


def normalize_username(value):
    return str(value or "").strip()


def find_user_by_identifier(identifier):
    text = str(identifier or "").strip()
    if not text:
        return None

    return query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                id::text AS id,
                email,
                username,
                nickname,
                password_hash AS "passwordHash"
            FROM app_user
            WHERE lower(email) = lower(:'identifier')
               OR lower(username) = lower(:'identifier')
            LIMIT 1
        ) AS t
        """,
        {"identifier": text},
    )


def find_user_by_email_or_username(email, username):
    return query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                id::text AS id,
                email,
                username
            FROM app_user
            WHERE lower(email) = lower(:'email')
               OR lower(username) = lower(:'username')
            LIMIT 1
        ) AS t
        """,
        {"email": normalize_email(email), "username": normalize_username(username)},
    )


def create_user(email, username, password, country, week_start_day):
    email = normalize_email(email)
    username = normalize_username(username)

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise ValueError("이메일 주소를 확인해주세요.")

    if not USERNAME_PATTERN.match(username):
        raise ValueError("아이디는 3-32자의 영문, 숫자, ., _, - 만 사용할 수 있어요.")

    if len(str(password or "")) < 8:
        raise ValueError("비밀번호는 8자 이상으로 입력해주세요.")

    if find_user_by_email_or_username(email, username):
        raise ValueError("이미 사용 중인 이메일 또는 아이디예요.")

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO app_user (
                email,
                username,
                nickname,
                password_hash,
                terms_accepted_at
            )
            VALUES (
                :'email',
                :'username',
                :'username',
                :'password_hash',
                now()
            )
            RETURNING id::text AS id, email, username, nickname
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "email": email,
            "username": username,
            "password_hash": hash_password(password),
        },
    )

    app_settings_repository.save_for_user(
        created["id"],
        {
            "country": country,
            "weekStartDay": week_start_day,
        },
    )
    return created


def authenticate_user(identifier, password):
    user = find_user_by_identifier(identifier)
    if not user or not verify_password(password, user.get("passwordHash")):
        return None
    return user
