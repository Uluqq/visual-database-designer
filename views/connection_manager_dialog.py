# views/connection_manager_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt
from controllers.connection_controller import ConnectionController
from .connection_dialog import ConnectionDialog
from models.user import User


class ConnectionManagerDialog(QDialog):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Менеджер подключений")
        self.setMinimumSize(500, 300)

        self.current_user = user;
        self.controller = ConnectionController();
        self.selected_connection = None

        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget();
        self.list_widget.itemDoubleClicked.connect(self.accept)
        self.layout.addWidget(self.list_widget)

        buttons_layout = QHBoxLayout()
        self.import_button = QPushButton("Импортировать");
        self.import_button.setEnabled(False)
        add_button = QPushButton("Добавить...");
        cancel_button = QPushButton("Отмена")

        buttons_layout.addWidget(add_button);
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button);
        buttons_layout.addWidget(self.import_button)
        self.layout.addLayout(buttons_layout)

        self.import_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        add_button.clicked.connect(self.handle_add_connection)
        self.list_widget.currentItemChanged.connect(self.on_selection_change)
        self.load_connections()

    def load_connections(self):
        self.list_widget.clear()
        connections = self.controller.get_connections_for_user(self.current_user.user_id)
        if not connections:
            self.list_widget.addItem("Сохраненных подключений нет. Добавьте новое.");
            self.list_widget.setEnabled(False);
            return

        self.list_widget.setEnabled(True)
        for conn in connections:
            item = QListWidgetItem(f"{conn.connection_name} ({conn.db_username}@{conn.host})")
            item.setData(Qt.UserRole, conn);
            self.list_widget.addItem(item)

    def handle_add_connection(self):
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            conn, message = self.controller.add_connection(user_id=self.current_user.user_id, **data)
            if conn:
                self.load_connections()
            else:
                QMessageBox.critical(self, "Ошибка", message)

    def on_selection_change(self, current_item: QListWidgetItem, previous_item):
        if current_item and current_item.data(Qt.UserRole):
            self.import_button.setEnabled(True);
            self.selected_connection = current_item.data(Qt.UserRole)
        else:
            self.import_button.setEnabled(False);
            self.selected_connection = None

    def accept(self):
        if not self.selected_connection:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите подключение для импорта.");
            return
        super().accept()