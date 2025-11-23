# views/database_selection_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox,
                               QPushButton, QHBoxLayout, QWidget, QFrame)
from PySide6.QtCore import Qt
from .custom_title_bar import CustomTitleBar


class DatabaseSelectionDialog(QDialog):
    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # --- Основной слой ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Рамка и фон ---
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

        # 1. Заголовок
        self.title_bar = CustomTitleBar(self, "Выбор БД")
        root_layout.addWidget(self.title_bar)

        # 2. Контент
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        lbl = QLabel("Выберите базу данных для импорта:")
        lbl.setStyleSheet("color: #bac2de; font-size: 14px;")
        content_layout.addWidget(lbl)

        self.combo_box = QComboBox()
        self.combo_box.addItems(items)
        # Стили уже подтянутся из main.py, но можно уточнить высоту
        self.combo_box.setMinimumHeight(35)
        content_layout.addWidget(self.combo_box)

        # 3. Кнопки
        buttons_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton("Импортировать")
        self.ok_btn.setProperty("role", "primary")
        self.ok_btn.clicked.connect(self.accept)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.ok_btn)

        content_layout.addLayout(buttons_layout)

        root_layout.addWidget(content_widget)
        main_layout.addWidget(self.root_frame)

        self.resize(400, 200)

    def get_selected_db(self):
        return self.combo_box.currentText()