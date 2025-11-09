# views/connection_dialog.py

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, QMessageBox
from utils.schema_inspector import test_mysql_connection


class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки подключения к серверу MySQL")

        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit();
        self.host_input = QLineEdit("localhost")
        self.port_input = QSpinBox();
        self.port_input.setRange(1, 65535);
        self.port_input.setValue(3306)
        self.user_input = QLineEdit("root")
        self.password_input = QLineEdit();
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Название подключения:", self.name_input)
        form_layout.addRow("Хост:", self.host_input)
        form_layout.addRow("Порт:", self.port_input)
        form_layout.addRow("Пользователь:", self.user_input)
        form_layout.addRow("Пароль:", self.password_input)

        # --- ИЗМЕНЕНИЕ: Поле "Имя БД" удалено ---

        self.layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        test_button = self.button_box.addButton("Тест", QDialogButtonBox.ActionRole)
        self.layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept);
        self.button_box.rejected.connect(self.reject)
        test_button.clicked.connect(self.handle_test_connection)
        self.setMinimumWidth(350)

    def get_data(self):
        # --- ИЗМЕНЕНИЕ: Убираем 'dbname' ---
        return {"name": self.name_input.text(), "host": self.host_input.text(), "port": self.port_input.value(),
                "user": self.user_input.text(), "password": self.password_input.text()}

    def handle_test_connection(self):
        data = self.get_data()
        if not all([data['host'], data['port'], data['user']]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля для теста.");
            return
        success, message = test_mysql_connection(data)
        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.critical(self, "Ошибка", message)

    def accept(self):
        data = self.get_data()
        if not all([data['name'], data['host'], data['port'], data['user']]):
            QMessageBox.warning(self, "Ошибка", "Все поля, кроме пароля, должны быть заполнены.");
            return
        super().accept()