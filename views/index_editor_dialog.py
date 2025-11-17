# views/index_editor_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QCheckBox, QListWidget, QPushButton, QDialogButtonBox, QListWidgetItem, QMessageBox
from typing import List
from models.table import TableColumn, DbIndex
class IndexEditorDialog(QDialog):
    def __init__(self, all_columns: List[TableColumn], index_to_edit: DbIndex = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор индекса"); self.setMinimumSize(500, 350)
        self.all_columns = all_columns; self.result_data = None
        self.name_input = QLineEdit(); self.unique_checkbox = QCheckBox("Уникальный (UNIQUE)")
        self.available_cols_list = QListWidget(); self.indexed_cols_list = QListWidget()
        add_button = QPushButton("▶"); remove_button = QPushButton("◀"); move_up_button = QPushButton("▲"); move_down_button = QPushButton("▼")
        add_button.setToolTip("Добавить колонку в индекс"); remove_button.setToolTip("Убрать колонку из индекса"); move_up_button.setToolTip("Поднять колонку в порядке индекса"); move_down_button.setToolTip("Опустить колонку в порядке индекса")
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout(); form_layout.addRow("Имя индекса:", self.name_input); form_layout.addRow("", self.unique_checkbox)
        columns_layout = QHBoxLayout()
        left_panel = QVBoxLayout(); left_panel.addWidget(self.available_cols_list)
        center_panel = QVBoxLayout(); center_panel.addStretch(); center_panel.addWidget(add_button); center_panel.addWidget(remove_button); center_panel.addStretch()
        right_panel = QVBoxLayout(); right_panel.addWidget(self.indexed_cols_list)
        order_buttons_layout = QHBoxLayout(); order_buttons_layout.addStretch(); order_buttons_layout.addWidget(move_up_button); order_buttons_layout.addWidget(move_down_button)
        right_panel.addLayout(order_buttons_layout)
        columns_layout.addLayout(left_panel, 2); columns_layout.addLayout(center_panel); columns_layout.addLayout(right_panel, 2)
        main_layout.addLayout(form_layout); main_layout.addLayout(columns_layout); main_layout.addWidget(button_box)
        add_button.clicked.connect(self.add_column); remove_button.clicked.connect(self.remove_column)
        move_up_button.clicked.connect(self.move_up); move_down_button.clicked.connect(self.move_down)
        button_box.accepted.connect(self.on_accept); button_box.rejected.connect(self.reject)
        if index_to_edit: self.load_index_data(index_to_edit)
        else: self.populate_available_columns()
    def populate_available_columns(self, indexed_cols: List[TableColumn] = None):
        self.available_cols_list.clear()
        indexed_ids = {col.column_id for col in indexed_cols} if indexed_cols else set()
        for col in self.all_columns:
            if col.column_id not in indexed_ids:
                item = QListWidgetItem(col.column_name); item.setData(1, col); self.available_cols_list.addItem(item)
    def load_index_data(self, index: DbIndex):
        self.name_input.setText(index.index_name); self.unique_checkbox.setChecked(index.is_unique)
        sorted_index_columns = sorted(index.index_columns, key=lambda ic: ic.order)
        indexed_cols_objects = []
        for index_col in sorted_index_columns:
            item = QListWidgetItem(index_col.column.column_name); item.setData(1, index_col.column)
            self.indexed_cols_list.addItem(item); indexed_cols_objects.append(index_col.column)
        self.populate_available_columns(indexed_cols_objects)
    def add_column(self):
        selected_item = self.available_cols_list.currentItem()
        if not selected_item: return
        self.indexed_cols_list.addItem(self.available_cols_list.takeItem(self.available_cols_list.row(selected_item)))
    def remove_column(self):
        selected_item = self.indexed_cols_list.currentItem()
        if not selected_item: return
        self.available_cols_list.addItem(self.indexed_cols_list.takeItem(self.indexed_cols_list.row(selected_item)))
    def move_up(self):
        current_row = self.indexed_cols_list.currentRow()
        if current_row > 0:
            item = self.indexed_cols_list.takeItem(current_row)
            self.indexed_cols_list.insertItem(current_row - 1, item); self.indexed_cols_list.setCurrentRow(current_row - 1)
    def move_down(self):
        current_row = self.indexed_cols_list.currentRow()
        if 0 <= current_row < self.indexed_cols_list.count() - 1:
            item = self.indexed_cols_list.takeItem(current_row)
            self.indexed_cols_list.insertItem(current_row + 1, item); self.indexed_cols_list.setCurrentRow(current_row + 1)
    def on_accept(self):
        if not self.name_input.text(): QMessageBox.warning(self, "Ошибка", "Имя индекса не может быть пустым."); return
        if self.indexed_cols_list.count() == 0: QMessageBox.warning(self, "Ошибка", "Индекс должен содержать хотя бы одну колонку."); return
        column_ids = [self.indexed_cols_list.item(i).data(1).column_id for i in range(self.indexed_cols_list.count())]
        self.result_data = { "name": self.name_input.text(), "is_unique": self.unique_checkbox.isChecked(), "column_ids": column_ids }
        self.accept()