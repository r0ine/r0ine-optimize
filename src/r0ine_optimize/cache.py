from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

from platformdirs import user_cache_dir


def _default_db_path() -> Path:
    base = Path(user_cache_dir("r0ine-optimize", "r0ine"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "cache.sqlite3"


def _hash_key(messages: list[dict], model: str) -> str:
    payload = json.dumps({"model": model, "messages": messages}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ResponseCache:
    def __init__(self, db_path: Path | str | None = None, ttl_seconds: int = 3600) -> None:
        self.db_path = Path(db_path) if db_path else _default_db_path()
        self.ttl_seconds = ttl_seconds
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                response TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()
        self.hits = 0
        self.misses = 0

    def key_for(self, messages: list[dict], model: str) -> str:
        return _hash_key(messages, model)

    def get(self, messages: list[dict], model: str) -> str | None:
        key = self.key_for(messages, model)
        row = self._conn.execute(
            "SELECT response, created_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            self.misses += 1
            return None

        response, created_at = row
        if time.time() - created_at > self.ttl_seconds:
            self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self._conn.commit()
            self.misses += 1
            return None

        self.hits += 1
        return response

    def set(self, messages: list[dict], model: str, response: str) -> None:
        key = self.key_for(messages, model)
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, response, created_at) VALUES (?, ?, ?)",
            (key, response, time.time()),
        )
        self._conn.commit()

    def clear(self) -> int:
        cursor = self._conn.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        self._conn.execute("DELETE FROM cache")
        self._conn.commit()
        return count

    def purge_expired(self) -> int:
        now = time.time()
        cursor = self._conn.execute(
            "DELETE FROM cache WHERE ? - created_at > ?", (now, self.ttl_seconds)
        )
        self._conn.commit()
        return cursor.rowcount

    def size(self) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(LENGTH(response)), 0) FROM cache"
        ).fetchone()
        entry_count, total_bytes = row
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        return {
            "entries": entry_count,
            "response_bytes": total_bytes,
            "db_bytes": db_size,
        }

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total else 0.0,
        }

    def close(self) -> None:
        self._conn.close()
