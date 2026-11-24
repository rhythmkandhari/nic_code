"""Database access for SQLite (default, zero setup) or Oracle.

Choose the backend in `.streamlit/secrets.toml`:

    [database]
    backend = "sqlite"          # or "oracle"
    # Oracle only:
    user = "govintel"
    password = "..."
    dsn = "127.0.0.1:1521/XEPDB1"

All SQL in the app uses named binds (`:p_email`), which both sqlite3 and
python-oracledb understand, so the same statements run on either backend.
"""
from __future__ import annotations

import contextlib
import csv
import sqlite3
from typing import Any, Iterator

import streamlit as st

from . import NIC_CSV, ROOT

SQLITE_PATH = ROOT / "data" / "govintel.db"
SQLITE_SCHEMA = ROOT / "sql" / "schema_sqlite.sql"


def settings() -> dict[str, Any]:
    try:
        return dict(st.secrets.get("database", {}))
    except Exception:  # no secrets.toml at all -> defaults
        return {}


def backend() -> str:
    return str(settings().get("backend", "sqlite")).lower()


@st.cache_resource(show_spinner=False)
def _oracle_pool():
    import oracledb  # thin mode: no Oracle Instant Client needed

    s = settings()
    missing = [k for k in ("user", "password", "dsn") if not s.get(k)]
    if missing:
        raise RuntimeError(
            f"Oracle backend selected but {', '.join(missing)} missing in "
            ".streamlit/secrets.toml [database]"
        )
    return oracledb.create_pool(
        user=s["user"], password=s["password"], dsn=s["dsn"], min=1, max=4, increment=1
    )


@contextlib.contextmanager
def connect() -> Iterator[Any]:
    """Yield a connection; commit on success, roll back on error, always close."""
    if backend() == "oracle":
        conn = _oracle_pool().acquire()
    else:
        SQLITE_PATH.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _rows(cur) -> list[dict[str, Any]]:
    cols = [d[0].upper() for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def fetch_all(sql: str, params: dict | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        return _rows(cur)


def fetch_one(sql: str, params: dict | None = None) -> dict[str, Any] | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: dict | None = None) -> int:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        return cur.rowcount


def _seed_nic_codes(conn) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM NIC_CODES")
    if cur.fetchone()[0]:
        return
    with open(NIC_CSV, newline="", encoding="utf-8") as f:
        rows = [
            {"p_code": r["NICcode"].strip().zfill(5), "p_descr": r["NIC description"].strip()}
            for r in csv.DictReader(f)
        ]
    cur.executemany(
        "INSERT INTO NIC_CODES (NIC_CODE, DESCRIPTION) VALUES (:p_code, :p_descr)", rows
    )


@st.cache_resource(show_spinner="Preparing database...")
def init_db() -> str:
    """Create tables (SQLite only) and load the NIC codes once per server process."""
    with connect() as conn:
        if backend() == "sqlite":
            conn.executescript(SQLITE_SCHEMA.read_text(encoding="utf-8"))
        _seed_nic_codes(conn)
    return backend()
