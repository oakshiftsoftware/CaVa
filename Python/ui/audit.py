import json
import os
from datetime import datetime

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


class AuditDialog(QDialog):
    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("Audit Log")
        self.setModal(True)

        app_icon = QIcon(QPixmap(_asset_path("cava_logo.png")))
        if app_icon.isNull():
            app_icon = QIcon(_asset_path("cava_icon.ico"))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        layout = QVBoxLayout(self)

        header = QLabel("Audit Log")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        self.audit_list = QListWidget()
        self.audit_list.currentItemChanged.connect(self.preview_selected)
        layout.addWidget(self.audit_list)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.details)

        button_layout = QHBoxLayout()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addStretch(1)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)

        self.refresh()

    def refresh(self):
        self.audit_list.clear()
        for entry in self.storage.get_audit():
            ts = entry.get("ts")
            text = entry.get("event") or ""
            label = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            item = QListWidgetItem(f"{label} — {text}")
            item.setData(Qt.UserRole, entry)
            self.audit_list.addItem(item)
        if self.audit_list.count() > 0:
            self.audit_list.setCurrentRow(0)

    def preview_selected(self, current, previous=None):
        if not current:
            self.details.clear()
            return
        entry = current.data(Qt.UserRole)
        content = {
            "id": entry.get("id"),
            "ts": entry.get("ts"),
            "event": entry.get("event"),
            "meta": entry.get("meta"),
        }
        self.details.setPlainText(json.dumps(content, indent=2, default=str))
