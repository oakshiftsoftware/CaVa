from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt


class DashboardWidget(QWidget):
    open_editor = Signal(object)
    logout = Signal()
    case_deleted = Signal(int)

    def __init__(self, storage, config, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.config = config

        layout = QVBoxLayout(self)

        header = QLabel(f"{self.config.app_name} — Cases")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-weight: bold; font-size: 14px;")

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search cases by title or ref")
        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.search_cases)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_search)

        self.list_widget = QListWidget()

        btn_new = QPushButton("New Case")
        btn_new.clicked.connect(self.new_case)

        btn_open = QPushButton("Open Case")
        btn_open.clicked.connect(self.open_selected)

        btn_delete = QPushButton("Delete Case")
        btn_delete.clicked.connect(self.delete_selected)

        btn_complete = QPushButton("Complete Case")
        btn_complete.clicked.connect(self.complete_selected)

        btn_logout = QPushButton("Lock / Logout")
        btn_logout.clicked.connect(lambda: self.logout.emit())

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_open)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_complete)
        btn_layout.addWidget(btn_logout)

        layout.addWidget(header)
        layout.addLayout(search_layout)
        layout.addWidget(self.list_widget)
        layout.addLayout(btn_layout)

        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        cases = self.storage.list_cases()
        for c in cases:
            item = QListWidgetItem(
                f"{c.get('ref')} — {c.get('title')} [{c.get('status')}]"
            )
            item.setData(Qt.UserRole, c)
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(self._open_from_item)

    def search_cases(self):
        q = self.search_input.text().strip()
        if not q:
            self.refresh()
            return
        self.list_widget.clear()
        cases = self.storage.search_cases(q)
        for c in cases:
            item = QListWidgetItem(
                f"{c.get('ref')} — {c.get('title')} [{c.get('status')}]"
            )
            item.setData(Qt.UserRole, c)
            self.list_widget.addItem(item)

    def new_case(self):
        title, ok = QInputDialog.getText(self, "New Case", "Case title:")
        if not ok or not title.strip():
            return
        case = self.storage.create_case(title.strip())
        self.refresh()

    def _open_from_item(self, item: QListWidgetItem):
        case = item.data(Qt.UserRole)
        self.open_editor.emit(case)

    def open_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Open", "Select a case first")
            return
        self._open_from_item(item)

    def delete_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Delete", "Select a case first")
            return
        case = item.data(Qt.UserRole)
        ok = QMessageBox.question(
            self, "Delete", f"Delete case {case.get('ref')}? This is irreversible."
        )
        if ok == QMessageBox.Yes:
            self.storage.delete_case(case.get("id"))
            self.case_deleted.emit(case.get("id"))
            self.refresh()

    def complete_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Complete", "Select a case first")
            return
        case = item.data(Qt.UserRole)
        self.storage.complete_case(case.get("id"))
        self.refresh()


if __name__ == "__main__":
    pass
