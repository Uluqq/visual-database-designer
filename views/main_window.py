# views/main_window.py

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStatusBar
from PySide6.QtCore import Qt
from views.diagram_view import DiagramView
from models.user import User
from models.project import Project
from controllers.diagram_controller import DiagramController


class MainWindow(QMainWindow):
    def __init__(self, user: User, project: Project):
        super().__init__()
        self.setWindowTitle(f"Visual Database Designer - [{project.project_name}]")
        self.current_user, self.current_project = user, project
        self.diagram_controller = DiagramController()

        self.main_container = QWidget()
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.diagram_view = DiagramView()
        self.diagram_view.set_controller(self.diagram_controller)
        # --- ИСПРАВЛЕНИЕ: Передаем ссылку на главное окно ---
        self.diagram_view.set_main_window(self)

        self.main_layout.addWidget(self.diagram_view)
        self.setCentralWidget(self.main_container)

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