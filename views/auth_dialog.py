# views/auth_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox,
    QStackedWidget, QWidget, QFormLayout, QLabel
)
from PySide6.QtCore import Signal, Qt
from controllers.user_controller import UserController


class AuthDialog(QDialog):
    # Сигнал, который будет испускаться при успешной аутентификации
    # Он будет передавать объект пользователя (в нашем случае - "фальшивый")
    authenticated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход / Регистрация")
        self.setModal(True)
        self.user_controller = UserController()

        # Главный макет
        self.main_layout = QVBoxLayout(self)

        # QStackedWidget для переключения между формами входа и регистрации
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Создаем и добавляем виджеты для входа и регистрации
        self.login_widget = self._create_login_widget()
        self.register_widget = self._create_register_widget()
        self.stacked_widget.addWidget(self.login_widget)
        self.stacked_widget.addWidget(self.register_widget)

        self.setMinimumWidth(350)

    def _create_login_widget(self):
        """Создает виджет для формы входа."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_layout = QFormLayout()

        self.login_user_input = QLineEdit()
        self.login_user_input.setPlaceholderText("Имя пользователя или Email")
        self.login_password_input = QLineEdit()
        self.login_password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Логин:", self.login_user_input)
        form_layout.addRow("Пароль:", self.login_password_input)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.handle_login)

        switch_to_register_button = QPushButton("Нет аккаунта? Зарегистрироваться")
        switch_to_register_button.setStyleSheet("border: none; color: blue;")
        switch_to_register_button.setCursor(Qt.PointingHandCursor)
        switch_to_register_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addLayout(form_layout)
        layout.addWidget(login_button)
        layout.addWidget(switch_to_register_button, 0, Qt.AlignCenter)

        return widget

    def _create_register_widget(self):
        """Создает виджет для формы регистрации."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_layout = QFormLayout()

        self.reg_user_input = QLineEdit()
        self.reg_user_input.setPlaceholderText("Имя пользователя")
        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("Email")
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        self.reg_confirm_password_input = QLineEdit()
        self.reg_confirm_password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Имя:", self.reg_user_input)
        form_layout.addRow("Email:", self.reg_email_input)
        form_layout.addRow("Пароль:", self.reg_password_input)
        form_layout.addRow("Подтвердите:", self.reg_confirm_password_input)

        register_button = QPushButton("Зарегистрироваться")
        register_button.clicked.connect(self.handle_register)

        switch_to_login_button = QPushButton("Уже есть аккаунт? Войти")
        switch_to_login_button.setStyleSheet("border: none; color: blue;")
        switch_to_login_button.setCursor(Qt.PointingHandCursor)
        switch_to_login_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addLayout(form_layout)
        layout.addWidget(register_button)
        layout.addWidget(switch_to_login_button, 0, Qt.AlignCenter)

        return widget

    def handle_login(self):
        username = self.login_user_input.text()
        password = self.login_password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        user = self.user_controller.authenticate_user(username, password)
        if user:
            self.authenticated.emit(user)
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка входа", "Неверное имя пользователя или пароль.")

    def handle_register(self):
        username = self.reg_user_input.text()
        email = self.reg_email_input.text()
        password = self.reg_password_input.text()
        confirm_password = self.reg_confirm_password_input.text()

        if not all([username, email, password, confirm_password]):
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return
        if password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return

        user, message = self.user_controller.register_user(username, email, password)
        if user:
            QMessageBox.information(self, "Успех", message + "\nТеперь вы можете войти.")
            self.stacked_widget.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, "Ошибка регистрации", message)