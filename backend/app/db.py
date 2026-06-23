"""Job persistence. SQLite (stdlib) — no external service required.

Single-table key/value of job records as JSON. Swap this module to change
storage without touching services or routes.
"""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

from .config import DB_PATH

_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, data TEXT)")
    return c


def create_job(job_id: str, **fields) -> dict:
    record = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "stage": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    with _lock, _conn() as c:
        c.execute("INSERT OR REPLACE INTO jobs VALUES (?, ?)", (job_id, json.dumps(record)))
    return record


def update_job(job_id: str, **fields) -> Optional[dict]:
    with _lock, _conn() as c:
        row = c.execute("SELECT data FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        record = json.loads(row[0])
        record.update(fields)
        c.execute("UPDATE jobs SET data = ? WHERE id = ?", (json.dumps(record), job_id))
    return record


def get_job(job_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute("SELECT data FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return json.loads(row[0]) if row else None


def list_jobs(limit: int = 100) -> list:
    with _conn() as c:
        rows = c.execute("SELECT data FROM jobs").fetchall()
    jobs = [json.loads(r[0]) for r in rows]
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return jobs[:limit]
