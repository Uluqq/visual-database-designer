# views/styled_message_box.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QWidget, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from .custom_title_bar import CustomTitleBar


class StyledMessageBox(QDialog):
    ICON_INFO = "ℹ️"
    ICON_WARNING = "⚠️"
    ICON_ERROR = "❌"
    ICON_QUESTION = "❓"

    def __init__(self, title, text, icon, buttons, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Основной контейнер
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Рамка и фон
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

        # 1. Кастомный заголовок
        self.title_bar = CustomTitleBar(self, title)
        root_layout.addWidget(self.title_bar)

        # 2. Контент
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)

        # Иконка (текстовая или картинка)
        if icon:
            icon_label = QLabel(icon)
            # Увеличим шрифт для эмодзи-иконки
            icon_label.setStyleSheet("font-size: 40px; background: transparent; border: none;")
            icon_label.setAlignment(Qt.AlignTop)
            content_layout.addWidget(icon_label)

        # Текст сообщения
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #cdd6f4; font-size: 14px; background: transparent; border: none;")
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        content_layout.addWidget(text_label, 1)  # Stretch factor 1

        root_layout.addWidget(content_widget)

        # 3. Кнопки
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 0, 20, 20)
        button_layout.setSpacing(10)
        button_layout.addStretch()

        self.clicked_button = None

        for btn_text, role in buttons:
            btn = QPushButton(btn_text)
            btn.setMinimumWidth(100)
            btn.setMinimumHeight(35)
            btn.setCursor(Qt.PointingHandCursor)

            if role == "accept":
                btn.setProperty("role", "primary")  # Розовый стиль
                btn.setDefault(True)
                btn.clicked.connect(self.accept)
            else:
                btn.clicked.connect(self.reject)

            button_layout.addWidget(btn)

        root_layout.addWidget(button_container)
        main_layout.addWidget(self.root_frame)

        # Адаптивный размер, но не меньше
        self.setMinimumWidth(400)
        self.setMaximumWidth(600)

    # --- Статические методы для удобного вызова (как у QMessageBox) ---

    @staticmethod
    def information(parent, title, text):
        dlg = StyledMessageBox(title, text, StyledMessageBox.ICON_INFO, [("OK", "accept")], parent)
        dlg.exec()

    @staticmethod
    def warning(parent, title, text):
        dlg = StyledMessageBox(title, text, StyledMessageBox.ICON_WARNING, [("OK", "accept")], parent)
        dlg.exec()

    @staticmethod
    def critical(parent, title, text):
        dlg = StyledMessageBox(title, text, StyledMessageBox.ICON_ERROR, [("OK", "accept")], parent)
        dlg.exec()

    @staticmethod
    def question(parent, title, text):
        """Возвращает True, если нажали 'Да', и False, если 'Нет'"""
        dlg = StyledMessageBox(title, text, StyledMessageBox.ICON_QUESTION, [("Да", "accept"), ("Нет", "reject")],
                               parent)
        return dlg.exec() == QDialog.Accepted