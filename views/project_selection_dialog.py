# views/project_selection_dialog.py

from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QListWidget, QLabel, QInputDialog,
                               QMessageBox, QListWidgetItem, QFrame)
from PySide6.QtCore import Qt, Signal, QSize
from controllers.project_controller import ProjectController
from models.user import User
from .connection_manager_dialog import ConnectionManagerDialog
from utils.schema_inspector import list_databases_on_server
from .custom_title_bar import CustomTitleBar
# --- ИМПОРТ НОВОГО ДИАЛОГА ---
from .database_selection_dialog import DatabaseSelectionDialog


class ProjectListItemWidget(QWidget):
    def __init__(self, project_name, updated_date_str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)

        self.setStyleSheet("background-color: transparent;")

        self.name_label = QLabel(f"<b>{project_name}</b>")
        self.name_label.setStyleSheet("font-size: 16px; color: #ffffff; background: transparent;")

        self.date_label = QLabel(f"Обновлен: {updated_date_str}")
        self.date_label.setStyleSheet("font-size: 12px; color: #a6adc8; background: transparent;")

        layout.addWidget(self.name_label)
        layout.addWidget(self.date_label)


class ProjectSelectionDialog(QDialog):
    project_selected = Signal(object)

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.current_user = user
        self.project_controller = ProjectController()
        self.selected_project = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

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

        self.title_bar = CustomTitleBar(self, "Выбор проекта")
        root_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        welcome_label = QLabel(f"Добро пожаловать, {self.current_user.username}!")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #cdd6f4; border: none;")
        content_layout.addWidget(welcome_label)

        buttons_layout = QHBoxLayout()
        new_project_button = QPushButton("Создать новый проект")
        new_project_button.setProperty("role", "primary")
        new_project_button.setCursor(Qt.PointingHandCursor)

        import_project_button = QPushButton("Импортировать проект...")
        import_project_button.setCursor(Qt.PointingHandCursor)

        buttons_layout.addWidget(new_project_button)
        buttons_layout.addWidget(import_project_button)
        buttons_layout.addStretch()
        content_layout.addLayout(buttons_layout)

        list_label = QLabel("Последние проекты:")
        list_label.setStyleSheet("font-size: 12px; margin-top: 10px; color: #bac2de; border: none;")
        content_layout.addWidget(list_label)

        self.projects_list_widget = QListWidget()
        self.projects_list_widget.setStyleSheet("""
            QListWidget {
                border: none; 
                background-color: rgba(24, 24, 37, 0.8); 
                border-radius: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        content_layout.addWidget(self.projects_list_widget)

        root_layout.addWidget(content_widget)
        main_layout.addWidget(self.root_frame)

        new_project_button.clicked.connect(self.handle_new_project)
        import_project_button.clicked.connect(self.handle_import_project)
        self.projects_list_widget.itemDoubleClicked.connect(self.handle_open_project)

        self.resize(650, 500)
        self.load_projects()

    def load_projects(self):
        self.projects_list_widget.clear()
        projects = self.project_controller.get_projects_for_user(self.current_user.user_id)
        if not projects:
            self.projects_list_widget.addItem("Проектов пока нет. Создайте новый!")
            self.projects_list_widget.setEnabled(False)
            return
        self.projects_list_widget.setEnabled(True)
        for proj in projects:
            updated_str = proj.updated_at.strftime('%Y-%m-%d %H:%M') if proj.updated_at else "N/A"
            item = QListWidgetItem(self.projects_list_widget)
            item_widget = ProjectListItemWidget(proj.project_name, updated_str)
            sz = item_widget.sizeHint()
            item.setSizeHint(QSize(sz.width(), sz.height() + 10))

            self.projects_list_widget.setItemWidget(item, item_widget)
            item.setData(Qt.UserRole, proj)

    def handle_new_project(self):
        project_name, ok = QInputDialog.getText(self, "Новый проект", "Введите имя проекта:")
        if ok and project_name:
            self.project_controller.create_project(user_id=self.current_user.user_id,
                                                   project_name=project_name)
            self.load_projects()
        elif ok and not project_name:
            QMessageBox.warning(self, "Ошибка", "Имя проекта не может быть пустым.")

    def handle_import_project(self):
        manager_dialog = ConnectionManagerDialog(self.current_user, self)
        if manager_dialog.exec() != QDialog.Accepted: return

        connection = manager_dialog.selected_connection
        if not connection: return

        databases, error = list_databases_on_server(connection)
        if error:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список БД:\n{error}")
            return
        if not databases:
            QMessageBox.warning(self, "Внимание", "На сервере нет доступных БД.")
            return

        # --- ИСПОЛЬЗУЕМ НОВЫЙ ДИАЛОГ ВМЕСТО QInputDialog ---
        db_selection_dialog = DatabaseSelectionDialog(databases, self)
        if db_selection_dialog.exec() == QDialog.Accepted:
            db_name = db_selection_dialog.get_selected_db()
            if db_name:
                QMessageBox.information(self, "Импорт", f"Начинаем импорт схемы '{db_name}'...")
                project, message = self.project_controller.import_project_from_db(
                    self.current_user.user_id, connection, db_name
                )
                if project:
                    QMessageBox.information(self, "Успех", message)
                    self.load_projects()
                else:
                    QMessageBox.critical(self, "Ошибка импорта", message)

    def handle_open_project(self, item: QListWidgetItem):
        project = item.data(Qt.UserRole)
        if project:
            self.selected_project = project
            self.project_selected.emit(self.selected_project)
            self.accept()