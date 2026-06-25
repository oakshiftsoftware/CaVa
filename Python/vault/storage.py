from . import db


def init_db(key: str | None = None):
    return db.init_db(key)


def create_case(
    title: str,
    county: str | None = None,
    suspect_name: str | None = None,
    victim_name: str | None = None,
    crime_type: str | None = None,
):
    return db.create_case(
        title,
        county=county,
        suspect_name=suspect_name,
        victim_name=victim_name,
        crime_type=crime_type,
    )


def update_case(case_id: int, **metadata):
    return db.update_case(case_id, **metadata)


def list_cases():
    return db.list_cases()


def search_cases(q: str):
    return db.search_cases(q)


def get_case(case_id: int):
    return db.get_case(case_id)


def add_note(case_id: int, summary: str, content: str):
    return db.add_note(case_id, summary, content)


def get_notes(case_id: int):
    return db.get_notes(case_id)


def update_note(note_id: int, summary: str, content: str):
    return db.update_note(note_id, summary, content)


def delete_note(note_id: int):
    return db.delete_note(note_id)


def add_file(case_id: int, filename: str, data: bytes):
    return db.add_file(case_id, filename, data)


def get_files(case_id: int):
    return db.get_files(case_id)


def delete_file(file_id: int):
    return db.delete_file(file_id)


def delete_case(case_id: int):
    return db.delete_case(case_id)


def complete_case(case_id: int):
    return db.complete_case(case_id)


def add_audit(event: str, meta: dict | None = None):
    return db.add_audit(event, meta)


def get_audit():
    return db.get_audit()


if __name__ == "__main__":
    init_db()
