# views/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStatusBar,
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QLabel,
    QInputDialog, QFileDialog, QFrame, QMenuBar
    # Убрал QMessageBox из импорта PySide6
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QAction, QDrag

# ... остальные импорты ...
from views.diagram_view import DiagramView
from models.user import User
from models.project import Project
from controllers.diagram_controller import DiagramController
from controllers.project_controller import ProjectController
from utils.exporters import MySqlExporter
from utils.validators import ProjectValidator
from .custom_title_bar import CustomTitleBar
import resources_rc

# --- ИМПОРТ НАШЕГО НОВОГО КЛАССА ---
from views.styled_message_box import StyledMessageBox

# ... класс DraggableTableListWidget без изменений ...
class DraggableTableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setFrameShape(QListWidget.NoFrame)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            table = item.data(Qt.UserRole)
            if table:
                mime_data = QMimeData()
                mime_data.setText(f"table_id:{table.table_id}")
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                drag.exec(Qt.MoveAction)

class MainWindow(QMainWindow):
    # ... __init__ и другие методы без изменений до handle_export_sql ...
    project_selection_requested = Signal()

    def __init__(self, user: User, project: Project):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.current_user, self.current_project = user, project
        self.diagram_controller = DiagramController()
        self.project_controller = ProjectController()
        self.current_diagram = None
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.root_frame = QFrame()
        self.root_frame.setObjectName("RootFrame")
        self.root_frame.setStyleSheet("QFrame#RootFrame { background-color: #1e1e2e; border: 1px solid #313244; }")
        layout.addWidget(self.root_frame)
        root_layout = QVBoxLayout(self.root_frame)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        title_text = f"Visual Database Designer - [{project.project_name}]"
        self.title_bar = CustomTitleBar(self, title_text, is_main_window=True)
        root_layout.addWidget(self.title_bar)
        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet("QMenuBar { background-color: #1e1e2e; border: none; border-bottom: 1px solid #313244; color: #cdd6f4; } QMenuBar::item { background: transparent; padding: 8px 12px; } QMenuBar::item:selected { background-color: rgba(137, 180, 250, 0.1); color: #ffffff; } QMenu { background-color: #1e1e2e; border: 1px solid #313244; color: #cdd6f4; } QMenu::item { padding: 5px 20px; } QMenu::item:selected { background-color: rgba(137, 180, 250, 0.2); }")
        root_layout.addWidget(self.menu_bar)
        self._setup_menu_actions()
        toolbar_container = QWidget()
        toolbar_container.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(15, 5, 15, 5)
        self.diagram_combo = QComboBox()
        self.diagram_combo.setMinimumWidth(250)
        add_diagram_button = QPushButton()
        add_diagram_button.setIcon(QIcon(":/icons/ui/icons/add.png"))
        add_diagram_button.setIconSize(QSize(20, 20))
        add_diagram_button.setFixedSize(QSize(36, 36))
        add_diagram_button.setToolTip("Создать новую диаграмму")
        add_diagram_button.setCursor(Qt.PointingHandCursor)
        add_diagram_button.setStyleSheet("QPushButton { background-color: rgba(137, 180, 250, 0.1); border: 1px solid rgba(137, 180, 250, 0.3); border-radius: 5px; } QPushButton:hover { background-color: rgba(137, 180, 250, 0.25); border: 1px solid #89b4fa; } QPushButton:pressed { background-color: rgba(137, 180, 250, 0.4); }")
        toolbar_layout.addWidget(QLabel(" ДИАГРАММА: "))
        toolbar_layout.addWidget(self.diagram_combo)
        toolbar_layout.addWidget(add_diagram_button)
        toolbar_layout.addStretch()
        root_layout.addWidget(toolbar_container)
        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(0)
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("background-color: #1e1e2e; border-right: 1px solid #313244;")
        sidebar_widget.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_header = QLabel("ТАБЛИЦЫ ПРОЕКТА")
        sidebar_header.setStyleSheet("color: #6c7086; font-weight: bold; border:none; background: transparent; margin-bottom: 5px;")
        sidebar_layout.addWidget(sidebar_header)
        self.tables_list_widget = DraggableTableListWidget()
        sidebar_layout.addWidget(self.tables_list_widget)
        view_container = QWidget()
        view_container.setStyleSheet("border: none;")
        self.diagram_view = DiagramView(view_container)
        self.diagram_view.set_controller(self.diagram_controller)
        self.diagram_view.set_main_window(self)
        self.save_button = QPushButton("СОХРАНИТЬ", view_container)
        self.save_button.setProperty("role", "primary")
        self.save_button.setFixedSize(QSize(130, 40))
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.exit_button = QPushButton("ВЫХОД", view_container)
        self.exit_button.setFixedSize(QSize(130, 40))
        self.exit_button.setCursor(Qt.PointingHandCursor)
        workspace_layout.addWidget(sidebar_widget)
        workspace_layout.addWidget(view_container, 1)
        root_layout.addLayout(workspace_layout)
        self.diagram_combo.currentIndexChanged.connect(self.handle_diagram_switch)
        add_diagram_button.clicked.connect(self.handle_create_new_diagram)
        self.save_button.clicked.connect(self.diagram_view.save_project_state)
        self.exit_button.clicked.connect(self.diagram_view.exit_to_project_selection)
        self.diagram_view.project_structure_changed.connect(self.update_project_tables_list)
        status = QStatusBar(self)
        status.setStyleSheet("background-color: #11111b; color: #bac2de; border-top: 1px solid #313244;")
        self.setStatusBar(status)
        self.update_status_bar()
        self.showMaximized()
        self.load_project_data()

    def _setup_menu_actions(self):
        file_menu = self.menu_bar.addMenu("Файл")
        export_menu = file_menu.addMenu("Экспорт")
        export_sql_action = QAction("Экспорт в SQL...", self)
        export_sql_action.triggered.connect(self.handle_export_sql)
        export_menu.addAction(export_sql_action)
        export_png_action = QAction("Экспорт в PNG...", self)
        export_png_action.triggered.connect(lambda: self.handle_export_image('png'))
        export_menu.addAction(export_png_action)
        export_jpg_action = QAction("Экспорт в JPG...", self)
        export_jpg_action.triggered.connect(lambda: self.handle_export_image('jpg'))
        export_menu.addAction(export_jpg_action)

    # --- ОБНОВЛЕННЫЙ МЕТОД ЭКСПОРТА С STYLED MESSAGE BOX ---
    def handle_export_sql(self):
        validator = ProjectValidator(self.current_project.project_id)
        is_valid = validator.validate()

        if not is_valid:
            error_text = "Невозможно экспортировать проект из-за ошибок:\n\n"
            error_text += "\n".join([f"• {err}" for err in validator.errors])
            # ЗАМЕНА QMessageBox на StyledMessageBox
            StyledMessageBox.critical(self, "Ошибка валидации", error_text)
            return

        if validator.warnings:
            warn_text = "Обнаружены потенциальные проблемы:\n\n"
            warn_text += "\n".join([f"• {warn}" for warn in validator.warnings])
            warn_text += "\n\nПродолжить экспорт?"
            # ЗАМЕНА QMessageBox на StyledMessageBox
            if not StyledMessageBox.question(self, "Предупреждение", warn_text):
                return

        all_tables = self.project_controller.get_all_tables_for_project(self.current_project.project_id)
        relationships = self.diagram_controller.get_relationships_for_project(self.current_project.project_id)

        if not all_tables:
            # ЗАМЕНА QMessageBox
            StyledMessageBox.information(self, "Экспорт", "В проекте нет таблиц для экспорта.")
            return

        default_name = f"{self.current_project.project_name}.sql"
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить SQL-скрипт", default_name, "SQL Files (*.sql)")

        if file_path:
            try:
                exporter = MySqlExporter(all_tables, relationships)
                sql_script = exporter.generate_script()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                # ЗАМЕНА QMessageBox
                StyledMessageBox.information(self, "Успех", f"SQL-скрипт успешно сохранен в:\n{file_path}")
            except Exception as e:
                # ЗАМЕНА QMessageBox
                StyledMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать или сохранить скрипт:\n{e}")

    def handle_export_image(self, img_format: str):
        if not self.current_diagram:
            StyledMessageBox.warning(self, "Экспорт", "Нет активной диаграммы для экспорта.")
            return
        default_name = f"{self.current_project.project_name}_{self.current_diagram.diagram_name}.{img_format}"
        file_path, _ = QFileDialog.getSaveFileName(self, f"Сохранить как {img_format.upper()}", default_name,
                                                   f"{img_format.upper()} Files (*.{img_format})")
        if file_path:
            success = self.diagram_view.export_as_image(file_path)
            if success:
                StyledMessageBox.information(self, "Успех", f"Изображение успешно сохранено в:\n{file_path}")
            else:
                StyledMessageBox.critical(self, "Ошибка", "Не удалось сохранить изображение.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        view_container = self.diagram_view.parentWidget()
        if view_container:
            self.diagram_view.setGeometry(0, 0, view_container.width(), view_container.height())
        button_width = 130
        margin_right = 20
        self.save_button.move(view_container.width() - button_width - margin_right, 20)
        self.exit_button.move(view_container.width() - button_width - margin_right, 70)

    def load_project_data(self):
        if not self.current_project: return
        self.update_diagrams_list()
        self.update_project_tables_list()
        self.load_current_diagram_view()

    def update_diagrams_list(self):
        self.diagram_combo.blockSignals(True)
        self.diagram_combo.clear()
        diagrams = self.diagram_controller.get_diagrams_for_project(self.current_project.project_id)
        if not diagrams:
            diagram = self.diagram_controller.create_diagram(self.current_project.project_id, "Main Diagram")
            if diagram: diagrams.append(diagram)
        for i, diagram in enumerate(diagrams):
            self.diagram_combo.addItem(diagram.diagram_name, userData=diagram)
            if self.current_diagram and self.current_diagram.diagram_id == diagram.diagram_id:
                self.diagram_combo.setCurrentIndex(i)
        if not self.current_diagram and len(diagrams) > 0:
            self.current_diagram = diagrams[0]
            self.diagram_combo.setCurrentIndex(0)
        self.diagram_combo.blockSignals(False)

    def update_project_tables_list(self):
        self.tables_list_widget.clear()
        all_tables = self.project_controller.get_all_tables_for_project(self.current_project.project_id)
        for table in all_tables:
            item = QListWidgetItem(table.table_name)
            item.setData(Qt.UserRole, table)
            self.tables_list_widget.addItem(item)

    def load_current_diagram_view(self):
        if not self.current_diagram:
            self.diagram_view.clear_diagram()
            return
        diagram_objects = self.diagram_controller.get_diagram_details(self.current_diagram.diagram_id)
        relationships = self.diagram_controller.get_relationships_for_project(self.current_project.project_id)
        self.diagram_view.load_diagram_data(self.current_diagram, diagram_objects, relationships)

    def handle_diagram_switch(self, index):
        diagram = self.diagram_combo.itemData(index)
        if diagram and (not self.current_diagram or self.current_diagram.diagram_id != diagram.diagram_id):
            self.current_diagram = diagram
            self.load_current_diagram_view()

    def handle_create_new_diagram(self):
        # Тут можно использовать стандартный InputDialog или тоже сделать кастомный, но это уже перфекционизм.
        # Для ошибок при создании - используем StyledMessageBox
        name, ok = QInputDialog.getText(self, "Новая диаграмма", "Введите имя диаграммы:")
        if ok and name:
            new_diagram = self.diagram_controller.create_diagram(self.current_project.project_id, name)
            if new_diagram:
                self.current_diagram = new_diagram
                self.load_project_data()
            else:
                StyledMessageBox.warning(self, "Ошибка", f"Диаграмма с именем '{name}' уже существует.")

    def update_status_bar(self):
        if self.current_user and self.current_project:
            self.statusBar().showMessage(
                f"Пользователь: {self.current_user.username}  |  Проект: {self.current_project.project_name}")

    def show_project_selection(self):
        self.project_selection_requested.emit()