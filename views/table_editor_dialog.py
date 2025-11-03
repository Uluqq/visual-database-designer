# views/table_editor_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QAbstractItemView, QHeaderView, QCheckBox, QWidget,
    QHBoxLayout, QPushButton, QComboBox
)
from PySide6.QtCore import Qt


class TableEditorDialog(QDialog):
    DATA_TYPES = ["integer", "varchar", "text", "boolean", "date", "timestamp", "numeric"]

    def __init__(self, table_id, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор таблицы")
        self.setMinimumSize(800, 400)

        self.table_id = table_id
        self.controller = controller

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["Column Name", "Datatype", "PK", "NN", "UQ"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        self.add_button = QPushButton("Добавить колонку")
        self.remove_button = QPushButton("Удалить колонку")

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(self.add_button)
        h_layout.addWidget(self.remove_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table_widget)
        layout.addLayout(h_layout)
        layout.addWidget(button_box)

        button_box.accepted.connect(self._save_changes)
        button_box.rejected.connect(self.reject)
        self.add_button.clicked.connect(self._add_row)
        self.remove_button.clicked.connect(self._remove_row)

        self._load_columns()

    def _load_columns(self):
        columns = self.controller.get_columns_for_table(self.table_id)
        self.table_widget.setRowCount(len(columns))

        for row, col in enumerate(columns):
            self.table_widget.setVerticalHeaderItem(row, QTableWidgetItem(str(col.column_id)))
            self.table_widget.setItem(row, 0, QTableWidgetItem(col.column_name))

            combo = QComboBox();
            combo.addItems(self.DATA_TYPES);
            combo.setCurrentText(col.data_type)
            self.table_widget.setCellWidget(row, 1, combo)

            pk_check = QCheckBox();
            pk_check.setChecked(col.is_primary_key)
            self._center_widget_in_cell(row, 2, pk_check)

            nn_check = QCheckBox();
            nn_check.setChecked(not col.is_nullable)
            self._center_widget_in_cell(row, 3, nn_check)

            uq_check = QCheckBox();
            uq_check.setChecked(col.is_unique);
            uq_check.setEnabled(False)
            self._center_widget_in_cell(row, 4, uq_check)

    def _center_widget_in_cell(self, row, col, widget):
        cell_widget = QWidget();
        layout = QHBoxLayout(cell_widget)
        layout.addWidget(widget);
        layout.setAlignment(Qt.AlignCenter);
        layout.setContentsMargins(0, 0, 0, 0)
        self.table_widget.setCellWidget(row, col, cell_widget)

    def _add_row(self):
        row = self.table_widget.rowCount();
        self.table_widget.insertRow(row)
        self.table_widget.setVerticalHeaderItem(row, QTableWidgetItem(""))
        self.table_widget.setItem(row, 0, QTableWidgetItem("new_column"))

        combo = QComboBox();
        combo.addItems(self.DATA_TYPES)
        self.table_widget.setCellWidget(row, 1, combo)

        self._center_widget_in_cell(row, 2, QCheckBox())
        self._center_widget_in_cell(row, 3, QCheckBox())
        uq_check = QCheckBox();
        uq_check.setEnabled(False)
        self._center_widget_in_cell(row, 4, uq_check)

    def _remove_row(self):
        current_row = self.table_widget.currentRow()
        if current_row >= 0: self.table_widget.removeRow(current_row)

    def _save_changes(self):
        columns_data = []
        for row in range(self.table_widget.rowCount()):
            header = self.table_widget.verticalHeaderItem(row)
            name = self.table_widget.item(row, 0)
            if not name or not name.text(): continue

            columns_data.append({
                "id": int(header.text()) if header and header.text() else None,
                "name": name.text(),
                "type": self.table_widget.cellWidget(row, 1).currentText(),
                "pk": self.table_widget.cellWidget(row, 2).layout().itemAt(0).widget().isChecked(),
                "nn": self.table_widget.cellWidget(row, 3).layout().itemAt(0).widget().isChecked(),
            })
        self.controller.sync_columns_for_table(self.table_id, columns_data)
        self.accept()