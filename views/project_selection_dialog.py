# views/project_selection_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QInputDialog, QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from controllers.project_controller import ProjectController
from models.user import User  # <-- Импортируем настоящую модель


class ProjectSelectionDialog(QDialog):
    project_selected = Signal(object)

    def __init__(self, user: User, parent=None):  # <-- Указываем тип для user
        super().__init__(parent)
        self.setWindowTitle("Выбор проекта")
        self.setMinimumSize(600, 400)

        self.current_user = user
        # --- ИЗМЕНЕНИЕ: Берем реальный ID из объекта пользователя ---
        self.current_user_id = self.current_user.user_id

        self.project_controller = ProjectController()
        self.selected_project = None

        self.main_layout = QVBoxLayout(self)
        title_label = QLabel(f"Добро пожаловать, {self.current_user.username}!")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.main_layout.addWidget(title_label)

        buttons_layout = QHBoxLayout()
        new_project_button = QPushButton("Создать новый проект")
        import_project_button = QPushButton("Импортировать проект")
        import_project_button.setEnabled(False)
        buttons_layout.addWidget(new_project_button)
        buttons_layout.addWidget(import_project_button)
        buttons_layout.addStretch()
        self.main_layout.addLayout(buttons_layout)

        list_label = QLabel("Последние проекты:")
        list_label.setStyleSheet("font-size: 10pt; margin-top: 10px;")
        self.projects_list_widget = QListWidget()
        self.projects_list_widget.setStyleSheet("font-size: 12pt;")
        self.main_layout.addWidget(list_label)
        self.main_layout.addWidget(self.projects_list_widget)

        new_project_button.clicked.connect(self.handle_new_project)
        self.projects_list_widget.itemDoubleClicked.connect(self.handle_open_project)

        self.load_projects()

    def load_projects(self):
        self.projects_list_widget.clear()
        projects = self.project_controller.get_projects_for_user(self.current_user_id)

        if not projects:
            self.projects_list_widget.addItem("Проектов пока нет. Создайте новый!")
            self.projects_list_widget.setEnabled(False)
            return

        self.projects_list_widget.setEnabled(True)
        for proj in projects:
            item = QListWidgetItem(f"{proj.project_name}\n{proj.description or 'Без описания'}")
            item.setData(Qt.UserRole, proj)
            self.projects_list_widget.addItem(item)

    def handle_new_project(self):
        project_name, ok = QInputDialog.getText(self, "Новый проект", "Введите имя проекта:")
        if ok and project_name:
            self.project_controller.create_project(
                user_id=self.current_user_id,
                project_name=project_name
            )
            self.load_projects()
        elif ok and not project_name:
            QMessageBox.warning(self, "Ошибка", "Имя проекта не может быть пустым.")

    def handle_open_project(self, item: QListWidgetItem):
        project = item.data(Qt.UserRole)
        if project:
            self.selected_project = project
            self.project_selected.emit(self.selected_project)
            self.accept()

    def get_selected_project(self):
        return self.selected_project