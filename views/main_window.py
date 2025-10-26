# views/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QWidget,
    QVBoxLayout, QListWidget, QLabel, QDialog, QMessageBox,
    QHBoxLayout, QToolButton, QStatusBar
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from views.diagram_view import DiagramView
from views.connection_dialog import ConnectionDialog
from utils.schema_inspector import SchemaInspector
from models.user import User
from models.project import Project
from controllers.diagram_controller import DiagramController


class MainWindow(QMainWindow):
    def __init__(self, user: User, project: Project):
        super().__init__()
        self.setWindowTitle(f"Visual Database Designer - [{project.project_name}]")
        self.current_user = user
        self.current_project = project
        self.diagram_controller = DiagramController()

        # --- Упрощаем инициализацию ---
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.diagram_view = DiagramView()
        self.diagram_view.set_controller(self.diagram_controller)
        self.main_layout.addWidget(self.diagram_view)
        self.setCentralWidget(self.main_container)

        self.setStatusBar(QStatusBar(self))
        self.update_status_bar()

        self.showMaximized()
        self.load_project_data()

    def load_project_data(self):
        """
        Загружает все данные проекта: диаграмму, таблицы и связи.
        """
        if not self.current_project:
            return

        # 1. Получаем (или создаем) основную диаграмму для проекта
        diagram = self.diagram_controller.get_or_create_diagram_for_project(self.current_project.project_id)

        # 2. Получаем все объекты (таблицы и их позиции) для этой диаграммы
        diagram_objects = self.diagram_controller.get_diagram_details(diagram.diagram_id)

        # 3. ИСПРАВЛЕНИЕ: Получаем все связи для этого проекта
        relationships = self.diagram_controller.get_relationships_for_project(self.current_project.project_id)

        # 4. Передаем ВСЕ данные (включая связи) в DiagramView для отрисовки
        self.diagram_view.load_diagram_data(diagram, diagram_objects, relationships)

        print(
            f"Загружена диаграмма '{diagram.diagram_name}'. Объектов: {len(diagram_objects)}, Связей: {len(relationships)}")

    def update_status_bar(self):
        if self.current_user and self.current_project:
            status_text = f"Пользователь: {self.current_user.username}  |  Проект: {self.current_project.project_name}"
            self.statusBar().showMessage(status_text)