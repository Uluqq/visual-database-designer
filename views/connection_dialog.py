# views/connection_dialog.py

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout,
                               QLineEdit, QSpinBox, QMessageBox, QWidget, QFrame, QPushButton, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt
from utils.schema_inspector import test_mysql_connection
from .custom_title_bar import CustomTitleBar


class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ВАЖНО: Добавляем Qt.Window, чтобы диалог был самостоятельным окном, а не виджетом внутри родителя
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.root_frame = QFrame()
        # ID для CSS, чтобы фон применялся только сюда
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

        self.title_bar = CustomTitleBar(self, "Новое подключение")
        root_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Локальный MySQL")

        self.host_input = QLineEdit("localhost")

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(3306)
        self.port_input.setButtonSymbols(QSpinBox.NoButtons)  # Убираем кнопки спинбокса для чистоты

        self.user_input = QLineEdit("root")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Хелпер для красивых лейблов
        def add_styled_row(text, widget):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #bac2de; font-weight: bold; font-size: 13px;")
            form_layout.addRow(lbl, widget)

        add_styled_row("Название:", self.name_input)
        add_styled_row("Хост:", self.host_input)
        add_styled_row("Порт:", self.port_input)
        add_styled_row("Пользователь:", self.user_input)
        add_styled_row("Пароль:", self.password_input)

        content_layout.addLayout(form_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.test_button = QPushButton("Проверить")
        self.test_button.setStyleSheet("""
            QPushButton { background-color: rgba(249, 226, 175, 0.1); color: #f9e2af; border: 1px solid #f9e2af; }
            QPushButton:hover { background-color: rgba(249, 226, 175, 0.2); }
        """)
        self.test_button.clicked.connect(self.handle_test_connection)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("Сохранить")
        self.save_button.setProperty("role", "primary")
        self.save_button.clicked.connect(self.accept)

        buttons_layout.addWidget(self.test_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)

        content_layout.addLayout(buttons_layout)

        root_layout.addWidget(content_widget)
        self.main_layout.addWidget(self.root_frame)

        self.setMinimumWidth(420)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "host": self.host_input.text(),
            "port": self.port_input.value(),
            "user": self.user_input.text(),
            "password": self.password_input.text()
        }

    def handle_test_connection(self):
        data = self.get_data()
        if not all([data['host'], data['port'], data['user']]):
            QMessageBox.warning(self, "Ошибка", "Заполните хост, порт и пользователя для теста.")
            return
        success, message = test_mysql_connection(data)
        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.critical(self, "Ошибка", message)

    def accept(self):
        data = self.get_data()
        if not all([data['name'], data['host'], data['port'], data['user']]):
            QMessageBox.warning(self, "Ошибка", "Все поля, кроме пароля, должны быть заполнены.")
            return
        super().accept()