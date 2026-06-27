from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QLineEdit,
    QInputDialog,
    QDialog,
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import Signal, Qt
from datetime import datetime
from ui.note_editor import NoteEditorDialog
from ui.case_profiles import ProfileListDialog


class EditorWidget(QWidget):
    saved = Signal()
    cancelled = Signal()
    case_deleted = Signal(int)

    def __init__(self, storage, config, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.config = config
        self.current_case = None

        layout = QVBoxLayout(self)

        self.title = QLabel("Editor")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.meta_form = QFormLayout()
        self.case_title_input = QLineEdit()
        self.location_input = QLineEdit()
        self.suspect_input = QLineEdit()
        self.victim_input = QLineEdit()
        self.category_input = QLineEdit()
        self.meta_form.addRow("Case Title", self.case_title_input)
        self.meta_form.addRow("Location", self.location_input)
        self.meta_form.addRow("Suspect", self.suspect_input)
        self.meta_form.addRow("Victim", self.victim_input)
        self.meta_form.addRow("Category", self.category_input)

        lists_layout = QHBoxLayout()

        notes_panel = QVBoxLayout()
        notes_label = QLabel("Notes")
        notes_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.notes_list = QListWidget()
        notes_panel.addWidget(notes_label)
        notes_panel.addWidget(self.notes_list)
        notes_panel.addStretch(1)

        preview_panel = QVBoxLayout()
        preview_label = QLabel("Note Preview")
        preview_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        preview_panel.addWidget(preview_label)
        preview_panel.addWidget(self.text)

        column1 = QVBoxLayout()
        column1.addLayout(notes_panel)
        column1.addLayout(preview_panel)

        attachments_panel = QVBoxLayout()
        attachments_label = QLabel("Attachments")
        attachments_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.files_list = QListWidget()
        attachments_panel.addWidget(attachments_label)
        attachments_panel.addWidget(self.files_list)
        attachments_panel.addStretch(1)

        profiles_panel = QVBoxLayout()
        profiles_label = QLabel("Person Profiles")
        profiles_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.profiles_list = QListWidget()
        profiles_panel.addWidget(profiles_label)
        profiles_panel.addWidget(self.profiles_list)
        profiles_panel.addStretch(1)

        column2 = QVBoxLayout()
        column2.addLayout(attachments_panel)
        column2.addLayout(profiles_panel)

        related_panel = QVBoxLayout()
        related_label = QLabel("Related Cases")
        related_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.related_list = QListWidget()
        related_panel.addWidget(related_label)
        related_panel.addWidget(self.related_list)
        related_panel.addStretch(1)

        sessions_panel = QVBoxLayout()
        sessions_label = QLabel("Research Sessions")
        sessions_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.sessions_list = QListWidget()
        sessions_panel.addWidget(sessions_label)
        sessions_panel.addWidget(self.sessions_list)
        sessions_panel.addStretch(1)

        column3 = QVBoxLayout()
        column3.addLayout(related_panel)
        column3.addLayout(sessions_panel)

        lists_layout.addLayout(column1)
        lists_layout.addLayout(column2)
        lists_layout.addLayout(column3)
        lists_layout.setStretch(0, 1)
        lists_layout.setStretch(1, 1)
        lists_layout.setStretch(2, 1)

        btn_notes = QPushButton("Notes")
        btn_notes.clicked.connect(self.show_notes_dialog)

        btn_attachments = QPushButton("Attachments")
        btn_attachments.clicked.connect(self.show_attachments_dialog)

        btn_case_actions = QPushButton("Case Actions")
        btn_case_actions.clicked.connect(self.show_case_actions_dialog)

        btn_case_links = QPushButton("Related Cases")
        btn_case_links.clicked.connect(self.show_case_link_dialog)

        btn_profiles = QPushButton("Person Profiles")
        btn_profiles.clicked.connect(self.show_profiles_dialog)

        btn_session = QPushButton("Session Control")
        btn_session.clicked.connect(self.show_session_dialog)

        btn_back = QPushButton("Back")
        btn_back.clicked.connect(lambda: self.cancelled.emit())

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_notes)
        btn_layout.addWidget(btn_attachments)
        btn_layout.addWidget(btn_case_actions)
        btn_layout.addWidget(btn_case_links)
        btn_layout.addWidget(btn_profiles)
        btn_layout.addWidget(btn_session)
        btn_layout.addWidget(btn_back)

        layout.addWidget(self.title)
        layout.addLayout(self.meta_form)
        layout.addLayout(lists_layout)
        layout.addLayout(btn_layout)

        self.notes_list.currentItemChanged.connect(self.preview_selected_note)
        self.sessions_list.currentItemChanged.connect(self.preview_selected_session)

    def load_case(self, case: dict | None):
        self.current_case = case
        if not case:
            self.title.setText("No case selected")
            self.case_title_input.clear()
            self.location_input.clear()
            self.suspect_input.clear()
            self.victim_input.clear()
            self.category_input.clear()
            self.notes_list.clear()
            self.files_list.clear()
            self.text.clear()
            return

        self.title.setText(f"Case: {case.get('ref')} — {case.get('title')}")
        self.case_title_input.setText(case.get("title") or "")
        self.location_input.setText(case.get("location") or "")
        self.suspect_input.setText(case.get("suspect_name") or "")
        self.victim_input.setText(case.get("victim_name") or "")
        self.category_input.setText(case.get("category") or "")
        self.current_session = None
        self.refresh_lists()
        self.load_research_sessions()

    def refresh_lists(self):
        if not self.current_case:
            return
        cid = self.current_case.get("id")
        self.notes_list.clear()
        notes = self.storage.get_notes(cid)
        for n in notes:
            item = QListWidgetItem(f"{n.get('id')} — {n.get('summary')}")
            item.setData(Qt.UserRole, n)
            self.notes_list.addItem(item)

        self.files_list.clear()
        files = self.storage.get_files(cid)
        for f in files:
            item = QListWidgetItem(f"{f.get('id')} — {f.get('filename')}")
            item.setData(Qt.UserRole, f)
            self.files_list.addItem(item)

        self.load_profiles()
        self.load_research_sessions()
        self.load_related_cases()
        self.text.clear()

    def load_profiles(self):
        if not self.current_case:
            return
        cid = self.current_case.get("id")
        self.profiles_list.clear()
        profiles = self.storage.get_case_profiles(cid)
        for p in profiles:
            item = QListWidgetItem(
                f"{p.get('id')} — {p.get('name')} ({p.get('association_type', 'Unknown')})"
            )
            item.setData(Qt.UserRole, p)
            self.profiles_list.addItem(item)

    def refresh_current_case(self):
        if not self.current_case:
            return
        case_id = self.current_case.get("id")
        self.current_case = self.storage.get_case(case_id)
        if not self.current_case:
            return
        self.title.setText(
            f"Case: {self.current_case.get('ref')} — {self.current_case.get('title')}"
        )
        self.case_title_input.setText(self.current_case.get("title") or "")
        self.location_input.setText(self.current_case.get("location") or "")
        self.suspect_input.setText(self.current_case.get("suspect_name") or "")
        self.victim_input.setText(self.current_case.get("victim_name") or "")
        self.category_input.setText(self.current_case.get("category") or "")
        self.refresh_lists()

    def open_new_note(self):
        if not self.current_case:
            QMessageBox.warning(self, "New Note", "No case selected")
            return
        dlg = NoteEditorDialog(self.storage, self.current_case.get("id"), None, self)
        dlg.saved.connect(self._on_note_saved)
        if dlg.exec():
            self.refresh_lists()
            self.saved.emit()

    def edit_selected_note(self):
        item = self.notes_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Edit Note", "Select a note first")
            return
        note = item.data(Qt.UserRole)
        dlg = NoteEditorDialog(self.storage, self.current_case.get("id"), note, self)
        dlg.saved.connect(self._on_note_saved)
        if dlg.exec():
            self.refresh_lists()
            self.saved.emit()

    def show_notes_dialog(self):
        if not self.current_case:
            QMessageBox.warning(self, "Notes", "No case selected")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Notes")
        layout = QVBoxLayout(dlg)

        notes_list = QListWidget()
        layout.addWidget(notes_list)

        note_preview = QTextEdit()
        note_preview.setReadOnly(True)
        note_preview.setMinimumHeight(150)
        layout.addWidget(note_preview)

        def refresh_notes():
            notes_list.clear()
            for n in self.storage.get_notes(self.current_case.get("id")):
                item = QListWidgetItem(f"{n.get('id')} — {n.get('summary')}")
                item.setData(Qt.UserRole, n)
                notes_list.addItem(item)
            if notes_list.count() > 0:
                notes_list.setCurrentRow(0)

        def preview_note(item):
            if not item:
                note_preview.clear()
                return
            note = item.data(Qt.UserRole)
            note_preview.setPlainText(note.get("content", ""))

        notes_list.currentItemChanged.connect(lambda current, _: preview_note(current))

        btn_new = QPushButton("New Note")
        btn_edit = QPushButton("Edit Note")
        btn_delete = QPushButton("Delete Note")
        btn_close = QPushButton("Close")

        def handle_new():
            dlg2 = NoteEditorDialog(self.storage, self.current_case.get("id"), None, self)
            dlg2.saved.connect(lambda _: [refresh_notes(), self.refresh_current_case()])
            if dlg2.exec():
                refresh_notes()
                self.refresh_current_case()

        def handle_edit():
            item = notes_list.currentItem()
            if not item:
                QMessageBox.warning(dlg, "Edit Note", "Select a note first")
                return
            note = item.data(Qt.UserRole)
            dlg2 = NoteEditorDialog(self.storage, self.current_case.get("id"), note, self)
            dlg2.saved.connect(lambda _: [refresh_notes(), self.refresh_current_case()])
            if dlg2.exec():
                refresh_notes()
                self.refresh_current_case()

        def handle_delete():
            item = notes_list.currentItem()
            if not item:
                QMessageBox.warning(dlg, "Delete Note", "Select a note first")
                return
            note = item.data(Qt.UserRole)
            self.storage.delete_note(note.get("id"))
            self.record_research_action("note_deleted", {"note_id": note.get("id")})
            refresh_notes()
            self.refresh_current_case()
            note_preview.clear()

        btn_new.clicked.connect(handle_new)
        btn_edit.clicked.connect(handle_edit)
        btn_delete.clicked.connect(handle_delete)
        btn_close.clicked.connect(dlg.accept)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        refresh_notes()
        dlg.exec()

    def show_attachments_dialog(self):
        if not self.current_case:
            QMessageBox.warning(self, "Attachments", "No case selected")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Attachments")
        layout = QVBoxLayout(dlg)

        files_list = QListWidget()
        layout.addWidget(files_list)

        file_preview = QTextEdit()
        file_preview.setReadOnly(True)
        file_preview.setMinimumHeight(120)
        layout.addWidget(file_preview)

        def refresh_files():
            files_list.clear()
            for f in self.storage.get_files(self.current_case.get("id")):
                item = QListWidgetItem(f"{f.get('id')} — {f.get('filename')}")
                item.setData(Qt.UserRole, f)
                files_list.addItem(item)
            if files_list.count() > 0:
                files_list.setCurrentRow(0)

        def preview_file(item):
            if not item:
                file_preview.clear()
                return
            f = item.data(Qt.UserRole)
            file_preview.setPlainText(f"Filename: {f.get('filename')}\nSize: {len(f.get('data') or b'')} bytes")

        files_list.currentItemChanged.connect(lambda current, _: preview_file(current))

        def handle_add():
            path, _ = QFileDialog.getOpenFileName(self, "Select file to attach")
            if not path:
                return
            try:
                with open(path, "rb") as fh:
                    data = fh.read()
                filename = path.split("/")[-1].split("\\")[-1]
                self.storage.add_file(self.current_case.get("id"), filename, data)
                refresh_files()
                self.refresh_current_case()
            except Exception as e:
                QMessageBox.critical(dlg, "Error", f"Failed to add file: {e}")

        def handle_delete():
            item = files_list.currentItem()
            if not item:
                QMessageBox.warning(dlg, "Delete File", "Select a file first")
                return
            f = item.data(Qt.UserRole)
            self.storage.delete_file(f.get("id"))
            self.record_research_action("file_deleted", {"file_id": f.get("id"), "filename": f.get("filename")})
            refresh_files()
            self.refresh_current_case()
            file_preview.clear()

        btn_add = QPushButton("Add File")
        btn_delete = QPushButton("Delete File")
        btn_close = QPushButton("Close")
        btn_add.clicked.connect(handle_add)
        btn_delete.clicked.connect(handle_delete)
        btn_close.clicked.connect(dlg.accept)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        refresh_files()
        dlg.exec()

    def show_case_actions_dialog(self):
        if not self.current_case:
            QMessageBox.warning(self, "Case Actions", "No case selected")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Case Actions")
        layout = QVBoxLayout(dlg)

        btn_save = QPushButton("Save Metadata")
        btn_export = QPushButton("Export Case PDF")
        btn_delete = QPushButton("Delete Case")
        btn_close = QPushButton("Close")

        def handle_save():
            self.save_metadata()
            self.refresh_current_case()
            dlg.accept()

        def handle_export():
            if self.export_case_pdf():
                self.refresh_current_case()
                dlg.accept()

        def handle_delete():
            answer = QMessageBox.question(
                dlg,
                "Delete Case",
                f"Delete case {self.current_case.get('ref')}? This is irreversible.",
            )
            if answer == QMessageBox.Yes:
                self.storage.delete_case(self.current_case.get('id'))
                self.case_deleted.emit(self.current_case.get('id'))
                dlg.accept()

        btn_save.clicked.connect(handle_save)
        btn_export.clicked.connect(handle_export)
        btn_delete.clicked.connect(handle_delete)
        btn_close.clicked.connect(dlg.accept)

        layout.addWidget(btn_save)
        layout.addWidget(btn_export)
        layout.addWidget(btn_delete)
        layout.addStretch(1)
        layout.addWidget(btn_close)

        dlg.exec()

    def add_file(self):
        if not self.current_case:
            QMessageBox.warning(self, "Add File", "No case selected")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Select file to attach")
        if not path:
            return
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            filename = path.split("/")[-1].split("\\")[-1]
            self.storage.add_file(self.current_case.get("id"), filename, data)
            self.refresh_lists()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add file: {e}")

    def delete_selected_note(self):
        item = self.notes_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Delete Note", "Select a note first")
            return
        note = item.data(Qt.UserRole)
        self.storage.delete_note(note.get("id"))
        self.record_research_action("note_deleted", {"note_id": note.get("id")})
        self.refresh_lists()
        self.text.clear()

    def preview_selected_note(self, current, previous=None):
        if not current:
            self.text.clear()
            return
        note = current.data(Qt.UserRole)
        self.text.setPlainText(note.get("content", ""))

    def delete_selected_file(self):
        item = self.files_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Delete File", "Select a file first")
            return
        f = item.data(Qt.UserRole)
        self.storage.delete_file(f.get("id"))
        self.record_research_action("file_deleted", {"file_id": f.get("id"), "filename": f.get("filename")})
        self.refresh_lists()

    def link_case(self):
        if not self.current_case:
            QMessageBox.warning(self, "Link Case", "No case selected")
            return
        ref, ok = QInputDialog.getText(self, "Link Case", "Enter related case ref:")
        if not ok or not ref.strip():
            return
        cases = self.storage.search_cases(ref.strip())
        if not cases:
            QMessageBox.warning(self, "Link Case", "No case found matching that ref")
            return
        related = cases[0]
        self.storage.link_case(self.current_case.get("id"), related.get("id"))
        self.load_related_cases()
        self.record_research_action("case_linked", {"related_case": related.get("id"), "ref": related.get("ref")})

    def unlink_selected_case(self):
        item = self.related_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Unlink Case", "Select a related case first")
            return
        related = item.data(Qt.UserRole)
        self.storage.unlink_case(self.current_case.get("id"), related.get("id"))
        self.load_related_cases()
        self.record_research_action("case_unlinked", {"related_case": related.get("id"), "ref": related.get("ref")})

    def save_metadata(self):
        if not self.current_case:
            QMessageBox.warning(self, "Save Metadata", "No case selected")
            return
        meta = {
            "title": self.case_title_input.text().strip(),
            "location": self.location_input.text().strip(),
            "suspect_name": self.suspect_input.text().strip(),
            "victim_name": self.victim_input.text().strip(),
            "category": self.category_input.text().strip(),
        }
        self.storage.update_case(self.current_case.get("id"), **meta)
        self.current_case = self.storage.get_case(self.current_case.get("id"))
        self.title.setText(
            f"Case: {self.current_case.get('ref')} — {self.current_case.get('title')}"
        )
        self.record_research_action("metadata_saved", {"case_id": self.current_case.get("id")})
        self.saved.emit()

    def delete_case(self):
        if not self.current_case:
            QMessageBox.warning(self, "Delete Case", "No case selected")
            return
        ok = QMessageBox.question(
            self,
            "Delete Case",
            f"Delete case {self.current_case.get('ref')}? This is irreversible.",
        )
        if ok == QMessageBox.Yes:
            self.storage.delete_case(self.current_case.get("id"))
            self.case_deleted.emit(self.current_case.get("id"))

    def _on_note_saved(self, note: dict):
        try:
            self.refresh_lists()
        except Exception:
            pass

    def start_research_session(self):
        if not self.current_case:
            QMessageBox.warning(self, "Research Session", "No case selected")
            return
        name, ok = QInputDialog.getText(self, "Start Research Session", "Session name:")
        if not ok:
            return
        session = self.storage.start_research_session(self.current_case.get("id"), name)
        self.current_session = session
        self.load_research_sessions()
        self.record_research_action("research_session_started", {"session_id": session.get("id"), "name": session.get("name")})
        QMessageBox.information(self, "Research Session", f"Started session: {session.get('name')}")

    def end_research_session(self):
        if not getattr(self, "current_session", None):
            QMessageBox.warning(self, "Research Session", "No active research session")
            return
        session_id = self.current_session.get("id")
        session = self.storage.end_research_session(session_id)
        self.current_session = None
        self.load_research_sessions()
        QMessageBox.information(
            self,
            "Research Session",
            f"Ended session: {session.get('name')}"
        )

    def record_research_action(self, event: str, meta: dict | None = None):
        if not getattr(self, "current_session", None):
            return
        try:
            self.storage.add_research_action(self.current_session.get("id"), event, meta or {})
        except Exception:
            pass

    def load_research_sessions(self):
        if not self.current_case:
            return
        self.sessions_list.clear()
        sessions = self.storage.get_research_sessions(self.current_case.get("id"))
        for s in sessions:
            ended = s.get("ended_at")
            status = "Closed" if ended else "Open"
            item = QListWidgetItem(f"{s.get('id')} — {s.get('name')} [{status}]")
            item.setData(Qt.UserRole, s)
            self.sessions_list.addItem(item)
        if self.current_session:
            for i in range(self.sessions_list.count()):
                item = self.sessions_list.item(i)
                session = item.data(Qt.UserRole)
                if session.get("id") == self.current_session.get("id"):
                    self.sessions_list.setCurrentItem(item)
                    break

    def load_related_cases(self):
        if not self.current_case:
            return
        self.related_list.clear()
        related = self.storage.get_related_cases(self.current_case.get("id"))
        for rc in related:
            item = QListWidgetItem(f"{rc.get('ref')} — {rc.get('title')} [{rc.get('status')}]")
            item.setData(Qt.UserRole, rc)
            self.related_list.addItem(item)

    def preview_selected_session(self, current, previous=None):
        if not current:
            return
        session = current.data(Qt.UserRole)
        actions = self.storage.get_research_actions(session.get("id"))
        self.text.clear()
        self.text.append(f"Session: {session.get('name')}\n")
        self.text.append(f"Started: {datetime.fromtimestamp(session.get('started_at')).strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.text.append(f"Ended: {datetime.fromtimestamp(session.get('ended_at')).strftime('%Y-%m-%d %H:%M:%S') if session.get('ended_at') else 'In Progress'}\n\n")
        if actions:
            for a in actions:
                self.text.append(f"- {datetime.fromtimestamp(a.get('ts')).strftime('%Y-%m-%d %H:%M:%S')}: {a.get('event')} {a.get('meta')}")
        else:
            self.text.append("No actions recorded for this session.")

    def show_profiles_dialog(self):
        if not self.current_case:
            QMessageBox.warning(self, "Person Profiles", "No case selected")
            return
        dlg = ProfileListDialog(self.storage, self.current_case.get("id"), self)
        dlg.exec()
        self.refresh_current_case()

    def show_session_dialog(self):
        if not self.current_case:
            QMessageBox.warning(self, "Session Control", "No case selected")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Research Session Control")
        layout = QVBoxLayout(dlg)

        session_list = QListWidget()
        layout.addWidget(session_list)

        details = QTextEdit()
        details.setReadOnly(True)
        details.setMinimumHeight(150)
        layout.addWidget(details)

        def refresh_sessions():
            session_list.clear()
            sessions = self.storage.get_research_sessions(self.current_case.get("id"))
            for s in sessions:
                ended = s.get("ended_at")
                status = "Closed" if ended else "Open"
                item = QListWidgetItem(f"{s.get('id')} — {s.get('name')} [{status}]")
                item.setData(Qt.UserRole, s)
                session_list.addItem(item)
            if session_list.count() > 0:
                session_list.setCurrentRow(0)

        def show_session_details(item):
            if not item:
                details.clear()
                return
            s = item.data(Qt.UserRole)
            actions = self.storage.get_research_actions(s.get("id"))
            lines = [
                f"Name: {s.get('name')}",
                f"Started: {datetime.fromtimestamp(s.get('started_at')).strftime('%Y-%m-%d %H:%M:%S')}",
                f"Ended: {datetime.fromtimestamp(s.get('ended_at')).strftime('%Y-%m-%d %H:%M:%S') if s.get('ended_at') else 'In Progress'}",
                "",
                "Actions:",
            ]
            if actions:
                for a in actions:
                    lines.append(f"- {datetime.fromtimestamp(a.get('ts')).strftime('%Y-%m-%d %H:%M:%S')}: {a.get('event')} {a.get('meta')}")
            else:
                lines.append("No actions recorded")
            details.setPlainText("\n".join(lines))

        session_list.currentItemChanged.connect(lambda current, _: show_session_details(current))

        btn_start = QPushButton("Start Session")
        btn_end = QPushButton("End Selected Session")
        btn_close = QPushButton("Close")

        def handle_start():
            name, ok = QInputDialog.getText(dlg, "Start Research Session", "Session name:")
            if not ok or not name.strip():
                return
            self.storage.start_research_session(self.current_case.get("id"), name.strip())
            refresh_sessions()

        def handle_end():
            item = session_list.currentItem()
            if not item:
                QMessageBox.warning(dlg, "End Session", "Select a session first")
                return
            session = item.data(Qt.UserRole)
            if session.get("ended_at"):
                QMessageBox.information(dlg, "End Session", "Selected session is already closed")
                return
            self.storage.end_research_session(session.get("id"))
            refresh_sessions()

        btn_start.clicked.connect(handle_start)
        btn_end.clicked.connect(handle_end)
        btn_close.clicked.connect(dlg.accept)

        action_layout = QHBoxLayout()
        action_layout.addWidget(btn_start)
        action_layout.addWidget(btn_end)
        action_layout.addStretch(1)
        action_layout.addWidget(btn_close)
        layout.addLayout(action_layout)

        refresh_sessions()
        dlg.exec()
        self.refresh_current_case()

    def show_case_link_dialog(self):
        if not self.current_case:
            QMessageBox.warning(self, "Related Cases", "No case selected")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Related Cases")
        layout = QVBoxLayout(dlg)

        related_list = QListWidget()
        layout.addWidget(related_list)

        def refresh_links():
            related_list.clear()
            for rc in self.storage.get_related_cases(self.current_case.get("id")):
                item = QListWidgetItem(f"{rc.get('ref')} — {rc.get('title')} [{rc.get('status')}]")
                item.setData(Qt.UserRole, rc)
                related_list.addItem(item)

        def handle_add():
            ref, ok = QInputDialog.getText(dlg, "Link Case", "Enter related case ref:")
            if not ok or not ref.strip():
                return
            cases = self.storage.search_cases(ref.strip())
            if not cases:
                QMessageBox.warning(dlg, "Link Case", "No case found matching that ref")
                return
            related = cases[0]
            self.storage.link_case(self.current_case.get("id"), related.get("id"))
            refresh_links()

        def handle_remove():
            item = related_list.currentItem()
            if not item:
                QMessageBox.warning(dlg, "Unlink Case", "Select a related case first")
                return
            related = item.data(Qt.UserRole)
            self.storage.unlink_case(self.current_case.get("id"), related.get("id"))
            refresh_links()

        btn_add = QPushButton("Link Case")
        btn_remove = QPushButton("Unlink Case")
        btn_close = QPushButton("Close")
        btn_add.clicked.connect(handle_add)
        btn_remove.clicked.connect(handle_remove)
        btn_close.clicked.connect(dlg.accept)

        action_layout = QHBoxLayout()
        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_remove)
        action_layout.addStretch(1)
        action_layout.addWidget(btn_close)
        layout.addLayout(action_layout)

        refresh_links()
        dlg.exec()
        self.refresh_current_case()

    def export_case_pdf(self):
        if not self.current_case:
            QMessageBox.warning(self, "Export PDF", "No case selected")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Case Summary as PDF",
            f"case_{self.current_case.get('ref', 'summary')}.pdf",
            "PDF Files (*.pdf)",
        )
        if not save_path:
            return False
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        try:
            document = QTextDocument()
            document.setHtml(self._build_case_summary_html())

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(save_path)
            document.print_(printer)

            QMessageBox.information(
                self, "Export Complete", f"Case summary exported to:\n{save_path}"
            )
            return True
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Unable to export PDF: {e}")
            return False

    def _build_case_summary_html(self) -> str:
        case = self.current_case
        notes = self.storage.get_notes(case.get("id"))
        files = self.storage.get_files(case.get("id"))

        html = [
            '<html><head><meta charset="utf-8"><style>'
            "body { font-family: Arial, sans-serif; margin: 24px; } "
            "h1 { font-size: 24px; margin-bottom: 8px; } "
            "h2 { font-size: 18px; margin-top: 20px; } "
            "p { margin: 6px 0; } "
            "table { width: 100%; border-collapse: collapse; margin-top: 10px; } "
            "th, td { border: 1px solid #888; padding: 8px; text-align: left; vertical-align: top; } "
            "th { background: #f0f0f0; } "
            "</style></head><body>"
        ]

        html.append(f"<h1>Case Summary: {case.get('ref')}</h1>")
        html.append(f"<p><strong>Title:</strong> {case.get('title') or ''}</p>")
        html.append(f"<p><strong>Location:</strong> {case.get('location') or ''}</p>")
        html.append(
            f"<p><strong>Suspect:</strong> {case.get('suspect_name') or ''}</p>"
        )
        html.append(f"<p><strong>Victim:</strong> {case.get('victim_name') or ''}</p>")
        html.append(f"<p><strong>Category:</strong> {case.get('category') or ''}</p>")

        def _fmt(dtval):
            if not dtval:
                return ""
            if isinstance(dtval, str):
                try:
                    d = datetime.fromisoformat(dtval)
                    return d.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    return dtval
            if isinstance(dtval, (int, float)):
                try:
                    d = datetime.fromtimestamp(dtval)
                    return d.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    return str(dtval)
            try:
                return dtval.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return str(dtval)

        html.append(f"<p><strong>Created:</strong> {_fmt(case.get('created_at'))}</p>")
        html.append(
            f"<p><strong>Last Updated:</strong> {_fmt(case.get('updated_at'))}</p>"
        )

        html.append("<h2>Notes</h2>")
        if notes:
            html.append("<table>")
            html.append("<tr><th>ID</th><th>Summary</th><th>Content</th></tr>")
            for note in notes:
                html.append(
                    "<tr>"
                    f'<td>{note.get("id")}</td>'
                    f'<td>{note.get("summary")}</td>'
                    f'<td>{note.get("content")}</td>'
                    "</tr>"
                )
            html.append("</table>")
        else:
            html.append("<p><em>No notes found for this case.</em></p>")

        html.append("<h2>Attachments</h2>")
        if files:
            html.append("<table>")
            html.append("<tr><th>ID</th><th>Filename</th></tr>")
            for f in files:
                html.append(
                    "<tr>"
                    f'<td>{f.get("id")}</td>'
                    f'<td>{f.get("filename")}</td>'
                    "</tr>"
                )
            html.append("</table>")
        else:
            html.append("<p><em>No attachments available.</em></p>")

        html.append("</body></html>")
        return "".join(html)


if __name__ == "__main__":
    pass
