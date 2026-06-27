import os

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Qt


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


class ProfileDialog(QDialog):
    def __init__(self, storage, case_id: int, profile: dict | None = None, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.case_id = case_id
        self.profile = profile
        self.setWindowTitle("Person Profile")
        self.setModal(True)

        app_icon = QIcon(QPixmap(_asset_path("cava_logo.png")))
        if app_icon.isNull():
            app_icon = QIcon(_asset_path("cava_icon.ico"))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Name"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Association Type"))
        self.association_input = QLineEdit()
        self.association_input.setPlaceholderText("e.g. Suspect, Victim, Witness, Analyst")
        layout.addWidget(self.association_input)

        layout.addWidget(QLabel("Role"))
        self.role_input = QLineEdit()
        layout.addWidget(self.role_input)

        layout.addWidget(QLabel("Contact Info"))
        self.contact_input = QLineEdit()
        layout.addWidget(self.contact_input)

        layout.addWidget(QLabel("Description"))
        self.description_input = QTextEdit()
        layout.addWidget(self.description_input)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_profile)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        if self.profile:
            self.name_input.setText(self.profile.get("name", ""))
            self.association_input.setText(self.profile.get("association_type", ""))
            self.role_input.setText(self.profile.get("role", ""))
            self.contact_input.setText(self.profile.get("contact_info", ""))
            self.description_input.setPlainText(self.profile.get("description", ""))

    def save_profile(self):
        name = self.name_input.text().strip()
        association = self.association_input.text().strip()
        if not name or not association:
            QMessageBox.warning(self, "Person Profile", "Name and association type are required.")
            return

        data = {
            "name": name,
            "association_type": association,
            "role": self.role_input.text().strip(),
            "contact_info": self.contact_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
        }

        if self.profile:
            self.storage.update_case_profile(self.profile.get("id"), **data)
        else:
            self.profile = self.storage.create_case_profile(
                self.case_id,
                name,
                association,
                role=data["role"],
                contact_info=data["contact_info"],
                description=data["description"],
            )

        self.accept()


class ProfileListDialog(QDialog):
    def __init__(self, storage, case_id: int, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.case_id = case_id
        self.setWindowTitle("Case People Profiles")
        self.setModal(True)

        app_icon = QIcon(QPixmap(_asset_path("cava_logo.png")))
        if app_icon.isNull():
            app_icon = QIcon(_asset_path("cava_icon.ico"))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        layout = QVBoxLayout(self)

        header = QLabel("Person Profiles")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        self.profiles_list = QListWidget()
        self.profiles_list.currentItemChanged.connect(self.preview_selected)
        layout.addWidget(self.profiles_list)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(150)
        layout.addWidget(self.details)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Profile")
        self.add_btn.clicked.connect(self.add_profile)
        self.edit_btn = QPushButton("Edit Profile")
        self.edit_btn.clicked.connect(self.edit_profile)
        self.delete_btn = QPushButton("Delete Profile")
        self.delete_btn.clicked.connect(self.delete_profile)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.refresh()

    def refresh(self):
        self.profiles_list.clear()
        profiles = self.storage.get_case_profiles(self.case_id)
        for p in profiles:
            item = QListWidgetItem(f"{p.get('name')} — {p.get('association_type')}")
            item.setData(Qt.UserRole, p)
            self.profiles_list.addItem(item)
        if self.profiles_list.count() > 0:
            self.profiles_list.setCurrentRow(0)

    def preview_selected(self, current, previous=None):
        if not current:
            self.details.clear()
            return
        profile = current.data(Qt.UserRole)
        lines = [
            f"Name: {profile.get('name')}",
            f"Association: {profile.get('association_type')}",
            f"Role: {profile.get('role') or 'N/A'}",
            f"Contact: {profile.get('contact_info') or 'N/A'}",
            "",
            f"Description:\n{profile.get('description') or 'No description'}",
        ]
        self.details.setPlainText("\n".join(lines))

    def add_profile(self):
        dlg = ProfileDialog(self.storage, self.case_id, None, self)
        if dlg.exec():
            self.refresh()

    def edit_profile(self):
        item = self.profiles_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Edit Profile", "Select a profile first.")
            return
        profile = item.data(Qt.UserRole)
        dlg = ProfileDialog(self.storage, self.case_id, profile, self)
        if dlg.exec():
            self.refresh()

    def delete_profile(self):
        item = self.profiles_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Delete Profile", "Select a profile first.")
            return
        profile = item.data(Qt.UserRole)
        answer = QMessageBox.question(
            self,
            "Delete Profile",
            f"Delete profile for {profile.get('name')}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.storage.delete_case_profile(profile.get('id'))
            self.refresh()
