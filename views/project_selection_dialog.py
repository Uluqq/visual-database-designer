# views/project_selection_dialog.py

from PySide6.QtWidgets import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, \
    QInputDialog, QMessageBox, QListWidgetItem
from PySide6.QtCore import Qt, Signal
from controllers.project_controller import ProjectController
from models.user import User
from .connection_manager_dialog import ConnectionManagerDialog
# --- ИЗМЕНЕНИЕ: Импортируем новую утилиту ---
from utils.schema_inspector import list_databases_on_server


class ProjectListItemWidget(QWidget):
    # ... (без изменений)
    def __init__(self, project_name, updated_date_str, parent=None):
        super().__init__(parent);
        layout = QHBoxLayout(self);
        layout.setContentsMargins(5, 5, 5, 5)
        self.name_label = QLabel(f"<b>{project_name}</b>");
        self.name_label.setStyleSheet("font-size: 13pt;")
        self.date_label = QLabel(f"Обновлен: {updated_date_str}");
        self.date_label.setStyleSheet("font-size: 10pt; color: #888;")
        layout.addWidget(self.name_label);
        layout.addStretch();
        layout.addWidget(self.date_label)


class ProjectSelectionDialog(QDialog):
    project_selected = Signal(object)

    def __init__(self, user: User, parent=None):
        super().__init__(parent);
        self.setWindowTitle("Выбор проекта");
        self.setMinimumSize(600, 400)
        self.current_user = user;
        self.project_controller = ProjectController();
        self.selected_project = None
        self.main_layout = QVBoxLayout(self)
        title_label = QLabel(f"Добро пожаловать, {self.current_user.username}!");
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.main_layout.addWidget(title_label)
        buttons_layout = QHBoxLayout();
        new_project_button = QPushButton("Создать новый проект");
        import_project_button = QPushButton("Импортировать проект...")
        buttons_layout.addWidget(new_project_button);
        buttons_layout.addWidget(import_project_button);
        buttons_layout.addStretch()
        self.main_layout.addLayout(buttons_layout)
        list_label = QLabel("Последние проекты:");
        list_label.setStyleSheet("font-size: 10pt; margin-top: 10px;")
        self.projects_list_widget = QListWidget();
        self.projects_list_widget.setStyleSheet("QListWidget::item { border: none; }")
        self.main_layout.addWidget(list_label);
        self.main_layout.addWidget(self.projects_list_widget)
        new_project_button.clicked.connect(self.handle_new_project)
        import_project_button.clicked.connect(self.handle_import_project)
        self.projects_list_widget.itemDoubleClicked.connect(self.handle_open_project)
        self.load_projects()

    def load_projects(self):
        self.projects_list_widget.clear();
        projects = self.project_controller.get_projects_for_user(self.current_user.user_id)
        if not projects:
            self.projects_list_widget.addItem("Проектов пока нет. Создайте новый!");
            self.projects_list_widget.setEnabled(False);
            return
        self.projects_list_widget.setEnabled(True)
        for proj in projects:
            updated_str = proj.updated_at.strftime('%Y-%m-%d %H:%M') if proj.updated_at else "N/A"
            item = QListWidgetItem(self.projects_list_widget)
            item_widget = ProjectListItemWidget(proj.project_name, updated_str)
            item.setSizeHint(item_widget.sizeHint());
            self.projects_list_widget.setItemWidget(item, item_widget)
            item.setData(Qt.UserRole, proj)

    def handle_new_project(self):
        project_name, ok = QInputDialog.getText(self, "Новый проект", "Введите имя проекта:")
        if ok and project_name:
            self.project_controller.create_project(user_id=self.current_user.user_id,
                                                   project_name=project_name); self.load_projects()
        elif ok and not project_name:
            QMessageBox.warning(self, "Ошибка", "Имя проекта не может быть пустым.")

    # --- ИЗМЕНЕНИЕ: Полностью переписанный метод импорта ---
    def handle_import_project(self):
        manager_dialog = ConnectionManagerDialog(self.current_user, self)
        if manager_dialog.exec() != QDialog.Accepted: return

        connection = manager_dialog.selected_connection
        if not connection: return

        # 1. Получаем список БД с сервера
        databases, error = list_databases_on_server(connection)
        if error:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список баз данных:\n{error}");
            return
        if not databases:
            QMessageBox.warning(self, "Внимание", "На сервере не найдено доступных баз данных.");
            return

        # 2. Показываем пользователю диалог выбора БД
        db_name, ok = QInputDialog.getItem(self, "Выбор базы данных", "Выберите базу данных для импорта:", databases, 0,
                                           False)

        # 3. Если пользователь выбрал БД и нажал ОК, запускаем импорт
        if ok and db_name:
            QMessageBox.information(self, "Импорт",
                                    f"Начинаем импорт схемы '{db_name}'. Это может занять некоторое время...")
            project, message = self.project_controller.import_project_from_db(
                self.current_user.user_id, connection, db_name
            )
            if project:
                QMessageBox.information(self, "Успех", message);
                self.load_projects()
            else:
                QMessageBox.critical(self, "Ошибка импорта", message)

    def handle_open_project(self, item: QListWidgetItem):
        project = item.data(Qt.UserRole);
        if project: self.selected_project = project; self.project_selected.emit(self.selected_project); self.accept()

    def get_selected_project(self):
        return self.selected_project