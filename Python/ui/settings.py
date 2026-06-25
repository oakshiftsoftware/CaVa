import os

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QPushButton,
    QButtonGroup,
    QMessageBox,
)
from PySide6.QtCore import Qt


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Application Settings")
        app_icon = QIcon(QPixmap(_asset_path("cava_logo.png")))
        if app_icon.isNull():
            app_icon = QIcon(_asset_path("cava_icon.ico"))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
        self.config.app_resize(self, "small")
        self.setModal(True)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Theme"))
        self.light_radio = QRadioButton("Light")
        self.dark_radio = QRadioButton("Dark")
        theme_group = QButtonGroup(self)
        theme_group.addButton(self.light_radio)
        theme_group.addButton(self.dark_radio)
        layout.addWidget(self.light_radio)
        layout.addWidget(self.dark_radio)

        if self.config.theme == "dark":
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

    def save_settings(self):
        self.config.theme = "dark" if self.dark_radio.isChecked() else "light"
        self.config.save()
        QMessageBox.information(
            self,
            "Settings",
            "Settings saved. Restart or re-open the app to apply the theme.",
        )
        self.accept()
