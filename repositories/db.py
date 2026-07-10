import json
import os
import subprocess
from contextvars import ContextVar
import re

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None


DEFAULT_USER_NICKNAME = "default"
current_user_id = ContextVar("current_user_id", default=None)
PARAM_PATTERN = re.compile(r":'([A-Za-z0-9_]+)'")
_connection = None


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


def _prepare_psycopg_sql(sql, params=None):
    values = []

    def replace(match):
        key = match.group(1)
        values.append((params or {}).get(key))
        return "%s"

    prepared_sql = PARAM_PATTERN.sub(replace, sql)
    return prepared_sql, values


def _get_connection():
    global _connection

    if psycopg is None:
        return None

    try:
        if _connection is not None and not _connection.closed:
            return _connection

        _connection = psycopg.connect(_build_dsn(), autocommit=True)
        return _connection
    except Exception:
        _connection = None
        return None


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
    connection = _get_connection()
    if connection is not None:
        prepared_sql, values = _prepare_psycopg_sql(sql, params)
        try:
            with connection.cursor() as cursor:
                cursor.execute(prepared_sql, values)
                if cursor.description:
                    rows = cursor.fetchall()
                    return "\n".join(
                        _render_db_row(row)
                        for row in rows
                    ).strip()
                return ""
        except Exception:
            try:
                connection.close()
            except Exception:
                pass
            globals()["_connection"] = None
            raise

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


def _render_db_row(row):
    if not isinstance(row, tuple):
        row = tuple(row)

    if len(row) == 1:
        value = row[0]
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return "" if value is None else str(value)

    rendered = []
    for value in row:
        if isinstance(value, (dict, list)):
            rendered.append(json.dumps(value, ensure_ascii=False))
        elif value is None:
            rendered.append("")
        else:
            rendered.append(str(value))
    return "\t".join(rendered)


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
