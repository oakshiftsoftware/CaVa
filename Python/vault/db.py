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

from . import crypto

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "cava.db")
_DB_KEY_HEX: Optional[str] = None


def set_db_key(key: Optional[str]) -> None:
    global _DB_KEY_HEX
    _DB_KEY_HEX = key


def _encrypt_if_enabled(data: bytes) -> bytes:
    if _DB_KEY_HEX:
        return crypto.encrypt_bytes(data, _DB_KEY_HEX)
    return data


def _decrypt_if_enabled(data: bytes) -> bytes:
    if _DB_KEY_HEX and data is not None:
        return crypto.decrypt_bytes(data, _DB_KEY_HEX)
    return data


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
    set_db_key(key)
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

    if "crime_type" in cols and "category" not in cols:
        try:
            cur.execute("ALTER TABLE cases RENAME COLUMN crime_type TO category;")
        except sqlite3.OperationalError:
            cur.execute("ALTER TABLE cases ADD COLUMN category TEXT;")
            cur.execute(
                "UPDATE cases SET category = crime_type WHERE category IS NULL;"
            )

    extras = {
        "location": "TEXT",
        "suspect_name": "TEXT",
        "victim_name": "TEXT",
        "category": "TEXT",
        "updated_at": "INTEGER",
    }
    for col, typ in extras.items():
        if col not in cols and not (col == "category" and "crime_type" in cols):
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS case_links (
            id INTEGER PRIMARY KEY,
            case_id INTEGER,
            related_case_id INTEGER,
            created_at INTEGER,
            FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE,
            FOREIGN KEY(related_case_id) REFERENCES cases(id) ON DELETE CASCADE
        );
        """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_sessions (
            id INTEGER PRIMARY KEY,
            case_id INTEGER,
            name TEXT,
            started_at INTEGER,
            ended_at INTEGER,
            FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
        );
        """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_actions (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            ts INTEGER,
            event TEXT,
            meta TEXT,
            FOREIGN KEY(session_id) REFERENCES research_sessions(id) ON DELETE CASCADE
        );
        """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS case_profiles (
            id INTEGER PRIMARY KEY,
            case_id INTEGER,
            name TEXT,
            association_type TEXT,
            role TEXT,
            contact_info TEXT,
            description TEXT,
            created_at INTEGER,
            FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
        );
        """)

    conn.commit()
    return conn


def _gen_ref() -> str:
    return f"CASE-{int(time.time())}-{os.urandom(3).hex()}"


def create_case(
    title: str,
    location: Optional[str] = None,
    suspect_name: Optional[str] = None,
    victim_name: Optional[str] = None,
    category: Optional[str] = None,
    crime_type: Optional[str] = None,
) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ref = _gen_ref()
    ts = int(time.time())
    category_value = category if category is not None else crime_type
    cur.execute(
        "INSERT INTO cases (ref, title, status, created_at, updated_at, location, suspect_name, victim_name, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (ref, title, "open", ts, ts, location, suspect_name, victim_name, category_value),
    )
    conn.commit()
    cid = cur.lastrowid
    return get_case(cid)


def list_cases() -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ref, title, status, created_at, completed_at, updated_at, location, suspect_name, victim_name, category FROM cases ORDER BY created_at DESC"
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
            updated_at=r[6],
            location=r[7],
            suspect_name=r[8],
            victim_name=r[9],
            category=r[10],
        )
        for r in rows
    ]


def search_cases(query: str) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    q = f"%{query}%"
    cur.execute(
        "SELECT DISTINCT c.id, c.ref, c.title, c.status, c.created_at, c.completed_at, c.updated_at, c.location, c.suspect_name, c.victim_name, c.category "
        "FROM cases c "
        "LEFT JOIN notes n ON n.case_id = c.id "
        "LEFT JOIN case_profiles p ON p.case_id = c.id "
        "WHERE c.title LIKE ? OR c.ref LIKE ? OR n.summary LIKE ? OR n.content LIKE ? OR p.name LIKE ? OR p.association_type LIKE ? "
        "ORDER BY c.created_at DESC",
        (q, q, q, q, q, q),
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
            updated_at=r[6],
            location=r[7],
            suspect_name=r[8],
            victim_name=r[9],
            category=r[10],
        )
        for r in rows
    ]


def get_case(case_id: int) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ref, title, status, created_at, completed_at, updated_at, location, suspect_name, victim_name, category FROM cases WHERE id = ?",
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
        updated_at=r[6],
        location=r[7],
        suspect_name=r[8],
        victim_name=r[9],
        category=r[10],
    )


def update_case(case_id: int, **metadata) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    allowed = ["title", "status", "location", "suspect_name", "victim_name", "category"]
    fields = []
    values = []
    for k, v in metadata.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return get_case(case_id)
    ts = int(time.time())
    fields.append("updated_at = ?")
    values.append(ts)
    values.append(case_id)
    cur.execute(f"UPDATE cases SET {', '.join(fields)} WHERE id = ?", tuple(values))
    conn.commit()
    add_audit(f"case_updated:{case_id}", {"updated": list(metadata.keys())})
    return get_case(case_id)


def add_note(case_id: int, summary: str, content: str) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    encrypted_summary = _encrypt_if_enabled(summary.encode("utf-8"))
    encrypted_content = _encrypt_if_enabled(content.encode("utf-8"))
    cur.execute(
        "INSERT INTO notes (case_id, summary, content, created_at) VALUES (?, ?, ?, ?)",
        (case_id, encrypted_summary, encrypted_content, ts),
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
    return dict(
        id=r[0],
        case_id=r[1],
        summary=_decrypt_if_enabled(r[2]).decode("utf-8") if r[2] is not None else "",
        content=_decrypt_if_enabled(r[3]).decode("utf-8") if r[3] is not None else "",
        created_at=r[4],
    )


def update_note(note_id: int, summary: str, content: str) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    encrypted_summary = _encrypt_if_enabled(summary.encode("utf-8"))
    encrypted_content = _encrypt_if_enabled(content.encode("utf-8"))
    cur.execute(
        "UPDATE notes SET summary = ?, content = ? WHERE id = ?",
        (encrypted_summary, encrypted_content, note_id),
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
    return [
        dict(
            id=r[0],
            summary=(
                _decrypt_if_enabled(r[1]).decode("utf-8") if r[1] is not None else ""
            ),
            content=(
                _decrypt_if_enabled(r[2]).decode("utf-8") if r[2] is not None else ""
            ),
            created_at=r[3],
        )
        for r in rows
    ]


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
    encrypted_data = _encrypt_if_enabled(data)
    cur.execute(
        "INSERT INTO files (case_id, filename, data, created_at) VALUES (?, ?, ?, ?)",
        (case_id, filename, encrypted_data, ts),
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
    return dict(
        id=r[0],
        case_id=r[1],
        filename=r[2],
        data=_decrypt_if_enabled(r[3]) if r[3] is not None else b"",
        created_at=r[4],
    )


def get_files(case_id: int) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, data, created_at FROM files WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,),
    )
    rows = cur.fetchall()
    return [
        dict(
            id=r[0],
            filename=r[1],
            data=_decrypt_if_enabled(r[2]) if r[2] is not None else b"",
            created_at=r[3],
        )
        for r in rows
    ]


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
        "UPDATE cases SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
        ("closed", ts, ts, case_id),
    )
    conn.commit()
    add_audit(f"case_completed:{case_id}")


def link_case(case_id: int, related_case_id: int) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO case_links (case_id, related_case_id, created_at) VALUES (?, ?, ?)",
        (case_id, related_case_id, ts),
    )
    conn.commit()
    return get_related_cases(case_id)


def unlink_case(case_id: int, related_case_id: int):
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM case_links WHERE case_id = ? AND related_case_id = ?",
        (case_id, related_case_id),
    )
    conn.commit()
    add_audit(f"case_unlinked:{case_id}", {"related_case": related_case_id})


def get_related_cases(case_id: int) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT c.id, c.ref, c.title, c.status, c.created_at, c.completed_at, c.updated_at, c.location, c.suspect_name, c.victim_name, c.category "
        "FROM cases c "
        "JOIN case_links cl ON cl.related_case_id = c.id "
        "WHERE cl.case_id = ? ORDER BY cl.created_at DESC",
        (case_id,),
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
            updated_at=r[6],
            location=r[7],
            suspect_name=r[8],
            victim_name=r[9],
            category=r[10],
        )
        for r in rows
    ]


def get_research_session(session_id: int) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, case_id, name, started_at, ended_at FROM research_sessions WHERE id = ?",
        (session_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return dict(
        id=r[0],
        case_id=r[1],
        name=r[2],
        started_at=r[3],
        ended_at=r[4],
    )


def get_case_profile(profile_id: int) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, case_id, name, association_type, role, contact_info, description, created_at FROM case_profiles WHERE id = ?",
        (profile_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return dict(
        id=r[0],
        case_id=r[1],
        name=r[2],
        association_type=r[3],
        role=r[4],
        contact_info=r[5],
        description=r[6],
        created_at=r[7],
    )


def create_case_profile(
    case_id: int,
    name: str,
    association_type: str,
    role: Optional[str] = None,
    contact_info: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO case_profiles (case_id, name, association_type, role, contact_info, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (case_id, name, association_type, role, contact_info, description, ts),
    )
    conn.commit()
    pid = cur.lastrowid
    add_audit(
        f"profile_added:{pid}",
        {"case": case_id, "name": name, "association_type": association_type},
    )
    return get_case_profile(pid)


def update_case_profile(profile_id: int, **metadata) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    allowed = ["name", "association_type", "role", "contact_info", "description"]
    fields = []
    values = []
    for k, v in metadata.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return get_case_profile(profile_id)
    values.append(profile_id)
    cur.execute(
        f"UPDATE case_profiles SET {', '.join(fields)} WHERE id = ?",
        tuple(values),
    )
    conn.commit()
    updated = get_case_profile(profile_id)
    if updated:
        add_audit(
            f"profile_updated:{profile_id}",
            {"case": updated.get("case_id"), "updated": list(metadata.keys())},
        )
    return updated


def delete_case_profile(profile_id: int):
    profile = get_case_profile(profile_id)
    conn = init_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM case_profiles WHERE id = ?", (profile_id,))
    conn.commit()
    if profile:
        add_audit(
            f"profile_deleted:{profile_id}",
            {"case": profile.get("case_id"), "name": profile.get("name")},
        )


def get_case_profiles(case_id: int) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, association_type, role, contact_info, description, created_at FROM case_profiles WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,),
    )
    rows = cur.fetchall()
    return [
        dict(
            id=r[0],
            name=r[1],
            association_type=r[2],
            role=r[3],
            contact_info=r[4],
            description=r[5],
            created_at=r[6],
        )
        for r in rows
    ]


def start_research_session(case_id: int, name: Optional[str] = None) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO research_sessions (case_id, name, started_at) VALUES (?, ?, ?)",
        (case_id, name or f"Session {ts}", ts),
    )
    conn.commit()
    sid = cur.lastrowid
    add_audit(f"research_session_started:{sid}", {"case": case_id, "name": name})
    return get_research_session(sid)


def end_research_session(session_id: int) -> dict:
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "UPDATE research_sessions SET ended_at = ? WHERE id = ?",
        (ts, session_id),
    )
    conn.commit()
    session = get_research_session(session_id)
    if session:
        add_audit(
            f"research_session_ended:{session_id}",
            {"case": session.get("case_id"), "name": session.get("name")},
        )
        try:
            notes = get_research_actions(session_id)
            summaries = [
                f"{a.get('ts')}: {a.get('event')}"
                for a in notes[:10]
            ]
            content = (
                "Research session ended. Recorded actions:\n"
                + "\n".join(summaries)
            )
            add_note(session.get("case_id"), f"Research Session: {session.get('name')}", content)
        except Exception:
            pass
    return session


def add_research_action(session_id: int, event: str, meta: Optional[dict] = None):
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    cur.execute(
        "INSERT INTO research_actions (session_id, ts, event, meta) VALUES (?, ?, ?, ?)",
        (session_id, ts, event, json.dumps(meta or {})),
    )
    conn.commit()
    add_audit(f"research_action:{session_id}", {"event": event, "session": session_id})
    return get_research_action(cur.lastrowid)


def get_research_action(action_id: int) -> Optional[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, session_id, ts, event, meta FROM research_actions WHERE id = ?",
        (action_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return dict(
        id=r[0],
        session_id=r[1],
        ts=r[2],
        event=r[3],
        meta=json.loads(r[4] or "{}"),
    )


def get_research_sessions(case_id: int) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, case_id, name, started_at, ended_at FROM research_sessions WHERE case_id = ? ORDER BY started_at DESC",
        (case_id,),
    )
    rows = cur.fetchall()
    return [
        dict(
            id=r[0],
            case_id=r[1],
            name=r[2],
            started_at=r[3],
            ended_at=r[4],
        )
        for r in rows
    ]


def get_research_actions(session_id: int) -> List[dict]:
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, session_id, ts, event, meta FROM research_actions WHERE session_id = ? ORDER BY ts ASC",
        (session_id,),
    )
    rows = cur.fetchall()
    return [
        dict(
            id=r[0],
            session_id=r[1],
            ts=r[2],
            event=r[3],
            meta=json.loads(r[4] or "{}"),
        )
        for r in rows
    ]


def add_audit(event: str, meta: Optional[dict] = None):
    conn = init_db()
    cur = conn.cursor()
    ts = int(time.time())
    encrypted_event = _encrypt_if_enabled(event.encode("utf-8"))
    if isinstance(encrypted_event, bytes):
        encrypted_event = encrypted_event.decode("utf-8")
    encrypted_meta = _encrypt_if_enabled(json.dumps(meta or {}).encode("utf-8"))
    if isinstance(encrypted_meta, bytes):
        encrypted_meta = encrypted_meta.decode("utf-8")
    cur.execute(
        "INSERT INTO audit (ts, event, meta) VALUES (?, ?, ?)",
        (ts, encrypted_event, encrypted_meta),
    )
    conn.commit()


def get_audit():
    conn = init_db()
    cur = conn.cursor()
    cur.execute("SELECT id, ts, event, meta FROM audit ORDER BY ts DESC")
    rows = cur.fetchall()
    results = []
    for r in rows:
        event_text = r[2]
        meta_text = r[3]
        try:
            if event_text is not None:
                event_text = _decrypt_if_enabled(event_text.encode("utf-8")).decode("utf-8")
        except Exception:
            pass
        try:
            if meta_text is not None:
                meta_text = _decrypt_if_enabled(meta_text.encode("utf-8")).decode("utf-8")
        except Exception:
            pass
        results.append(
            dict(
                id=r[0],
                ts=r[1],
                event=event_text,
                meta=json.loads(meta_text or "{}"),
            )
        )
    return results


if __name__ == "__main__":
    init_db()
