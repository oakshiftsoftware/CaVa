import os

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QTabWidget,
    QMessageBox,
)
from PySide6.QtCore import Qt


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "assets", filename)


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "assets", filename)


from data.config import AppConfig
from ui.dashboard import DashboardWidget
from ui.editor import EditorWidget
from ui.settings import SettingsDialog
from ui.audit import AuditDialog

import vault.auth as auth
import vault.storage as storage
import vault.db as db


class CaVaMain(QMainWindow):
    config = AppConfig()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            f"{self.config.org_tag} {self.config.app_name} (v{self.config.version})"
        )
        png_path = _asset_path("cava_logo.png")
        app_icon = QIcon(QPixmap(png_path))
        if app_icon.isNull():
            icon_path = _asset_path("cava_icon.ico")
            app_icon = QIcon(icon_path)
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(app_icon)
        self.config.app_resize(self, "medium")
        self.config.app_menubar(self)
        self.apply_theme()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)

        self.login_dialog = None
        self.setup_dialog = None
        self.dashboard = DashboardWidget(storage, self.config)

        self.hide()

        self.dashboard.open_editor.connect(self.open_case_tab)
        self.dashboard.case_deleted.connect(self.on_case_deleted)
        self.dashboard.logout.connect(self.lock_session)

        self.user_authenticated = False
        if not auth.is_initialized():
            self.show_setup()
        else:
            self.show_login()

    def show_login(self):
        self.ensure_login_dialog()
        self.login_dialog.widget.refresh()
        result = self.login_dialog.exec()
        if result != QDialog.Accepted:
            QApplication.instance().quit()

    def show_setup(self):
        self.ensure_setup_dialog()
        result = self.setup_dialog.exec()
        if result != QDialog.Accepted:
            QApplication.instance().quit()
        self.setWindowTitle(
            f"{self.config.org_tag} {self.config.app_name} (v{self.config.version})"
        )
        self.show_login()

    def ensure_setup_dialog(self):
        if self.setup_dialog is None:
            from ui.login import SetupDialog

            self.setup_dialog = SetupDialog(auth, self.config, self)
            self.setup_dialog.setup_success.connect(self._on_setup_success)

    def _on_setup_success(self, password: str, org_tag: str):
        self.config.org_tag = org_tag
        self.config.save()
        self.on_vault_initialized(password)

    def ensure_login_dialog(self):
        if self.login_dialog is None:
            from ui.login import LoginDialog

            self.login_dialog = LoginDialog(auth, self.config, self)
            self.login_dialog.login_success.connect(self.on_login)
            self.login_dialog.init_success.connect(self.on_vault_initialized)

    def on_vault_initialized(self, password: str):
        try:
            key = auth.get_db_key_hex(password)
            if key:
                db.init_db(key)
            else:
                db.init_db()
            storage.add_audit("vault_initialized")
        except Exception:
            storage.add_audit("vault_init_failed")

    def on_login(self, password: str):
        try:
            key = auth.get_db_key_hex(password)
            if key:
                db.init_db(key)
            else:
                db.init_db()
        except Exception:
            db.init_db()
        self.user_authenticated = True
        storage.add_audit("user_login")
        self.dashboard.refresh()
        self.tabs.clear()
        self.tabs.addTab(self.dashboard, "Cases")
        self.setCentralWidget(self.tabs)
        self.show()
        self.show()

    def show_dashboard(self):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) is self.dashboard:
                self.tabs.setCurrentIndex(i)
                return

        self.tabs.addTab(self.dashboard, "Cases")
        self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def open_case_tab(self, case):
        ref = case.get("ref")
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if (
                hasattr(w, "current_case")
                and w.current_case
                and w.current_case.get("ref") == ref
            ):
                self.tabs.setCurrentIndex(i)
                return

        editor = EditorWidget(storage, self.config)
        editor.load_case(case)
        editor.saved.connect(self.on_saved)

        if hasattr(editor, "case_deleted"):
            editor.case_deleted.connect(self.on_case_deleted)
        editor.cancelled.connect(self.show_dashboard)
        self.tabs.addTab(editor, f"{case.get('ref')}")
        self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def on_case_deleted(self, case_id: int):
        to_close = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if (
                hasattr(w, "current_case")
                and w.current_case
                and w.current_case.get("id") == case_id
            ):
                to_close.append(i)

        for idx in sorted(to_close, reverse=True):
            self.tabs.removeTab(idx)
        self.dashboard.refresh()

    def _close_tab(self, index: int):
        widget = self.tabs.widget(index)
        if widget is self.dashboard:
            QMessageBox.warning(self, "Close Tab", "Cannot close the Cases tab")
            return

        self.tabs.removeTab(index)
        try:
            widget.deleteLater()
        except Exception:
            pass

        if self.tabs.count() == 0:
            self.tabs.addTab(self.dashboard, "Cases")
            self.setCentralWidget(self.tabs)

    def on_saved(self):
        storage.add_audit("note_saved")
        self.dashboard.refresh()

    def lock_session(self):
        storage.add_audit("user_logout")
        self.user_authenticated = False
        self.tabs.clear()
        self.hide()
        self.show_login()

    def closeQuestion(self):
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.close()

    def open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            self.apply_theme()
            self.setWindowTitle(
                f"{self.config.org_tag} {self.config.app_name} (v{self.config.version})"
            )

    def show_audit(self):
        dlg = AuditDialog(storage, self)
        dlg.exec()

    def show_error_codes(self):
        error_codes = [
            (auth.ERROR_CODE_VAULT_ALREADY_INITIALIZED, "Vault already initialized"),
            (auth.ERROR_CODE_VAULT_NOT_INITIALIZED, "Vault has not been initialized"),
            (auth.ERROR_CODE_INVALID_PASSWORD, "Incorrect password"),
            (
                auth.ERROR_CODE_CRYPTO_MISSING,
                "Argon2 is not available; install argon2-cffi",
            ),
            (auth.ERROR_CODE_KEY_DERIVATION_FAILED, "Unable to derive vault key"),
            (auth.ERROR_CODE_GENERAL_FAILURE, "General failure or unexpected error"),
        ]
        message = "\n".join([f"{code}: {text}" for code, text in error_codes])
        QMessageBox.information(self, "Error Codes", message)

    def aboutMessage(self):
        _about_text = (
            f"{self.config.app_name} — v{self.config.version}\n"
            f"Author: {self.config.author}\n"
            f"License: {self.config.license}\n"
            f"Organization: {self.config.org_tag}\n\n"
            "Case Vault is a secure, local only, case management system with encrypted storage, notes, and file attachments."
        )
        QMessageBox.information(self, "About", _about_text)

    def apply_theme(self):
        if self.config.theme == "dark":
            self.setStyleSheet(
                "QWidget { background: #2b2b2b; color: #f0f0f0; } "
                "QLineEdit, QTextEdit, QListWidget, QPlainTextEdit { background: #3b3b3b; color: #f0f0f0; } "
                "QPushButton { background: #444444; color: #f0f0f0; border: 1px solid #555555; } "
                "QPushButton:hover { background: #5a5a5a; }"
            )
        else:
            self.setStyleSheet("")


if __name__ == "__main__":
    app = QApplication()
    png_path = _asset_path("cava_logo.png")
    app_icon = QIcon(QPixmap(png_path))
    if app_icon.isNull():
        icon_path = _asset_path("cava_icon.ico")
        app_icon = QIcon(icon_path)
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    window = CaVaMain()
    window.show()
    app.exec()
