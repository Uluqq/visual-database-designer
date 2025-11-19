# views/auth_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox,
    QStackedWidget, QWidget, QLabel, QFrame
)
from PySide6.QtCore import Signal, Qt
from controllers.user_controller import UserController
from .custom_title_bar import CustomTitleBar


class AuthDialog(QDialog):
    authenticated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Настройки прозрачности окна
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.user_controller = UserController()
        self.current_user = None

        self.setMinimumWidth(400)
        self.setMinimumHeight(450)  # Увеличил высоту, чтобы влезло все

        # Главный лейаут диалога (прозрачный)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Отступ для тени (если захотим добавить)

        # --- ГЛАВНЫЙ КОНТЕЙНЕР (Рамка окна) ---
        self.root_frame = QFrame()
        # Задаем фон и границу здесь, а не глобально
        self.root_frame.setStyleSheet("""
            QFrame#RootFrame {
                background-color: #1e1e2e; 
                border: 1px solid #313244; 
                border-radius: 10px;
            }
        """)
        self.root_frame.setObjectName("RootFrame")

        # Лейаут внутри рамки
        root_layout = QVBoxLayout(self.root_frame)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Добавляем кастомный заголовок
        self.title_bar = CustomTitleBar(self, "Доступ к системе")
        root_layout.addWidget(self.title_bar)

        # 2. Контентная часть
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 20, 40, 40)  # Внутренние отступы
        content_layout.setSpacing(20)

        # Заголовок "ВХОД В СИСТЕМУ"
        header_lbl = QLabel("ВХОД В СИСТЕМУ")
        header_lbl.setAlignment(Qt.AlignCenter)
        header_lbl.setStyleSheet(
            "color: #89b4fa; font-size: 20px; font-weight: bold; letter-spacing: 2px; margin-bottom: 10px;")
        content_layout.addWidget(header_lbl)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        root_layout.addWidget(content_widget)
        main_layout.addWidget(self.root_frame)

        self.login_widget = self._create_login_widget()
        self.register_widget = self._create_register_widget()
        self.stacked_widget.addWidget(self.login_widget)
        self.stacked_widget.addWidget(self.register_widget)

    def _create_login_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        self.login_user_input = QLineEdit()
        self.login_user_input.setPlaceholderText("Логин или Email")

        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Пароль")
        self.login_password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.login_user_input)
        layout.addWidget(self.login_password_input)

        layout.addSpacing(10)

        login_button = QPushButton("ВОЙТИ")
        login_button.setProperty("role", "primary")
        login_button.setCursor(Qt.PointingHandCursor)
        login_button.clicked.connect(self.handle_login)

        switch_to_register_button = QPushButton("Нет аккаунта? Регистрация")
        switch_to_register_button.setFlat(True)
        switch_to_register_button.setStyleSheet(
            "color: #a6adc8; border: none; text-decoration: underline; text-align: center;")
        switch_to_register_button.setCursor(Qt.PointingHandCursor)
        switch_to_register_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addWidget(login_button)
        layout.addWidget(switch_to_register_button, 0, Qt.AlignCenter)
        layout.addStretch()  # Сдвигаем все вверх
        return widget

    def _create_register_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        self.reg_user_input = QLineEdit()
        self.reg_user_input.setPlaceholderText("Имя пользователя")

        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("Email")

        self.reg_password_input = QLineEdit()
        self.reg_password_input.setPlaceholderText("Пароль")
        self.reg_password_input.setEchoMode(QLineEdit.Password)

        self.reg_confirm_password_input = QLineEdit()
        self.reg_confirm_password_input.setPlaceholderText("Подтвердите пароль")
        self.reg_confirm_password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.reg_user_input)
        layout.addWidget(self.reg_email_input)
        layout.addWidget(self.reg_password_input)
        layout.addWidget(self.reg_confirm_password_input)

        layout.addSpacing(10)

        register_button = QPushButton("ЗАРЕГИСТРИРОВАТЬСЯ")
        register_button.setProperty("role", "primary")
        register_button.clicked.connect(self.handle_register)

        switch_to_login_button = QPushButton("Назад ко входу")
        switch_to_login_button.setFlat(True)
        switch_to_login_button.setStyleSheet("color: #a6adc8; border: none; text-decoration: underline;")
        switch_to_login_button.setCursor(Qt.PointingHandCursor)
        switch_to_login_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addWidget(register_button)
        layout.addWidget(switch_to_login_button, 0, Qt.AlignCenter)
        layout.addStretch()
        return widget

    def handle_login(self):
        username = self.login_user_input.text()
        password = self.login_password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return
        user = self.user_controller.authenticate_user(username, password)
        if user:
            self.current_user = user
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