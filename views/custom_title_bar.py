# views/custom_title_bar.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor


class CustomTitleBar(QWidget):
    def __init__(self, parent, title="", is_main_window=False):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(32)  # Компактная высота
        # Фон заголовка должен быть таким же, как у основного окна или чуть светлее
        self.setStyleSheet("background-color: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(8)

        # Заголовок
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)
        layout.addStretch()

        # Стили кнопок
        btn_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #a6adc8;
                font-weight: bold;
                font-family: monospace;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); color: white; }
        """
        close_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #a6adc8;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #f38ba8; color: white; }
        """

        self.btn_min = QPushButton("—")
        self.btn_min.setFixedSize(28, 24)
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.btn_min)

        if is_main_window:
            self.btn_max = QPushButton("□")
            self.btn_max.setFixedSize(28, 24)
            self.btn_max.setStyleSheet(btn_style)
            self.btn_max.clicked.connect(self.toggle_maximize)
            layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(28, 24)
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