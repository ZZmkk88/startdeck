"""startdeck: a lightweight self-hosted personal start page.

Your frequently used sites and services, grouped into sections on one
page, with favicons, instant search and a one-click status probe.
Single-file FastAPI backend + SQLite + one static page.
Design notes live in NOTES.md.
"""
import hashlib
import os
import secrets
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("STARTDECK_DB_PATH", str(BASE_DIR / "data" / "startdeck.db"))
TOKEN_TTL_SECONDS = 24 * 60 * 60
INITIAL_USERNAME = os.environ.get("SD_INITIAL_USERNAME", "admin")
INITIAL_PASSWORD = os.environ.get("SD_INITIAL_PASSWORD", "admin123")
PROBE_TIMEOUT_SECONDS = 6.0
MAX_SECTION_NAME = 60
MAX_LINK_NAME = 100
MAX_URL_LENGTH = 2048
MAX_DESC_LENGTH = 500


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 200_000
    ).hex()


def favicon_url_for(url: str) -> str:
    """The icon a browser would try first: <scheme>://<host>/favicon.ico.

    The frontend falls back to a letter tile when this image fails to
    load, so sites without a favicon still get a placeholder.
    """
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


# ---------------------------------------------------------------------------
# database
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                expires_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                icon_url TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_links_section
                ON links(section_id, sort_order, id);
            """
        )
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (INITIAL_USERNAME,)
        ).fetchone()
        if row is None:
            salt = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO users (username, password_hash, salt,"
                " must_change_password, created_at) VALUES (?, ?, ?, 1, ?)",
                (INITIAL_USERNAME, hash_password(INITIAL_PASSWORD, salt), salt, iso(utcnow())),
            )


# ---------------------------------------------------------------------------
# status probe
# ---------------------------------------------------------------------------

def probe(url: str, timeout: float = PROBE_TIMEOUT_SECONDS) -> dict:
    """One HTTP probe. Up = status 2xx/3xx; redirects are not followed so
    a redirecting service still counts as reachable, like sitepulse does.
    Anything else (4xx/5xx, timeout, connection failure) is down."""
    start = time.perf_counter()

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    code = None
    try:
        req = urllib.request.Request(
            url, method="GET", headers={"User-Agent": "startdeck/1.0"}
        )
        with opener.open(req, timeout=timeout) as resp:
            code = resp.getcode()
            resp.read(1024)
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:  # URLError, TimeoutError, ssl errors, ...
        reason = getattr(e, "reason", None) or str(e) or e.__class__.__name__
        return {
            "up": False,
            "status_code": None,
            "response_ms": None,
            "error": str(reason)[:300],
            "checked_at": iso(utcnow()),
        }
    ms = int((time.perf_counter() - start) * 1000)
    up = code is not None and 200 <= code < 400
    return {
        "up": up,
        "status_code": code,
        "response_ms": ms,
        "error": None if up else f"HTTP {code}",
        "checked_at": iso(utcnow()),
    }


# ---------------------------------------------------------------------------
# app + auth
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="startdeck", lifespan=lifespan)


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class SectionIn(BaseModel):
    name: str


class LinkIn(BaseModel):
    section_id: int
    name: str
    url: str
    description: str = ""


class LinkUpdateIn(BaseModel):
    section_id: int | None = None
    name: str | None = None
    url: str | None = None
    description: str | None = None


def current_user(request: Request) -> sqlite3.Row:
    auth = request.headers.get("Authorization", "")
    token = auth[len("Bearer "):].strip() if auth.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token = ? AND s.expires_at > ?",
            (token, time.time()),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return row


@app.post("/api/login")
def login(body: LoginIn):
    init_db()
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (body.username.strip(),)
        ).fetchone()
        if user is None or hash_password(body.password, user["salt"]) != user["password_hash"]:
            raise HTTPException(status_code=401, detail="用户名或密码不正确")
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user["id"], time.time() + TOKEN_TTL_SECONDS),
        )
    return {
        "token": token,
        "username": user["username"],
        "must_change_password": bool(user["must_change_password"]),
    }


@app.post("/api/logout")
def logout(request: Request, user: sqlite3.Row = Depends(current_user)):
    token = request.headers.get("Authorization", "")[len("Bearer "):].strip()
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return {"ok": True}


@app.post("/api/change-password")
def change_password(body: ChangePasswordIn, user: sqlite3.Row = Depends(current_user)):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    if hash_password(body.old_password, user["salt"]) != user["password_hash"]:
        raise HTTPException(status_code=400, detail="旧密码不正确")
    salt = secrets.token_hex(16)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ?,"
            " must_change_password = 0 WHERE id = ?",
            (hash_password(body.new_password, salt), salt, user["id"]),
        )
    return {"ok": True}


@app.get("/api/me")
def me(user: sqlite3.Row = Depends(current_user)):
    return {
        "username": user["username"],
        "must_change_password": bool(user["must_change_password"]),
    }


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------

def validate_section_name(name: str) -> str:
    name = (name or "").strip()
    if not name or len(name) > MAX_SECTION_NAME:
        raise HTTPException(status_code=400, detail="分组名为空或过长")
    return name


def get_section_row(section_id: int, user_id: int) -> sqlite3.Row:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sections WHERE id = ? AND user_id = ?",
            (section_id, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="分组不存在")
    return row


def link_json(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "section_id": row["section_id"],
        "name": row["name"],
        "url": row["url"],
        "description": row["description"],
        "icon_url": row["icon_url"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def section_json(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    links = conn.execute(
        "SELECT * FROM links WHERE section_id = ? ORDER BY sort_order, id",
        (row["id"],),
    ).fetchall()
    return {
        "id": row["id"],
        "name": row["name"],
        "links": [link_json(r) for r in links],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@app.get("/api/sections")
def list_sections(user: sqlite3.Row = Depends(current_user)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sections WHERE user_id = ? ORDER BY sort_order, id",
            (user["id"],),
        ).fetchall()
        return [section_json(conn, r) for r in rows]


@app.post("/api/sections")
def create_section(body: SectionIn, user: sqlite3.Row = Depends(current_user)):
    name = validate_section_name(body.name)
    now = iso(utcnow())
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) + 1 AS nxt FROM sections WHERE user_id = ?",
            (user["id"],),
        ).fetchone()
        cur = conn.execute(
            "INSERT INTO sections (user_id, name, sort_order, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (user["id"], name, row["nxt"], now, now),
        )
        created = conn.execute(
            "SELECT * FROM sections WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return section_json(conn, created)


@app.put("/api/sections/{section_id}")
def update_section(section_id: int, body: SectionIn, user: sqlite3.Row = Depends(current_user)):
    get_section_row(section_id, user["id"])
    name = validate_section_name(body.name)
    with get_conn() as conn:
        conn.execute(
            "UPDATE sections SET name = ?, updated_at = ? WHERE id = ?",
            (name, iso(utcnow()), section_id),
        )
        row = conn.execute(
            "SELECT * FROM sections WHERE id = ?", (section_id,)
        ).fetchone()
        return section_json(conn, row)


@app.delete("/api/sections/{section_id}")
def delete_section(section_id: int, user: sqlite3.Row = Depends(current_user)):
    get_section_row(section_id, user["id"])
    with get_conn() as conn:
        conn.execute("DELETE FROM links WHERE section_id = ?", (section_id,))
        conn.execute("DELETE FROM sections WHERE id = ?", (section_id,))
    return {"ok": True}


# ---------------------------------------------------------------------------
# links
# ---------------------------------------------------------------------------

def validate_link_name(name: str) -> str:
    name = (name or "").strip()
    if not name or len(name) > MAX_LINK_NAME:
        raise HTTPException(status_code=400, detail="链接名称为空或过长")
    return name


def validate_url(url: str) -> str:
    url = (url or "").strip()
    if not url or len(url) > MAX_URL_LENGTH:
        raise HTTPException(status_code=400, detail="网址为空或过长")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="只支持 http/https 网址")
    return url


def validate_description(description: str) -> str:
    description = (description or "").strip()
    if len(description) > MAX_DESC_LENGTH:
        raise HTTPException(status_code=400, detail="说明过长")
    return description


def get_link_row(link_id: int, user_id: int) -> sqlite3.Row:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM links WHERE id = ? AND user_id = ?", (link_id, user_id)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="链接不存在")
    return row


@app.get("/api/links")
def list_links(
    q: str = "",
    section_id: int | None = None,
    user: sqlite3.Row = Depends(current_user),
):
    clauses = ["user_id = ?"]
    params: list = [user["id"]]
    if section_id is not None:
        clauses.append("section_id = ?")
        params.append(section_id)
    if q.strip():
        clauses.append("(name LIKE ? OR description LIKE ? OR url LIKE ?)")
        like = f"%{q.strip()}%"
        params.extend([like, like, like])
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM links WHERE " + " AND ".join(clauses)
            + " ORDER BY section_id, sort_order, id",
            params,
        ).fetchall()
    return [link_json(r) for r in rows]


@app.post("/api/links")
def create_link(body: LinkIn, user: sqlite3.Row = Depends(current_user)):
    get_section_row(body.section_id, user["id"])
    name = validate_link_name(body.name)
    url = validate_url(body.url)
    description = validate_description(body.description)
    now = iso(utcnow())
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) + 1 AS nxt FROM links WHERE section_id = ?",
            (body.section_id,),
        ).fetchone()
        cur = conn.execute(
            "INSERT INTO links (user_id, section_id, name, url, description,"
            " icon_url, sort_order, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], body.section_id, name, url, description,
             favicon_url_for(url), row["nxt"], now, now),
        )
        created = conn.execute(
            "SELECT * FROM links WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return link_json(created)


@app.get("/api/links/{link_id}")
def get_link(link_id: int, user: sqlite3.Row = Depends(current_user)):
    return link_json(get_link_row(link_id, user["id"]))


@app.put("/api/links/{link_id}")
def update_link(link_id: int, body: LinkUpdateIn, user: sqlite3.Row = Depends(current_user)):
    existing = get_link_row(link_id, user["id"])
    fields: dict = {}
    if body.section_id is not None:
        get_section_row(body.section_id, user["id"])  # 404 if target missing
        fields["section_id"] = body.section_id
    if body.name is not None:
        fields["name"] = validate_link_name(body.name)
    if body.url is not None:
        fields["url"] = validate_url(body.url)
        fields["icon_url"] = favicon_url_for(fields["url"])
    if body.description is not None:
        fields["description"] = validate_description(body.description)
    if fields:
        fields["updated_at"] = iso(utcnow())
        sets = ", ".join(f"{k} = ?" for k in fields)
        with get_conn() as conn:
            conn.execute(
                f"UPDATE links SET {sets} WHERE id = ?", (*fields.values(), link_id)
            )
    return link_json(get_link_row(link_id, user["id"]))


@app.delete("/api/links/{link_id}")
def delete_link(link_id: int, user: sqlite3.Row = Depends(current_user)):
    get_link_row(link_id, user["id"])
    with get_conn() as conn:
        conn.execute("DELETE FROM links WHERE id = ?", (link_id,))
    return {"ok": True}


# ---------------------------------------------------------------------------
# status probes
# ---------------------------------------------------------------------------

@app.post("/api/links/{link_id}/check")
def check_link(link_id: int, user: sqlite3.Row = Depends(current_user)):
    row = get_link_row(link_id, user["id"])
    result = probe(row["url"])
    return {"link_id": link_id, **result}


@app.post("/api/check-all")
def check_all(user: sqlite3.Row = Depends(current_user)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, url FROM links WHERE user_id = ? ORDER BY id", (user["id"],)
        ).fetchall()
    targets = [(r["id"], r["url"]) for r in rows]
    if not targets:
        return []
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda t: probe(t[1]), targets))
    return [
        {"link_id": link_id, **result}
        for (link_id, _), result in zip(targets, results)
    ]


# ---------------------------------------------------------------------------
# static page
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


init_db()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
