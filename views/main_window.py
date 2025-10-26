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

# --- НОВЫЙ ИМПОРТ ---
from controllers.diagram_controller import DiagramController


class MainWindow(QMainWindow):
    def __init__(self, user: User, project: Project):
        super().__init__()
        self.setWindowTitle(f"Visual Database Designer - [{project.project_name}]")
        self.current_user = user
        self.current_project = project

        self.diagram_controller = DiagramController()

        self.connection_params = {}
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.init_db_list_panel()

        self.diagram_view = DiagramView()
        self.diagram_view.set_controller(self.diagram_controller)
        self.main_layout.addWidget(self.diagram_view)
        self.setCentralWidget(self.main_container)

        toolbar = QToolBar("Главная панель")
        self.addToolBar(toolbar)

        # --- ИСПРАВЛЕНИЕ: ЭТИ ТРИ СТРОКИ УДАЛЕНЫ ---
        # add_table_action = QAction(QIcon(), "Добавить таблицу", self)
        # add_table_action.triggered.connect(lambda: self.diagram_view.add_table_at(None))
        # toolbar.addAction(add_table_action)
        # ----------------------------------------------

        connect_action = QAction(QIcon(), "Подключиться к БД", self)
        connect_action.triggered.connect(self.show_connection_dialog)
        toolbar.addAction(connect_action)

        self.setStatusBar(QStatusBar(self))
        self.update_status_bar()

        self.showMaximized()

        self.load_project_data()

    def load_project_data(self):
        """Загружает данные диаграммы для текущего проекта."""
        if not self.current_project:
            return

        diagram = self.diagram_controller.get_or_create_diagram_for_project(self.current_project.project_id)
        diagram_objects = self.diagram_controller.get_diagram_details(diagram.diagram_id)

        self.diagram_view.load_diagram_data(diagram, diagram_objects)
        print(
            f"Загружена диаграмма '{diagram.diagram_name}' для проекта '{self.current_project.project_name}'. Найдено объектов: {len(diagram_objects)}")

    def update_status_bar(self):
        if self.current_user and self.current_project:
            status_text = f"Пользователь: {self.current_user.username}  |  Проект: {self.current_project.project_name}"
            self.statusBar().showMessage(status_text)

    def init_db_list_panel(self):
        self.db_panel_container = QWidget()
        self.db_panel_layout = QVBoxLayout(self.db_panel_container)
        self.db_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.db_panel_container.setVisible(False)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.db_list_label = QLabel("Доступные базы данных (Двойной клик для загрузки схемы):")
        self.toggle_button = QToolButton()
        self.toggle_button.setText("Скрыть")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self.toggle_db_list_visibility)
        header_layout.addWidget(self.db_list_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.toggle_button)
        self.db_list_widget = QListWidget()
        self.db_list_widget.setMaximumHeight(200)
        self.db_list_widget.itemDoubleClicked.connect(self.start_reverse_engineering)
        self.db_panel_layout.addWidget(header_widget)
        self.db_panel_layout.addWidget(self.db_list_widget)
        self.main_layout.addWidget(self.db_panel_container)

    def toggle_db_list_visibility(self, checked):
        if checked:
            self.db_list_widget.setVisible(False)
            self.db_list_label.setVisible(False)
            self.toggle_button.setText("Показать")
        else:
            self.db_list_widget.setVisible(True)
            self.db_list_label.setVisible(True)
            self.toggle_button.setText("Скрыть")

    def display_database_list(self, db_list):
        self.db_list_widget.clear()
        filtered_db_list = [db for db in db_list if
                            db not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
        self.db_list_widget.addItems(filtered_db_list)
        self.db_panel_container.setVisible(True)
        self.db_list_widget.setVisible(True)
        self.db_list_label.setVisible(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setText("Скрыть")
        print(f"Доступные пользовательские БД: {filtered_db_list}")

    def show_connection_dialog(self):
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            db_list = dialog.get_db_list()
            if db_list:
                self.connection_params = {
                    'host': dialog.host_input.text(),
                    'port': dialog.port_input.value(),
                    'user': dialog.user_input.text(),
                    'password': dialog.password_input.text()
                }
                self.display_database_list(db_list)

    def start_reverse_engineering(self, item):
        db_name = item.text()
        if not self.connection_params:
            QMessageBox.warning(self, "Ошибка", "Сначала необходимо установить соединение с сервером.")
            return
        try:
            QMessageBox.information(self, "Загрузка", f"Загрузка схемы для '{db_name}'...", QMessageBox.NoButton)
            inspector = SchemaInspector(
                db_name=db_name,
                **self.connection_params
            )
            schema_data = inspector.inspect_schema()
            self.diagram_view.load_schema(schema_data)
            QMessageBox.information(self, "Готово",
                                    f"Схема БД '{db_name}' успешно загружена. Найдено {len(schema_data['tables'])} таблиц и {len(schema_data['foreign_keys'])} связей.")
            self.toggle_button.setChecked(True)
            self.toggle_db_list_visibility(True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка инспекции схемы", str(e))