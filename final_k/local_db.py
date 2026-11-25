"""Offline SQLite database shared by all pages.

The whole database lives in one file, govintel.db, in the project folder.
Tables are created automatically the first time the app connects.
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "govintel.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS LOGIN_DETAILS (
    ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    USER_NAME TEXT NOT NULL UNIQUE,
    PASSWORD  TEXT NOT NULL
);

-- One row per search on the Home page; also used as the user's search history
CREATE TABLE IF NOT EXISTS RESULT_CODES (
    ID            INTEGER PRIMARY KEY AUTOINCREMENT,
    ACTIVITY_NAME TEXT NOT NULL,              -- what the user typed
    NIC_CODE      TEXT DEFAULT 'N/A',
    DESCRIPTION   TEXT,                       -- query translated to English
    PREDICTED_NIC TEXT,                       -- top NIC matches
    USER_NAME     TEXT NOT NULL DEFAULT 'anonymous',
    CREATED_AT    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS IDX_RESULT_CODES_USER ON RESULT_CODES (USER_NAME);

CREATE TABLE IF NOT EXISTS CONTACT_INFO (
    ID            INTEGER PRIMARY KEY AUTOINCREMENT,
    YOUR_NAME     TEXT NOT NULL,
    YOUR_MAIN     TEXT NOT NULL,              -- email (column name kept from the Oracle version)
    YOUR_FEEDBACK TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS NIC_CODES (
    ID            INTEGER PRIMARY KEY,
    ACTIVITY_NAME TEXT NOT NULL CHECK (length(ACTIVITY_NAME) <= 50),
    NIC_CODE      TEXT NOT NULL UNIQUE CHECK (length(NIC_CODE) = 5),
    DESCRIPTION   TEXT NOT NULL CHECK (length(DESCRIPTION) <= 200)
);
"""


def get_connection():
    """Open a connection to the local database, creating the tables if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn
