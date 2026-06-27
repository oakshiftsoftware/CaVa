from . import db


def init_db(key: str | None = None):
    return db.init_db(key)


def create_case(
    title: str,
    location: str | None = None,
    suspect_name: str | None = None,
    victim_name: str | None = None,
    category: str | None = None,
    crime_type: str | None = None,
):
    return db.create_case(
        title,
        location=location,
        suspect_name=suspect_name,
        victim_name=victim_name,
        category=category,
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


def link_case(case_id: int, related_case_id: int):
    return db.link_case(case_id, related_case_id)


def unlink_case(case_id: int, related_case_id: int):
    return db.unlink_case(case_id, related_case_id)


def get_related_cases(case_id: int):
    return db.get_related_cases(case_id)


def create_case_profile(
    case_id: int,
    name: str,
    association_type: str,
    role: str | None = None,
    contact_info: str | None = None,
    description: str | None = None,
):
    return db.create_case_profile(
        case_id,
        name,
        association_type,
        role=role,
        contact_info=contact_info,
        description=description,
    )


def update_case_profile(profile_id: int, **metadata):
    return db.update_case_profile(profile_id, **metadata)


def delete_case_profile(profile_id: int):
    return db.delete_case_profile(profile_id)


def get_case_profiles(case_id: int):
    return db.get_case_profiles(case_id)


def get_case_profile(profile_id: int):
    return db.get_case_profile(profile_id)


def start_research_session(case_id: int, name: str | None = None):
    return db.start_research_session(case_id, name)


def end_research_session(session_id: int):
    return db.end_research_session(session_id)


def add_research_action(session_id: int, event: str, meta: dict | None = None):
    return db.add_research_action(session_id, event, meta)


def get_research_sessions(case_id: int):
    return db.get_research_sessions(case_id)


def get_research_actions(session_id: int):
    return db.get_research_actions(session_id)


def add_audit(event: str, meta: dict | None = None):
    return db.add_audit(event, meta)


def get_audit():
    return db.get_audit()


if __name__ == "__main__":
    init_db()
