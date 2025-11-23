# views/connection_manager_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QMessageBox, QListWidgetItem, QFrame, QWidget, QLabel
)
from PySide6.QtCore import Qt
from controllers.connection_controller import ConnectionController
from .connection_dialog import ConnectionDialog
from models.user import User
from .custom_title_bar import CustomTitleBar


class ConnectionManagerDialog(QDialog):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        # ВАЖНО: Делаем независимым окном
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.current_user = user
        self.controller = ConnectionController()
        self.selected_connection = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.root_frame = QFrame()
        self.root_frame.setObjectName("RootFrame")
        self.root_frame.setStyleSheet("""
            QFrame#RootFrame {
                background-color: #1e1e2e; 
                border: 1px solid #313244; 
                border-radius: 10px;
            }
        """)

        root_layout = QVBoxLayout(self.root_frame)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, "Менеджер подключений")
        root_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)

        lbl = QLabel("Выберите сохраненное подключение:")
        lbl.setStyleSheet("color: #bac2de; font-size: 13px;")
        content_layout.addWidget(lbl)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(30, 30, 46, 0.6);
                border: 1px solid #313244;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                color: white;
            }
            QListWidget::item:selected {
                background-color: rgba(137, 180, 250, 0.2);
                border: 1px solid #89b4fa;
                border-radius: 4px;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self.accept)
        content_layout.addWidget(self.list_widget)

        buttons_layout = QHBoxLayout()

        add_button = QPushButton("Добавить новое...")
        add_button.clicked.connect(self.handle_add_connection)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        self.import_button = QPushButton("Выбрать")
        self.import_button.setProperty("role", "primary")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.accept)

        buttons_layout.addWidget(add_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.import_button)

        content_layout.addLayout(buttons_layout)

        root_layout.addWidget(content_widget)
        main_layout.addWidget(self.root_frame)

        self.resize(500, 400)

        self.list_widget.currentItemChanged.connect(self.on_selection_change)
        self.load_connections()

    def load_connections(self):
        self.list_widget.clear()
        connections = self.controller.get_connections_for_user(self.current_user.user_id)
        if not connections:
            self.list_widget.addItem("Сохраненных подключений нет. Добавьте новое.")
            self.list_widget.setEnabled(False)
            return

        self.list_widget.setEnabled(True)
        for conn in connections:
            item = QListWidgetItem(f"{conn.connection_name} ({conn.db_username}@{conn.host})")
            item.setData(Qt.UserRole, conn)
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
            self.import_button.setEnabled(True)
            self.selected_connection = current_item.data(Qt.UserRole)
        else:
            self.import_button.setEnabled(False)
            self.selected_connection = None

    def accept(self):
        if not self.selected_connection:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите подключение для импорта.")
            return
        super().accept()