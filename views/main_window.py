# views/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStatusBar,
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QLabel,
    QInputDialog, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QAction, QImage, QPainter, QDrag
from views.diagram_view import DiagramView
from models.user import User
from models.project import Project
from controllers.diagram_controller import DiagramController
from controllers.project_controller import ProjectController
from utils.exporters import MySqlExporter


class DraggableTableListWidget(QListWidget):
    """Кастомный QListWidget с реализацией начала Drag-and-Drop."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

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
    project_selection_requested = Signal()

    def __init__(self, user: User, project: Project):
        super().__init__()
        self.setWindowTitle(f"Visual Database Designer - [{project.project_name}]")
        self.current_user, self.current_project = user, project
        self.diagram_controller = DiagramController()
        self.project_controller = ProjectController()
        self.current_diagram = None

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        toolbar_layout = QHBoxLayout()
        self.diagram_combo = QComboBox()
        self.diagram_combo.setMinimumWidth(200)
        add_diagram_button = QPushButton("+")
        add_diagram_button.setFixedSize(QSize(30, 30))
        add_diagram_button.setToolTip("Создать новую диаграмму")
        toolbar_layout.addWidget(QLabel("Диаграмма:"))
        toolbar_layout.addWidget(self.diagram_combo)
        toolbar_layout.addWidget(add_diagram_button)
        toolbar_layout.addStretch()

        workspace_layout = QHBoxLayout()
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.addWidget(QLabel("Таблицы проекта:"))
        self.tables_list_widget = DraggableTableListWidget()
        sidebar_layout.addWidget(self.tables_list_widget)
        sidebar_widget.setFixedWidth(200)

        view_container = QWidget()
        self.diagram_view = DiagramView(view_container)
        self.diagram_view.set_controller(self.diagram_controller)
        self.diagram_view.set_main_window(self)

        self.save_button = QPushButton(view_container)
        self.save_button.setIcon(QIcon(':/icons/save-icon.png'))
        self.save_button.setIconSize(QSize(24, 24))
        self.save_button.setFixedSize(QSize(36, 36))
        self.save_button.setToolTip("Сохранить (Ctrl+S)")

        self.exit_button = QPushButton(view_container)
        self.exit_button.setIcon(QIcon(':/icons/exit-icon.png'))
        self.exit_button.setIconSize(QSize(24, 24))
        self.exit_button.setFixedSize(QSize(36, 36))
        self.exit_button.setToolTip("Выход к выбору проекта")

        workspace_layout.addWidget(sidebar_widget)
        workspace_layout.addWidget(view_container)
        main_layout.addLayout(toolbar_layout)
        main_layout.addLayout(workspace_layout)

        self.diagram_combo.currentIndexChanged.connect(self.handle_diagram_switch)
        add_diagram_button.clicked.connect(self.handle_create_new_diagram)
        self.save_button.clicked.connect(self.diagram_view.save_project_state)
        self.exit_button.clicked.connect(self.diagram_view.exit_to_project_selection)
        self.diagram_view.project_structure_changed.connect(self.update_project_tables_list)

        self._create_menu_bar()

        self.setStatusBar(QStatusBar(self))
        self.update_status_bar()
        self.showMaximized()
        self.load_project_data()

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")
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

    def handle_export_sql(self):
        all_tables = self.project_controller.get_all_tables_for_project(self.current_project.project_id)
        relationships = self.diagram_controller.get_relationships_for_project(self.current_project.project_id)

        if not all_tables:
            QMessageBox.information(self, "Экспорт", "В проекте нет таблиц для экспорта.")
            return

        default_name = f"{self.current_project.project_name}.sql"
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить SQL-скрипт", default_name, "SQL Files (*.sql)")

        if file_path:
            try:
                exporter = MySqlExporter(all_tables, relationships)
                sql_script = exporter.generate_script()

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sql_script)

                QMessageBox.information(self, "Успех", f"SQL-скрипт успешно сохранен в:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать или сохранить скрипт:\n{e}")

    def handle_export_image(self, img_format: str):
        if not self.current_diagram:
            QMessageBox.warning(self, "Экспорт", "Нет активной диаграммы для экспорта.")
            return

        default_name = f"{self.current_project.project_name}_{self.current_diagram.diagram_name}.{img_format}"
        file_path, _ = QFileDialog.getSaveFileName(self, f"Сохранить как {img_format.upper()}", default_name,
                                                   f"{img_format.upper()} Files (*.{img_format})")

        if file_path:
            success = self.diagram_view.export_as_image(file_path)
            if success:
                QMessageBox.information(self, "Успех", f"Изображение успешно сохранено в:\n{file_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить изображение.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        view_container = self.diagram_view.parentWidget()
        if view_container:
            self.diagram_view.setGeometry(0, 0, view_container.width(), view_container.height())
        self.save_button.move(15, 15)
        self.exit_button.move(15, 60)

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
        print(
            f"Загружена диаграмма '{self.current_diagram.diagram_name}'. Объектов: {len(diagram_objects)}, Связей: {len(relationships)}")

    def handle_diagram_switch(self, index):
        diagram = self.diagram_combo.itemData(index)
        if diagram and (not self.current_diagram or self.current_diagram.diagram_id != diagram.diagram_id):
            self.current_diagram = diagram
            self.load_current_diagram_view()

    def handle_create_new_diagram(self):
        name, ok = QInputDialog.getText(self, "Новая диаграмма", "Введите имя диаграммы:")
        if ok and name:
            new_diagram = self.diagram_controller.create_diagram(self.current_project.project_id, name)
            if new_diagram:
                self.current_diagram = new_diagram
                self.load_project_data()
            else:
                QMessageBox.warning(self, "Ошибка", f"Диаграмма с именем '{name}' уже существует.")

    def update_status_bar(self):
        if self.current_user and self.current_project:
            self.statusBar().showMessage(
                f"Пользователь: {self.current_user.username}  |  Проект: {self.current_project.project_name}")

    def show_project_selection(self):
        self.project_selection_requested.emit()