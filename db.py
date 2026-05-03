"""SQLite Database for Research Session Tracking

연구 세션의 진행 과정(라운드별 이벤트)을 저장하여
팀원이 나중에 조회할 수 있도록 합니다.
"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "virtual_lab.db"

_conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
_conn.execute("PRAGMA journal_mode=WAL")
_conn.execute("PRAGMA foreign_keys=ON")

_conn.executescript("""
CREATE TABLE IF NOT EXISTS research_sessions (
    id              TEXT PRIMARY KEY,
    topic           TEXT NOT NULL,
    constraints     TEXT DEFAULT '',
    status          TEXT DEFAULT 'running',
    total_rounds    INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    completed_at    TEXT,
    final_report    TEXT
);

CREATE TABLE IF NOT EXISTS session_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES research_sessions(id),
    event_type      TEXT NOT NULL,
    agent           TEXT,
    agent_name      TEXT,
    round           INTEGER DEFAULT 0,
    content         TEXT,
    scores          TEXT,
    timestamp       TEXT NOT NULL,
    metadata        TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_session ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_round ON session_events(session_id, round);
""")
_conn.commit()


def create_session(topic: str, constraints: str = "") -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    _conn.execute(
        "INSERT INTO research_sessions (id, topic, constraints, status, created_at) VALUES (?, ?, ?, 'running', ?)",
        (session_id, topic, constraints, now),
    )
    _conn.commit()
    return session_id


def add_event(
    session_id: str,
    event_type: str,
    agent: str = "",
    agent_name: str = "",
    round_num: int = 0,
    content: str = "",
    scores: dict | None = None,
    metadata: dict | None = None,
) -> int:
    now = datetime.now().isoformat()
    cursor = _conn.execute(
        """INSERT INTO session_events
           (session_id, event_type, agent, agent_name, round, content, scores, timestamp, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id, event_type, agent, agent_name, round_num,
            content[:50000] if content else "",
            json.dumps(scores, ensure_ascii=False) if scores else None,
            now,
            json.dumps(metadata, ensure_ascii=False) if metadata else None,
        ),
    )
    _conn.commit()
    return cursor.lastrowid


def complete_session(session_id: str, total_rounds: int, final_report: str = "") -> None:
    now = datetime.now().isoformat()
    _conn.execute(
        "UPDATE research_sessions SET status='completed', total_rounds=?, completed_at=?, final_report=? WHERE id=?",
        (total_rounds, now, final_report, session_id),
    )
    _conn.commit()


def fail_session(session_id: str, error: str = "") -> None:
    now = datetime.now().isoformat()
    _conn.execute(
        "UPDATE research_sessions SET status='error', completed_at=? WHERE id=?",
        (now, session_id),
    )
    if error:
        add_event(session_id, "error", content=error)
    _conn.commit()


def list_sessions(limit: int = 50) -> list[dict]:
    _conn.row_factory = sqlite3.Row
    rows = _conn.execute(
        "SELECT id, topic, constraints, status, total_rounds, created_at, completed_at FROM research_sessions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    _conn.row_factory = None
    return [dict(r) for r in rows]


def get_session(session_id: str) -> dict | None:
    _conn.row_factory = sqlite3.Row
    row = _conn.execute("SELECT * FROM research_sessions WHERE id=?", (session_id,)).fetchone()
    _conn.row_factory = None
    return dict(row) if row else None


def get_session_events(session_id: str) -> list[dict]:
    _conn.row_factory = sqlite3.Row
    rows = _conn.execute(
        "SELECT * FROM session_events WHERE session_id=? ORDER BY id ASC", (session_id,),
    ).fetchall()
    _conn.row_factory = None

    events = []
    for r in rows:
        event = dict(r)
        for key in ("scores", "metadata"):
            if event.get(key):
                try:
                    event[key] = json.loads(event[key])
                except json.JSONDecodeError:
                    pass
        events.append(event)
    return events
