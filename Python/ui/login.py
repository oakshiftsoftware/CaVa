import os

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialog,
    QFormLayout,
    QRadioButton,
    QButtonGroup,
)
from PySide6.QtCore import Signal, Qt


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


class LoginWidget(QWidget):
    login_success = Signal(str)
    init_success = Signal(str)

    def __init__(self, auth, config, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.config = config

        layout = QVBoxLayout(self)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_path = _asset_path("cava_logo.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            )
        else:
            logo_label.setText(f"{self.config.org_tag} {self.config.app_name}")
            logo_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(logo_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter master password")

        self.login_button = QPushButton("Log in")
        self.login_button.clicked.connect(self.attempt_login)

        self.setpw_button = QPushButton("Initialize Vault (first run)")
        self.setpw_button.clicked.connect(self.set_password)

        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.setpw_button)

        self.refresh()

    def refresh(self):
        if self.auth.is_initialized():
            self.setpw_button.setVisible(False)
            self.login_button.setEnabled(True)
            self.password_input.setEnabled(True)
        else:
            self.setpw_button.setVisible(True)
            self.login_button.setEnabled(False)
            self.password_input.setEnabled(True)

    def attempt_login(self):
        pw = self.password_input.text()
        if not pw:
            QMessageBox.warning(self, "Login", "Please enter a password")
            return
        try:
            if self.auth.verify_password(pw):
                self.password_input.clear()
                self.login_success.emit(pw)
        except Exception as exc:
            code = getattr(exc, "code", "E199")
            QMessageBox.critical(self, "Login Failed", f"{exc}\n\nError code: {code}")

    def set_password(self):
        pw = self.password_input.text()
        if not pw:
            QMessageBox.warning(
                self, "Initialize", "Enter a new master password in the field first"
            )
            return
        try:
            self.auth.initialize(pw)
            QMessageBox.information(
                self, "Initialized", "Vault initialized. You can now log in."
            )
            self.init_success.emit(pw)
            self.refresh()
        except Exception as e:
            code = getattr(e, "code", "E199")
            QMessageBox.critical(
                self, "Error", f"Failed to initialize: {e}\n\nError code: {code}"
            )


class SetupDialog(QDialog):
    setup_success = Signal(str, str)

    def __init__(self, auth, config, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.config = config
        self.setWindowTitle(f"{self.config.app_name} Setup")
        self.setModal(True)
        self.config.app_resize(self, "login")
        app_icon = QIcon(QPixmap(_asset_path("cava_logo.png")))
        if app_icon.isNull():
            app_icon = QIcon(_asset_path("cava_icon.ico"))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.org_input = QLineEdit()
        self.org_input.setPlaceholderText("Enter your organisation tag")
        form.addRow("Organisation:", self.org_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter master password")
        form.addRow("Master Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm password")
        form.addRow("Confirm Password:", self.confirm_input)

        layout.addLayout(form)

        layout.addWidget(QLabel("Theme"))
        self.light_radio = QRadioButton("Light")
        self.dark_radio = QRadioButton("Dark")
        theme_buttons = QButtonGroup(self)
        theme_buttons.addButton(self.light_radio)
        theme_buttons.addButton(self.dark_radio)
        layout.addWidget(self.light_radio)
        layout.addWidget(self.dark_radio)

        if self.config.theme == "dark":
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)

        self.init_button = QPushButton("Initialize and Continue")
        self.init_button.clicked.connect(self.initialize_vault)
        layout.addWidget(self.init_button)

    def _set_logo(self, layout: QVBoxLayout):
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_path = _asset_path("cava_logo.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            )
        else:
            logo_label.setText(f"{self.config.org_tag} {self.config.app_name}")
            logo_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.insertWidget(0, logo_label)

    def initialize_vault(self):
        org_tag = self.org_input.text().strip()
        pw = self.password_input.text()
        confirm = self.confirm_input.text()

        if not org_tag:
            QMessageBox.warning(self, "Setup", "Please enter an organisation tag")
            return
        if not pw:
            QMessageBox.warning(self, "Setup", "Please enter a master password")
            return
        if pw != confirm:
            QMessageBox.warning(self, "Setup", "Password and confirmation do not match")
            return

        try:
            self.auth.initialize(pw)
            self.config.org_tag = org_tag
            self.config.theme = "dark" if self.dark_radio.isChecked() else "light"
            self.config.save()
            QMessageBox.information(
                self, "Setup Complete", "Vault initialized and settings saved."
            )
            self.setup_success.emit(pw, org_tag)
            self.accept()
        except Exception as e:
            code = getattr(e, "code", "E199")
            QMessageBox.critical(
                self, "Error", f"Failed to initialize vault: {e}\n\nError code: {code}"
            )


class LoginDialog(QDialog):
    login_success = Signal(str)
    init_success = Signal(str)

    def __init__(self, auth, config, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.config = config
        self.setWindowTitle(f"{self.config.app_name} Login")
        self.setModal(True)
        self.config.app_resize(self, "login")
        app_icon = QIcon(QPixmap(_asset_path("cava_logo.png")))
        if app_icon.isNull():
            app_icon = QIcon(_asset_path("cava_icon.ico"))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        layout = QVBoxLayout(self)
        self.widget = LoginWidget(self.auth, self.config, self)
        self.widget.login_success.connect(self.handle_login)
        self.widget.init_success.connect(self.handle_init)
        layout.addWidget(self.widget)

    def handle_login(self, password: str):
        self.login_success.emit(password)
        self.accept()

    def handle_init(self, password: str):
        self.init_success.emit(password)


if __name__ == "__main__":
    pass
