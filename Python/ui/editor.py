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
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import Signal, Qt
from datetime import datetime
from ui.note_editor import NoteEditorDialog


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

        files_panel = QVBoxLayout()
        files_label = QLabel("Attachments")
        files_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.files_list = QListWidget()
        files_panel.addWidget(files_label)
        files_panel.addWidget(self.files_list)

        lists_layout.addLayout(notes_panel)
        lists_layout.addLayout(files_panel)

        self.text = QTextEdit()
        self.text.setReadOnly(True)

        btn_new_note = QPushButton("New Note")
        btn_new_note.clicked.connect(self.open_new_note)

        btn_edit_note = QPushButton("Edit Note")
        btn_edit_note.clicked.connect(self.edit_selected_note)

        btn_add_file = QPushButton("Add File")
        btn_add_file.clicked.connect(self.add_file)

        btn_delete_note = QPushButton("Delete Note")
        btn_delete_note.clicked.connect(self.delete_selected_note)

        btn_delete_file = QPushButton("Delete File")
        btn_delete_file.clicked.connect(self.delete_selected_file)

        btn_save_meta = QPushButton("Save Metadata")
        btn_save_meta.clicked.connect(self.save_metadata)

        btn_export_pdf = QPushButton("Export Case PDF")
        btn_export_pdf.clicked.connect(self.export_case_pdf)

        btn_delete_case = QPushButton("Delete Case")
        btn_delete_case.clicked.connect(self.delete_case)

        btn_back = QPushButton("Back")
        btn_back.clicked.connect(lambda: self.cancelled.emit())

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_new_note)
        btn_layout.addWidget(btn_edit_note)
        btn_layout.addWidget(btn_add_file)
        btn_layout.addWidget(btn_delete_note)
        btn_layout.addWidget(btn_delete_file)
        btn_layout.addWidget(btn_save_meta)
        btn_layout.addWidget(btn_export_pdf)
        btn_layout.addWidget(btn_delete_case)
        btn_layout.addWidget(btn_back)

        layout.addWidget(self.title)
        layout.addLayout(self.meta_form)
        layout.addLayout(lists_layout)
        layout.addWidget(self.text)
        layout.addLayout(btn_layout)

        self.notes_list.currentItemChanged.connect(self.preview_selected_note)

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
        self.refresh_lists()

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

        self.text.clear()

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
        self.refresh_lists()

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
            self.saved.emit()
        except Exception:
            pass

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
            return
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
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Unable to export PDF: {e}")

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
