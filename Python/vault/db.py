import os
import json
import time
import sqlite3
from typing import List, Optional

try:
    from pysqlcipher3 import dbapi2 as sqlcipher

    _HAS_SQLCIPHER = True
except Exception:
    sqlcipher = None
    _HAS_SQLCIPHER = False


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "cava.db")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _connect(key: Optional[str] = None):
    _ensure_data_dir()
    if _HAS_SQLCIPHER and sqlcipher is not None:
        conn = sqlcipher.connect(DB_FILE)
        if key:
            conn.execute(f"PRAGMA key = \"x'{key}'\";")
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        return conn


def init_db(key: Optional[str] = None):
    conn = _connect(key)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY,
            ref TEXT UNIQUE,
            title TEXT,
            status TEXT,
            created_at INTEGER,
            completed_at INTEGER
        );
        """)

    cur.execute("PRAGMA table_info(cases);")
    cols = [r[1] for r in cur.fetchall()]
    extras = {
        "county": "TEXT",
        "suspect_name": "TEXT",
        "victim_name": "TEXT",
        "crime_type": "TEXT",
    }
    for col, typ in extras.items():
        if col not in cols:
            try:
                cur.execute(f"ALTER TABLE cases ADD COLUMN {col} {typ};")
            except Exception:
                pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            case_id INTEGER,
            summary TEXT,
            content TEXT,
            created_at INTEGER,
            FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
        );
        """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            case_id INTEGER,
            filename TEXT,
            data BLOB,
            created_at INTEGER,
            FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
        );
        """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY,
            ts INTEGER,
            event TEXT,
            meta TEXT
        );
        """)

    conn.commit()
    return conn


def _gen_ref() -> str:
    return f"CASE-{int(time.time())}-{os.urandom(3).hex()}"


def create_case(
    title: str,
    county: Optional[str] = None,
    suspect_name: Optional[str] = None,
    victim_name: Optional[str] = None,
    crime_type: Optional[str] = None,
) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ref = _gen_ref()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO cases (ref, title, status, created_at, county, suspect_name, victim_name, crime_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (ref, title, "open", ts, county, suspect_name, victim_name, crime_type),
    )
    conn.commit()
    cid = cur.lastrowid
    return get_case(cid)


def list_cases() -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ref, title, status, created_at, completed_at, county, suspect_name, victim_name, crime_type FROM cases ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    return [
        dict(
            id=r[0],
            ref=r[1],
            title=r[2],
            status=r[3],
            created_at=r[4],
            completed_at=r[5],
            county=r[6],
            suspect_name=r[7],
            victim_name=r[8],
            crime_type=r[9],
        )
        for r in rows
    ]


def search_cases(query: str) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    q = f"%{query}%"
    cur.execute(
        "SELECT id, ref, title, status, created_at, completed_at, county, suspect_name, victim_name, crime_type FROM cases WHERE title LIKE ? OR ref LIKE ? ORDER BY created_at DESC",
        (q, q),
    )
    rows = cur.fetchall()
    return [
        dict(
            id=r[0],
            ref=r[1],
            title=r[2],
            status=r[3],
            created_at=r[4],
            completed_at=r[5],
            county=r[6],
            suspect_name=r[7],
            victim_name=r[8],
            crime_type=r[9],
        )
        for r in rows
    ]


def get_case(case_id: int) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ref, title, status, created_at, completed_at, county, suspect_name, victim_name, crime_type FROM cases WHERE id = ?",
        (case_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return dict(
        id=r[0],
        ref=r[1],
        title=r[2],
        status=r[3],
        created_at=r[4],
        completed_at=r[5],
        county=r[6],
        suspect_name=r[7],
        victim_name=r[8],
        crime_type=r[9],
    )


def update_case(case_id: int, **metadata) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    allowed = ["title", "status", "county", "suspect_name", "victim_name", "crime_type"]
    fields = []
    values = []
    for k, v in metadata.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return get_case(case_id)
    values.append(case_id)
    cur.execute(f"UPDATE cases SET {', '.join(fields)} WHERE id = ?", tuple(values))
    conn.commit()
    add_audit(f"case_updated:{case_id}", {"updated": list(metadata.keys())})
    return get_case(case_id)


def add_note(case_id: int, summary: str, content: str) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO notes (case_id, summary, content, created_at) VALUES (?, ?, ?, ?)",
        (case_id, summary, content, ts),
    )
    conn.commit()
    nid = cur.lastrowid
    add_audit(f"note_added:{nid}", {"case": case_id})
    return get_note(nid)


def get_note(note_id: int) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, case_id, summary, content, created_at FROM notes WHERE id = ?",
        (note_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return dict(id=r[0], case_id=r[1], summary=r[2], content=r[3], created_at=r[4])


def update_note(note_id: int, summary: str, content: str) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE notes SET summary = ?, content = ? WHERE id = ?",
        (summary, content, note_id),
    )
    conn.commit()
    add_audit(f"note_updated:{note_id}", {"note": note_id})
    return get_note(note_id)


def get_notes(case_id: int) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, summary, content, created_at FROM notes WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,),
    )
    rows = cur.fetchall()
    return [dict(id=r[0], summary=r[1], content=r[2], created_at=r[3]) for r in rows]


def delete_note(note_id: int):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    add_audit(f"note_deleted:{note_id}")


def add_file(case_id: int, filename: str, data: bytes) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO files (case_id, filename, data, created_at) VALUES (?, ?, ?, ?)",
        (case_id, filename, data, ts),
    )
    conn.commit()
    fid = cur.lastrowid
    add_audit(f"file_added:{fid}", {"case": case_id, "filename": filename})
    return get_file(fid)


def get_file(file_id: int) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, case_id, filename, data, created_at FROM files WHERE id = ?",
        (file_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return dict(id=r[0], case_id=r[1], filename=r[2], data=r[3], created_at=r[4])


def get_files(case_id: int) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, created_at FROM files WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,),
    )
    rows = cur.fetchall()
    return [dict(id=r[0], filename=r[1], created_at=r[2]) for r in rows]


def delete_file(file_id: int):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    add_audit(f"file_deleted:{file_id}")


def delete_case(case_id: int):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    conn.commit()
    add_audit(f"case_deleted:{case_id}")


def complete_case(case_id: int):
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "UPDATE cases SET status = ?, completed_at = ? WHERE id = ?",
        ("closed", ts, case_id),
    )
    conn.commit()
    add_audit(f"case_completed:{case_id}")


def add_audit(event: str, meta: Optional[dict] = None):
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO audit (ts, event, meta) VALUES (?, ?, ?)",
        (ts, event, json.dumps(meta or {})),
    )
    conn.commit()


def get_audit():
    conn = init_db()
    cur = conn.cursor()
    cur.execute("SELECT id, ts, event, meta FROM audit ORDER BY ts DESC")
    rows = cur.fetchall()
    return [
        dict(id=r[0], ts=r[1], event=r[2], meta=json.loads(r[3] or "{}")) for r in rows
    ]


if __name__ == "__main__":
    init_db()
