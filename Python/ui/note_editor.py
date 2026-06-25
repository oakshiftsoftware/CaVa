import os

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)
from PySide6.QtCore import Signal


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


class NoteEditorDialog(QDialog):
    saved = Signal(dict)

    def __init__(self, storage, case_id: int, note: dict | None = None, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.case_id = case_id
        self.note = note
        self.setWindowTitle("Note Editor")
        app_icon = QIcon(QPixmap(_asset_path("cava_logo.png")))
        if app_icon.isNull():
            app_icon = QIcon(_asset_path("cava_icon.ico"))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
        self.setModal(True)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Summary"))
        self.summary_input = QLineEdit()
        layout.addWidget(self.summary_input)

        layout.addWidget(QLabel("Content"))
        self.content_input = QTextEdit()
        layout.addWidget(self.content_input)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(lambda: self.save_note(close_after=False))
        self.save_close_btn = QPushButton("Save and Close")
        self.save_close_btn.clicked.connect(lambda: self.save_note(close_after=True))
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_note)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.save_close_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        if self.note:
            self.summary_input.setText(self.note.get("summary", ""))
            self.content_input.setPlainText(self.note.get("content", ""))
        else:
            self.delete_btn.setEnabled(False)

    def save_note(self, close_after: bool = False):
        summary = self.summary_input.text().strip()
        content = self.content_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Save Note", "Note content cannot be empty.")
            return
        if not summary:
            summary = content.splitlines()[0]

        if self.note:
            self.storage.update_note(self.note.get("id"), summary, content)
        else:
            self.note = self.storage.add_note(self.case_id, summary, content)

        try:
            self.saved.emit(self.note)
        except Exception:
            pass

        if close_after:
            self.accept()
        else:
            self.summary_input.setText(self.note.get("summary", ""))
            self.content_input.setPlainText(self.note.get("content", ""))
            QMessageBox.information(self, "Save Note", "Note saved.")

    def delete_note(self):
        if not self.note:
            return
        answer = QMessageBox.question(
            self,
            "Delete Note",
            "Delete this note? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.storage.delete_note(self.note.get("id"))
            self.accept()
