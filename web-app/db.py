"""Local portfolio storage. Each signed browser session owns its lectures."""
import secrets
import sqlite3
from contextlib import closing
from flask import g


def initialize(path):
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                name TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lectures (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL,
                summary TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
                updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS library ON lectures(owner, updated);
        """)
        connection.execute("INSERT OR IGNORE INTO settings VALUES ('signing', ?)",
                           (secrets.token_hex(32),))
        return connection.execute("SELECT value FROM settings WHERE name='signing'").fetchone()[0]


def database(path):
    if 'db' not in g:
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_database(_error=None):
    connection = g.pop('db', None)
    if connection is not None:
        connection.close()
