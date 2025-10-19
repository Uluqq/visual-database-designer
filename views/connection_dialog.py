# views/connection_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QLabel, QSpinBox
)
from PySide6.QtCore import Qt
from utils.database_connector import DatabaseConnector  # Импорт из папки utils


class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к MySQL")
        self.db_list = None

        self.connector = DatabaseConnector()

        self.layout = QVBoxLayout(self)

        # Форма для ввода данных
        self.form_layout = QFormLayout()

        # Установим разумные значения по умолчанию для удобства
        self.host_input = QLineEdit("localhost")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(3306)
        self.user_input = QLineEdit("root")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.form_layout.addRow("Хост:", self.host_input)
        self.form_layout.addRow("Порт:", self.port_input)
        self.form_layout.addRow("Пользователь:", self.user_input)
        self.form_layout.addRow("Пароль:", self.password_input)

        self.layout.addLayout(self.form_layout)

        # Кнопки OK и Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.attempt_connection)
        self.button_box.rejected.connect(self.reject)

        self.button_box.button(QDialogButtonBox.Ok).setText("Подключиться")

        self.layout.addWidget(self.button_box)

        self.setMinimumWidth(350)

    def attempt_connection(self):
        host = self.host_input.text()
        port = self.port_input.value()
        user = self.user_input.text()
        password = self.password_input.text()

        try:
            self.db_list = self.connector.get_database_list(host, port, user, password)
            QMessageBox.information(self, "Успех", f"Успешно подключено. Найдено {len(self.db_list)} баз данных.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения", str(e))
            self.db_list = None

    def get_db_list(self):
        return self.db_list