# views/custom_title_bar.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon


class CustomTitleBar(QWidget):
    def __init__(self, parent, title="", is_main_window=False):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(32)
        self.setStyleSheet("background-color: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "color: #a6adc8; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(self.title_label)
        layout.addStretch()

        # --- СТИЛИ ДЛЯ КНОПОК С ИКОНКАМИ ---
        # Убираем текст, оставляем только иконки
        # Используем border-radius: 0 или circle, если хотите
        btn_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: rgba(255, 255, 255, 0.1); 
            }
        """

        close_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: #f38ba8; 
            }
        """

        # --- Кнопка Свернуть (remove.png) ---
        self.btn_min = QPushButton()
        self.btn_min.setFixedSize(28, 24)
        # ВАЖНО: Путь к ресурсу :icons/icons/remove.png
        # (зависит от того, как вы указали в qrc. У нас prefix="icons" и путь внутри icons/remove.png)
        self.btn_min.setIcon(QIcon(":/icons/ui/icons/remove.png"))
        self.btn_min.setIconSize(QSize(16, 16))
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.btn_min)

        if is_main_window:
            # Для развернуть пока можно оставить квадрат или текст, либо найти иконку square.png
            self.btn_max = QPushButton("□")
            self.btn_max.setFixedSize(28, 24)
            self.btn_max.setStyleSheet("""
                QPushButton { color: white; background: transparent; border: none; font-size: 16px; }
                QPushButton:hover { background: rgba(255,255,255,0.1); }
            """)
            self.btn_max.clicked.connect(self.toggle_maximize)
            layout.addWidget(self.btn_max)

        # --- Кнопка Закрыть (close.png) ---
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(28, 24)
        self.btn_close.setIcon(QIcon(":/icons/ui/icons/close.png"))
        self.btn_close.setIconSize(QSize(16, 16))
        self.btn_close.setStyleSheet(close_style)
        self.btn_close.clicked.connect(self.parent_window.close)
        layout.addWidget(self.btn_close)

        self.start_pos = None

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent_window.move(self.parent_window.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None