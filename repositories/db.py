import json
import os
import subprocess
from contextvars import ContextVar


DEFAULT_USER_NICKNAME = "default"
current_user_id = ContextVar("current_user_id", default=None)


def _build_dsn():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    dbname = os.getenv("PGDATABASE", "postgres")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD")

    auth = user
    if password:
        auth = f"{user}:{password}"

    return f"postgresql://{auth}@{host}:{port}/{dbname}"


def _psql_args():
    return [
        "psql",
        _build_dsn(),
        "-X",
        "--no-psqlrc",
        "-qAt",
        "-v",
        "ON_ERROR_STOP=1",
    ]


def _render_params(params):
    args = []
    for key, value in (params or {}).items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif value is None:
            rendered = ""
        else:
            rendered = str(value)
        args.extend(["-v", f"{key}={rendered}"])
    return args


def _run(sql, params=None):
    command = _psql_args() + _render_params(params)
    result = subprocess.run(
        command,
        input=sql,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PGCLIENTENCODING": "UTF8"},
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip() or "database query failed"
        )

    return result.stdout.strip()


def query_rows(sql, params=None):
    output = _run(sql, params)
    if not output:
        return []

    rows = []
    for line in output.splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            rows.append(json.loads(text))
        except json.JSONDecodeError:
            rows.append({"value": text})
    return rows


def query_one(sql, params=None):
    rows = query_rows(sql, params)
    return rows[0] if rows else None


def execute(sql, params=None):
    _run(sql, params)


def get_or_create_user_id():
    scoped_user_id = current_user_id.get()
    if scoped_user_id:
        return scoped_user_id

    rows = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM app_user
            ORDER BY created_at
            LIMIT 1
        ) AS t
        """
    )

    if rows:
        return rows[0]["id"]

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO app_user (nickname)
            VALUES (:'nickname')
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {"nickname": DEFAULT_USER_NICKNAME},
    )

    return created["id"] if created else None
