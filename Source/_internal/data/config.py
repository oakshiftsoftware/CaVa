# Imports


import os
import json


class AppConfig:
    def __init__(self):
        self.org_tag = ""
        self.app_name = "Case Vault"
        self.version = "1.2.2"
        self.author = "Oakshift Software"
        self.license = "CLASSIFIED"
        self.theme = "light"
        self.window_sizes = {
            "login": [360, 220],
            "small": [400, 100],
            "medium": [800, 600],
        }

        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                theme = data.get("theme")
                if isinstance(theme, str) and theme.lower() in ("light", "dark"):
                    self.theme = theme.lower()
                org_tag = data.get("org_tag")
                if isinstance(org_tag, str) and org_tag.strip():
                    self.org_tag = org_tag.strip()
            except Exception:
                pass

    def save(self, path: str | None = None):
        cfg_file = path or self.config_path
        data = {
            "theme": self.theme,
            "org_tag": self.org_tag,
        }
        try:
            with open(cfg_file, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except Exception:
            pass

    def app_menubar(self, app):
        menubar = app.menuBar()
        file_menu = menubar.addMenu("File")
        help_menu = menubar.addMenu("Help")

        settings_action = file_menu.addAction("Settings")
        settings_action.triggered.connect(app.open_settings)

        fm_action = file_menu.addAction("Exit")
        fm_action.triggered.connect(app.closeQuestion)

        hm_action = help_menu.addAction("About")
        hm_action.triggered.connect(app.aboutMessage)

        hc_action = help_menu.addAction("Errors")
        hc_action.triggered.connect(app.show_error_codes)

    def app_resize(self, app, size_key: str):
        width, height = self._get_window_size(size_key)
        app.resize(width, height)

    def _get_window_size(self, size_key: str):
        if size_key in self.window_sizes:
            return (
                int(self.window_sizes[size_key][0]),
                int(self.window_sizes[size_key][1]),
            )
        else:
            return (
                int(self.window_sizes["small"][0]),
                int(self.window_sizes["small"][1]),
            )


if __name__ == "__main__":
    pass
