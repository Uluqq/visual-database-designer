# views/main_window.py

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStatusBar, QPushButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from views.diagram_view import DiagramView
from models.user import User
from models.project import Project
from controllers.diagram_controller import DiagramController


class MainWindow(QMainWindow):
    project_selection_requested = Signal()

    def __init__(self, user: User, project: Project):
        super().__init__()
        self.setWindowTitle(f"Visual Database Designer - [{project.project_name}]")
        self.current_user, self.current_project = user, project
        self.diagram_controller = DiagramController()

        # Главный контейнер, который позволит разместить кнопки поверх вида
        self.main_container = QWidget()

        # DiagramView теперь не имеет кнопок, это просто холст
        self.diagram_view = DiagramView(self.main_container)
        self.diagram_view.set_controller(self.diagram_controller)
        self.diagram_view.set_main_window(self)

        self.setCentralWidget(self.main_container)

        # --- Создаем настоящие кнопки QPushButton ---
        self.save_button = QPushButton(self.main_container)
        self.save_button.setIcon(QIcon(':/icons/save-icon.png'))
        self.save_button.setIconSize(QSize(24, 24))
        self.save_button.setFixedSize(QSize(36, 36))
        self.save_button.setToolTip("Сохранить позиции (Ctrl+S)")
        self.save_button.setStyleSheet(
            "QPushButton { border-radius: 18px; background-color: rgba(240, 240, 240, 0.8); } QPushButton:hover { background-color: rgba(220, 235, 255, 1); }")

        self.exit_button = QPushButton(self.main_container)
        # Используем ту же иконку для примера. Замените на свою.
        self.exit_button.setIcon(QIcon(':/icons/exit-icon.png'))
        self.exit_button.setIconSize(QSize(24, 24))
        self.exit_button.setFixedSize(QSize(36, 36))
        self.exit_button.setToolTip("Выход к выбору проекта")
        self.exit_button.setStyleSheet(
            "QPushButton { border-radius: 18px; background-color: rgba(240, 240, 240, 0.8); } QPushButton:hover { background-color: rgba(220, 235, 255, 1); }")

        # --- Соединяем сигналы кнопок со слотами в DiagramView ---
        self.save_button.clicked.connect(self.diagram_view.save_project_state)
        self.exit_button.clicked.connect(self.diagram_view.exit_to_project_selection)

        self.setStatusBar(QStatusBar(self))
        self.update_status_bar()
        self.showMaximized()
        self.load_project_data()

    def load_project_data(self):
        if not self.current_project: return
        diagram = self.diagram_controller.get_or_create_diagram_for_project(self.current_project.project_id)
        diagram_objects = self.diagram_controller.get_diagram_details(diagram.diagram_id)
        relationships = self.diagram_controller.get_relationships_for_project(self.current_project.project_id)
        self.diagram_view.load_diagram_data(diagram, diagram_objects, relationships)
        print(
            f"Загружена диаграмма '{diagram.diagram_name}'. Объектов: {len(diagram_objects)}, Связей: {len(relationships)}")

    def update_status_bar(self):
        if self.current_user and self.current_project:
            self.statusBar().showMessage(
                f"Пользователь: {self.current_user.username}  |  Проект: {self.current_project.project_name}")

    def show_project_selection(self):
        """Инициирует процесс возврата к окну выбора проекта."""
        self.project_selection_requested.emit()

    def resizeEvent(self, event):
        """Этот метод вызывается при изменении размера окна. Мы используем его, чтобы кнопки оставались на месте."""
        super().resizeEvent(event)
        # Размещаем DiagramView на весь размер контейнера
        self.diagram_view.setGeometry(0, 0, self.main_container.width(), self.main_container.height())
        # Размещаем кнопки в левом верхнем углу с отступом
        self.save_button.move(15, 15)
        self.exit_button.move(15, 60)