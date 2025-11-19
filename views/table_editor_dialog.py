# views/table_editor_dialog.py

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QWidget,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QComboBox, QCheckBox, QAbstractItemView, QMessageBox, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QSize
from controllers.table_controller import TableController
from .index_editor_dialog import IndexEditorDialog
from models.table import DbIndex
from .custom_title_bar import CustomTitleBar


class TableEditorDialog(QDialog):
    DATA_TYPES = ["integer", "varchar", "text", "boolean", "date", "timestamp", "numeric"]

    def __init__(self, table_id, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.table_id = table_id
        self.controller = TableController()

        # Глобальный лейаут
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- КОРНЕВОЙ ФРЕЙМ ---
        self.root_frame = QFrame()
        self.root_frame.setStyleSheet("""
            QFrame#RootFrame {
                background-color: #1e1e2e; 
                border: 1px solid #313244; 
                border-radius: 10px;
            }
        """)
        self.root_frame.setObjectName("RootFrame")

        root_layout = QVBoxLayout(self.root_frame)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Кастомный заголовок
        self.title_bar = CustomTitleBar(self, "Редактор таблицы")
        root_layout.addWidget(self.title_bar)

        # 2. Контент
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)

        self.tab_widget = QTabWidget()
        content_layout.addWidget(self.tab_widget)

        self.columns_widget = self._create_columns_tab()
        self.indexes_widget = self._create_indexes_tab()
        self.notes_widget = self._create_notes_tab()

        self.tab_widget.addTab(self.columns_widget, "Колонки")
        self.tab_widget.addTab(self.indexes_widget, "Индексы")
        self.tab_widget.addTab(self.notes_widget, "Заметки")

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)

        ok_btn = button_box.button(QDialogButtonBox.Ok)
        ok_btn.setProperty("role", "primary")

        content_layout.addWidget(button_box)
        root_layout.addWidget(content_widget)
        main_layout.addWidget(self.root_frame)

        self.setMinimumSize(850, 600)
        self._load_all_data()

    def _create_columns_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.cols_table = QTableWidget()
        self.cols_table.setColumnCount(6)
        self.cols_table.setHorizontalHeaderLabels(["Имя", "Тип", "PK", "NN", "UQ", "По умолч."])
        self.cols_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cols_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cols_table.setStyleSheet("border: none;")
        layout.addWidget(self.cols_table)

        buttons_layout = QHBoxLayout()
        add_col_button = QPushButton("Добавить")
        remove_col_button = QPushButton("Удалить")
        buttons_layout.addStretch()
        buttons_layout.addWidget(add_col_button)
        buttons_layout.addWidget(remove_col_button)
        layout.addLayout(buttons_layout)
        add_col_button.clicked.connect(self._add_column_row)
        remove_col_button.clicked.connect(self._remove_column_row)
        return widget

    # --- ОСТАЛЬНЫЕ МЕТОДЫ БЕЗ ИЗМЕНЕНИЙ (кроме отступов в create_indexes_tab) ---
    def _create_indexes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.indexes_table = QTableWidget()
        self.indexes_table.setColumnCount(3)
        self.indexes_table.setHorizontalHeaderLabels(["Имя", "Тип", "Колонки"])
        self.indexes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.indexes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.indexes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.indexes_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.indexes_table.setStyleSheet("border: none;")
        layout.addWidget(self.indexes_table)
        buttons_layout = QHBoxLayout()
        add_idx_button = QPushButton("Добавить...")
        edit_idx_button = QPushButton("Редактировать...")
        remove_idx_button = QPushButton("Удалить")
        buttons_layout.addStretch()
        buttons_layout.addWidget(add_idx_button)
        buttons_layout.addWidget(edit_idx_button)
        buttons_layout.addWidget(remove_idx_button)
        layout.addLayout(buttons_layout)
        add_idx_button.clicked.connect(self.handle_add_index)
        edit_idx_button.clicked.connect(self.handle_edit_index)
        remove_idx_button.clicked.connect(self.handle_delete_index)
        return widget

    def _create_notes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.notes_text_edit = QTextEdit()
        self.notes_text_edit.setPlaceholderText("Введите здесь описание таблицы...")
        layout.addWidget(self.notes_text_edit)
        return widget

    def _center_widget_in_cell(self, table, row, col, widget):
        cell_widget = QWidget()
        layout = QHBoxLayout(cell_widget)
        layout.addWidget(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        table.setCellWidget(row, col, cell_widget)

    def _load_all_data(self):
        table_data = self.controller.get_table_details(self.table_id)
        if not table_data:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные для таблицы ID={self.table_id}")
            self.reject()
            return
        self._load_columns(list(table_data.columns))
        self._load_indexes(list(table_data.indexes))
        self.notes_text_edit.setText(table_data.notes or "")

    def _load_columns(self, columns):
        columns.sort(key=lambda c: c.column_id)
        self.cols_table.setRowCount(len(columns))
        for row, col in enumerate(columns):
            self.cols_table.setVerticalHeaderItem(row, QTableWidgetItem(str(col.column_id)))
            self.cols_table.setItem(row, 0, QTableWidgetItem(col.column_name))
            combo = QComboBox()
            combo.addItems(self.DATA_TYPES)
            combo.setCurrentText(col.data_type)
            self.cols_table.setCellWidget(row, 1, combo)
            pk_check = QCheckBox()
            pk_check.setChecked(col.is_primary_key)
            self._center_widget_in_cell(self.cols_table, row, 2, pk_check)
            nn_check = QCheckBox()
            nn_check.setChecked(not col.is_nullable)
            self._center_widget_in_cell(self.cols_table, row, 3, nn_check)
            uq_check = QCheckBox()
            uq_check.setChecked(col.is_unique)
            self._center_widget_in_cell(self.cols_table, row, 4, uq_check)
            self.cols_table.setItem(row, 5, QTableWidgetItem(col.default_value or ""))

    def _add_column_row(self):
        row = self.cols_table.rowCount()
        self.cols_table.insertRow(row)
        self.cols_table.setVerticalHeaderItem(row, QTableWidgetItem(""))
        self.cols_table.setItem(row, 0, QTableWidgetItem("new_column"))
        combo = QComboBox()
        combo.addItems(self.DATA_TYPES)
        self.cols_table.setCellWidget(row, 1, combo)
        self._center_widget_in_cell(self.cols_table, row, 2, QCheckBox())
        self._center_widget_in_cell(self.cols_table, row, 3, QCheckBox())
        self._center_widget_in_cell(self.cols_table, row, 4, QCheckBox())
        self.cols_table.setItem(row, 5, QTableWidgetItem(""))

    def _remove_column_row(self):
        current_row = self.cols_table.currentRow()
        if current_row >= 0:
            self.cols_table.removeRow(current_row)

    def _save_columns(self) -> bool:
        columns_data = []
        column_names = set()
        for row in range(self.cols_table.rowCount()):
            name_item = self.cols_table.item(row, 0)
            if not name_item or not name_item.text():
                QMessageBox.warning(self, "Ошибка", f"Имя колонки в строке {row + 1} не может быть пустым.")
                return False
            name = name_item.text().strip()
            if name in column_names:
                QMessageBox.warning(self, "Ошибка", f"Имя колонки '{name}' дублируется.")
                return False
            column_names.add(name)
            header = self.cols_table.verticalHeaderItem(row)
            columns_data.append({
                "id": int(header.text()) if header and header.text() else None,
                "name": name,
                "type": self.cols_table.cellWidget(row, 1).currentText(),
                "pk": self.cols_table.cellWidget(row, 2).layout().itemAt(0).widget().isChecked(),
                "nn": self.cols_table.cellWidget(row, 3).layout().itemAt(0).widget().isChecked(),
                "uq": self.cols_table.cellWidget(row, 4).layout().itemAt(0).widget().isChecked(),
                "default": self.cols_table.item(row, 5).text()
            })
        self.controller.sync_columns_for_table(self.table_id, columns_data)
        return True

    def _save_notes(self):
        self.controller.update_table_notes(self.table_id, self.notes_text_edit.toPlainText())

    def _load_indexes(self, indexes):
        self.indexes_table.clearContents()
        self.indexes_table.setRowCount(len(indexes))
        for row, index in enumerate(indexes):
            name_item = QTableWidgetItem(index.index_name)
            name_item.setData(Qt.UserRole, index)
            self.indexes_table.setItem(row, 0, name_item)
            index_type = "UNIQUE" if index.is_unique else "INDEX"
            self.indexes_table.setItem(row, 1, QTableWidgetItem(index_type))
            sorted_cols = sorted(index.index_columns, key=lambda ic: ic.order)
            col_names = ", ".join([ic.column.column_name for ic in sorted_cols])
            self.indexes_table.setItem(row, 2, QTableWidgetItem(col_names))

    def handle_add_index(self):
        all_columns = self.controller.get_columns_for_table(self.table_id)
        if not all_columns:
            QMessageBox.warning(self, "Ошибка", "Нельзя создать индекс, пока в таблице нет колонок.")
            return
        dialog = IndexEditorDialog(all_columns, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.controller.create_or_update_index(self.table_id, None, dialog.result_data)
            self._load_all_data()

    def handle_edit_index(self):
        current_row = self.indexes_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Внимание", "Пожалуйста, выберите индекс для редактирования.")
            return
        index_obj: DbIndex = self.indexes_table.item(current_row, 0).data(Qt.UserRole)
        all_columns = self.controller.get_columns_for_table(self.table_id)
        dialog = IndexEditorDialog(all_columns, index_to_edit=index_obj, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.controller.create_or_update_index(self.table_id, index_obj.index_id, dialog.result_data)
            self._load_all_data()

    def handle_delete_index(self):
        current_row = self.indexes_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Внимание", "Пожалуйста, выберите индекс для удаления.")
            return
        index_obj: DbIndex = self.indexes_table.item(current_row, 0).data(Qt.UserRole)
        reply = QMessageBox.question(self, "Подтверждение",
                                     f"Вы уверены, что хотите удалить индекс '{index_obj.index_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.controller.delete_index(index_obj.index_id)
            self._load_all_data()

    def on_accept(self):
        if not self._save_columns():
            return
        self._save_notes()
        self.accept()