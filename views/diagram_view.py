# views/diagram_view.py

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QMenu, QGraphicsPathItem,
    QGraphicsEllipseItem, QMessageBox, QInputDialog, QGraphicsItem, QDialog,
    QMainWindow, QColorDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QRectF, QPointF, QSettings, Signal
from PySide6.QtGui import (QBrush, QColor, QPen, QPainter, QPainterPath,
                           QFontMetrics, QImage, QLinearGradient, QFont)
from .table_editor_dialog import TableEditorDialog
from controllers.table_controller import TableController
from typing import Dict

# --- ЦВЕТОВАЯ ПАЛИТРА ---
COLOR_BG_DARK = QColor(20, 20, 25)  # Очень темный фон сцены
COLOR_GRID_LINE = QColor(255, 255, 255, 15)  # Еле заметная сетка
COLOR_NODE_BODY = QColor(30, 32, 40, 210)  # Полупрозрачное тело таблицы
COLOR_ACCENT_CYAN = QColor(137, 180, 250)  # Neon Cyan
COLOR_ACCENT_PINK = QColor(245, 194, 231)  # Neon Pink
COLOR_TEXT_MAIN = QColor(255, 255, 255)
COLOR_TEXT_DIM = QColor(180, 180, 200)


class PortItem(QGraphicsEllipseItem):
    def __init__(self, parent_column, side='left'):
        super().__init__(-5, -5, 10, 10, parent_column)
        self.column = parent_column
        self.side = side

        # Неоновые цвета портов
        self.default_color = COLOR_ACCENT_CYAN
        self.highlight_color = COLOR_ACCENT_PINK

        self.setBrush(QBrush(self.default_color))
        self.setPen(QPen(Qt.NoPen))
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        self.setVisible(False)
        self.update_position()

        # Свечение порта
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(10)
        glow.setColor(self.default_color)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

    def update_position(self):
        r = self.column.rect()
        y_center = r.top() + r.height() / 2
        if self.side == 'left':
            self.setPos(r.left(), y_center)
        else:
            self.setPos(r.right(), y_center)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(self.highlight_color))
        self.graphicsEffect().setColor(self.highlight_color)
        self.setRect(-6, -6, 12, 12)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.column.is_highlighted:  # Если не активен, возвращаем цвет
            self.setBrush(QBrush(self.default_color))
            self.graphicsEffect().setColor(self.default_color)
        self.setRect(-5, -5, 10, 10)
        super().hoverLeaveEvent(event)

    def set_highlighted(self, highlighted: bool):
        if highlighted:
            self.setBrush(QBrush(self.highlight_color))
            self.graphicsEffect().setColor(self.highlight_color)
            self.setRect(-7, -7, 14, 14)
        else:
            self.setBrush(QBrush(self.default_color))
            self.graphicsEffect().setColor(self.default_color)
            self.setRect(-5, -5, 10, 10)


class ColumnItem(QGraphicsRectItem):
    MAX_NAME_WIDTH = 130
    MAX_TYPE_WIDTH = 120

    def __init__(self, name, parent_table, column_id=None, column_info=None, width=300, height=28):
        super().__init__(QRectF(6, 0, width - 12, height), parent_table)
        self.parent_table = parent_table
        self.column_id = column_id
        self.raw_name = name
        self.data_type = column_info.get('type', 'varchar') if column_info else "varchar"
        self.is_pk = column_info.get('pk', False) if column_info else False
        self.is_fk = False
        self.is_nn = column_info.get('nn', True) if column_info else True
        self.is_highlighted = False

        # Прозрачный фон колонки
        self.setBrush(Qt.NoBrush)
        self.setPen(Qt.NoPen)
        self.setZValue(1)

        self.name_item = QGraphicsTextItem("", self)
        self.name_item.setDefaultTextColor(COLOR_TEXT_MAIN)
        self.name_item.setPos(10, 4)
        self.name_item.setFont(QFont("Segoe UI", 9))

        self.type_item = QGraphicsTextItem("", self)
        self.type_item.setDefaultTextColor(COLOR_TEXT_DIM)
        self.type_item.setPos(150, 4)
        self.type_item.setFont(QFont("Consolas", 9))  # Моноширинный шрифт для типов

        self.left_port = PortItem(self, 'left')
        self.right_port = PortItem(self, 'right')
        self._update_and_elide_text()

    def _update_and_elide_text(self):
        prefix = ""
        # Цвет иконок
        pk_color = "#fab387"  # Orange
        fk_color = "#a6e3a1"  # Green

        # Формируем HTML для раскраски иконок
        name_html = ""
        if self.is_pk: name_html += f"<span style='color:{pk_color};'>🔑 </span>"
        if self.is_fk: name_html += f"<span style='color:{fk_color};'>🔒 </span>"

        name_html += self.raw_name

        # Сначала элайдим текст без HTML тегов
        font_metrics_name = QFontMetrics(self.name_item.font())
        elided_name = font_metrics_name.elidedText(self.raw_name, Qt.ElideRight, self.MAX_NAME_WIDTH)

        # Применяем HTML с элайженным именем
        final_html = name_html.replace(self.raw_name, elided_name)
        self.name_item.setHtml(final_html)

        suffix = "" if self.is_nn else " [null]"
        display_type = f"{self.data_type}{suffix}"
        font_metrics_type = QFontMetrics(self.type_item.font())
        elided_type = font_metrics_type.elidedText(display_type, Qt.ElideRight, self.MAX_TYPE_WIDTH)
        self.type_item.setPlainText(elided_type)

    def update_data_type(self, new_type: str):
        self.data_type = new_type
        self._update_and_elide_text()

    def set_highlighted(self, highlighted: bool):
        self.is_highlighted = highlighted
        if highlighted:
            # Подсветка фона колонки при наведении на связь
            self.setBrush(QBrush(QColor(137, 180, 250, 50)))
        else:
            self.setBrush(Qt.NoBrush)


class TableItem(QGraphicsRectItem):
    def __init__(self, name, x, y, diagram_object_id=None, table_id=None, controller=None, color=None, width=300,
                 height=60):
        super().__init__(QRectF(0, 0, width, height))
        self.diagram_object_id = diagram_object_id
        self.table_id = table_id
        self.diagram_controller = controller
        self.width, self.row_height = width, 28
        self.columns = []
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Цвета
        self.custom_header_color = QColor(color) if color else COLOR_ACCENT_CYAN
        self.body_color = COLOR_NODE_BODY

        # Эффект свечения (Drop Shadow) для выбранной таблицы
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(20)
        self.glow.setColor(QColor(0, 0, 0, 0))  # По умолчанию выключен
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

        # Заголовок (Text)
        self.text = QGraphicsTextItem(name, self)
        self.text.setDefaultTextColor(QColor(10, 10, 20))  # Темный текст на ярком заголовке
        font = QFont("Segoe UI", 10, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        self.text.setFont(font)
        self.text.setPos(8, 4)

    def paint(self, painter, option, widget=None):
        # --- КАСТОМНАЯ ОТРИСОВКА "СТЕКЛА" ---
        r = self.rect()

        # 1. Тело (Body) - Полупрозрачное темное
        body_path = QPainterPath()
        body_path.addRoundedRect(r, 10, 10)
        painter.setBrush(self.body_color)
        painter.setPen(Qt.NoPen)
        painter.drawPath(body_path)

        # 2. Заголовок (Header)
        header_height = 30
        header_rect = QRectF(r.x(), r.y(), r.width(), header_height)
        header_path = QPainterPath()
        header_path.setFillRule(Qt.WindingFill)
        header_path.addRoundedRect(header_rect, 10, 10)
        # Обрезаем нижние углы, чтобы они были прямыми (стык с телом)
        header_path.addRect(QRectF(r.x(), r.y() + header_height - 5, r.width(), 5))

        # Градиент для заголовка
        grad = QLinearGradient(header_rect.topLeft(), header_rect.bottomRight())
        grad.setColorAt(0, self.custom_header_color)
        grad.setColorAt(1, self.custom_header_color.darker(120))

        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawPath(header_path)  # Рисуем header_path, но он может вылезти снизу.
        # Упрощенно: рисуем закругленный верх
        painter.drawRoundedRect(header_rect, 10, 10)
        # И прямоугольник снизу заголовка, чтобы перекрыть нижние скругления заголовка
        painter.fillRect(QRectF(r.x(), r.y() + 15, r.width(), 15), grad)

        # 3. Обводка (Border)
        border_pen = QPen(QColor(255, 255, 255, 30), 1)  # Тонкая белая рамка
        if self.isSelected():
            border_pen = QPen(COLOR_ACCENT_PINK, 2)  # Яркая рамка при выборе
            self.glow.setColor(COLOR_ACCENT_PINK)
            self.glow.setColor(QColor(245, 194, 231, 150))
        else:
            self.glow.setColor(QColor(0, 0, 0, 100))  # Обычная тень

        painter.setBrush(Qt.NoBrush)
        painter.setPen(border_pen)
        painter.drawRoundedRect(r, 10, 10)

    def setColor(self, color: QColor):
        if color.isValid():
            self.custom_header_color = color
            self.update()
            self.diagram_controller.update_table_color(self.diagram_object_id, color.name())

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        dialog = TableEditorDialog(self.table_id, self.scene().views()[0])
        if dialog.exec() == QDialog.Accepted:
            self.update_layout()
            self.scene().views()[0].update_connections_for_table(self)
        event.accept()

    def add_column(self, name: str, column_id: int, column_info: dict = None):
        col = ColumnItem(name, self, column_id, column_info, self.width)
        self.columns.append(col)
        self.scene().views()[0].add_column_to_map(col)

    def update_layout(self):
        for item in self.childItems():
            if isinstance(item, ColumnItem):
                self.scene().views()[0].remove_column_from_map(item)
                self.scene().removeItem(item)
        self.columns.clear()
        table_ctrl = TableController()
        fresh_columns = table_ctrl.get_columns_for_table(self.table_id)
        for col_data in fresh_columns:
            info = {'type': col_data.data_type, 'pk': col_data.is_primary_key, 'nn': not col_data.is_nullable}
            self.add_column(col_data.column_name, col_data.column_id, info)
        height = 30 + len(self.columns) * self.row_height + 10
        self.setRect(0, 0, self.width, height)
        for i, col in enumerate(self.columns):
            col.setY(30 + i * self.row_height)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and event.scenePos() != event.lastScenePos():
            pos = self.pos()
            self.diagram_controller.update_table_position(self.diagram_object_id, int(pos.x()), int(pos.y()))

    def hoverEnterEvent(self, event):
        for col in self.columns:
            col.left_port.setVisible(True)
            col.right_port.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        for col in self.columns:
            col.left_port.setVisible(False)
            col.right_port.setVisible(False)
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for column in self.columns:
                for port in [column.left_port, column.right_port]:
                    if hasattr(port, 'connections'):
                        for connection in port.connections:
                            connection.update_position()
        return super().itemChange(change, value)


class ConnectionLine(QGraphicsPathItem):
    def __init__(self, start_port, end_port, relationship_id=None):
        super().__init__()
        self.start_port, self.end_port, self.relationship_id = start_port, end_port, relationship_id

        # Стиль линий
        self.default_pen = QPen(QColor(100, 100, 120), 2)
        self.highlight_pen = QPen(COLOR_ACCENT_CYAN, 3)

        self.setPen(self.default_pen)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(-1)

        # Эффект свечения для линий
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(10)
        self.glow.setColor(COLOR_ACCENT_CYAN)
        self.glow.setEnabled(False)
        self.setGraphicsEffect(self.glow)

        for port in [start_port, end_port]:
            if not hasattr(port, 'connections'):
                port.connections = []
            port.connections.append(self)
        self.update_position()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen())
        painter.drawPath(self.path())

    def update_position(self):
        path = QPainterPath()
        start_p = self.start_port.scenePos()
        end_p = self.end_port.scenePos()
        path.moveTo(start_p)
        dx = end_p.x() - start_p.x()
        offset = min(abs(dx) * 0.5, 100.0)
        if abs(dx) < 50: offset = 50
        start_offset = offset if self.start_port.side == 'right' else -offset
        end_offset = -offset if self.end_port.side == 'left' else offset
        control1 = QPointF(start_p.x() + start_offset, start_p.y())
        control2 = QPointF(end_p.x() + end_offset, end_p.y())
        path.cubicTo(control1, control2, end_p)
        self.setPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.set_highlighted(value)
        return super().itemChange(change, value)

    def set_highlighted(self, highlighted: bool):
        self.setPen(self.highlight_pen if highlighted else self.default_pen)
        self.glow.setEnabled(highlighted)
        self.start_port.set_highlighted(highlighted)
        self.start_port.column.set_highlighted(highlighted)
        self.end_port.set_highlighted(highlighted)
        self.end_port.column.set_highlighted(highlighted)


class DiagramView(QGraphicsView):
    project_structure_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QBrush(COLOR_BG_DARK))
        self.setSceneRect(0, 0, 8000, 6000)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.controller = None
        self.current_diagram = None
        self.main_window: QMainWindow = None
        self.setAcceptDrops(True)
        self.table_items: Dict[int, TableItem] = {}
        self.column_map: Dict[int, ColumnItem] = {}
        self.first_port: PortItem = None
        self.default_table_color = self.load_default_color()

        # Убираем скроллбары для полного погружения (опционально)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def load_default_color(self) -> QColor:
        settings = QSettings("MyCompany", "VisualDBDesigner")
        color_name = settings.value("default_table_color", COLOR_ACCENT_CYAN.name())
        return QColor(color_name)

    def save_default_color(self, color: QColor):
        settings = QSettings("MyCompany", "VisualDBDesigner")
        settings.setValue("default_table_color", color.name())
        self.default_table_color = color
        QMessageBox.information(self, "Настройки",
                                f"Цвет {color.name()} установлен как цвет по умолчанию для новых таблиц.")

    def save_project_state(self):
        if not self.controller or not self.table_items: return
        for table_item in self.table_items.values():
            pos = table_item.pos()
            self.controller.update_table_position(table_item.diagram_object_id, int(pos.x()), int(pos.y()))
        if self.current_diagram: self.controller.update_project_timestamp(self.current_diagram.project_id)
        if self.main_window: self.main_window.statusBar().showMessage("Проект успешно сохранен.", 3000)

    def exit_to_project_selection(self):
        if self.main_window and hasattr(self.main_window, 'show_project_selection'):
            self.main_window.show_project_selection()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            self.save_project_state()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        item = self.itemAt(event.pos())
        if event.button() == Qt.LeftButton and not item:
            for sel_item in self.scene.selectedItems():
                sel_item.setSelected(False)
            if self.first_port:
                self.first_port.set_highlighted(False)
                self.first_port = None
        elif isinstance(item, PortItem):
            if not self.first_port:
                self.first_port = item
                self.first_port.set_highlighted(True)
            else:
                self.first_port.set_highlighted(False)
                if self.first_port.column.parent_table != item.column.parent_table:
                    self.create_relationship(self.first_port, item)
                self.first_port = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            data_str = event.mimeData().text()
            if data_str.startswith("table_id:"):
                try:
                    table_id = int(data_str.split(":")[1])
                    if table_id in self.table_items:
                        QMessageBox.information(self, "Внимание", "Эта таблица уже находится на диаграмме.")
                        return
                    drop_pos = self.mapToScene(event.position().toPoint())
                    self.controller.add_existing_table_to_diagram(
                        self.current_diagram.diagram_id,
                        table_id,
                        int(drop_pos.x()),
                        int(drop_pos.y())
                    )
                    self.main_window.load_current_diagram_view()
                    event.acceptProposedAction()
                except (ValueError, IndexError):
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()

    def clear_diagram(self):
        items_to_remove = [item for item in self.scene.items() if isinstance(item, (TableItem, ConnectionLine))]
        for item in items_to_remove:
            self.scene.removeItem(item)
        self.table_items.clear()
        self.column_map.clear()
        self.first_port = None

    def set_main_window(self, main_window: QMainWindow):
        self.main_window = main_window

    def set_controller(self, controller):
        self.controller = controller

    def add_column_to_map(self, col):
        self.column_map[col.column_id] = col

    def remove_column_from_map(self, col):
        if col.column_id in self.column_map:
            del self.column_map[col.column_id]

    def load_diagram_data(self, diagram, diagram_objects, relationships):
        self.clear_diagram()
        self.current_diagram = diagram
        for d_obj in diagram_objects:
            table = d_obj.table
            item = TableItem(
                name=table.table_name, x=d_obj.pos_x, y=d_obj.pos_y,
                diagram_object_id=d_obj.object_id, table_id=table.table_id,
                controller=self.controller, color=d_obj.color
            )
            self.scene.addItem(item)
            self.table_items[table.table_id] = item
            item.update_layout()

        for rel in relationships:
            if not rel.relationship_columns: continue
            rel_col = rel.relationship_columns[0]
            start_col_item = self.column_map.get(rel_col.start_column_id)
            end_col_item = self.column_map.get(rel_col.end_column_id)
            if start_col_item and end_col_item:
                start_port = start_col_item.left_port if rel_col.start_port_side == 'left' else start_col_item.right_port
                end_port = end_col_item.right_port if rel_col.end_port_side == 'right' else end_col_item.left_port
                self.scene.addItem(ConnectionLine(start_port, end_port, rel.relationship_id))
                end_col_item.is_fk = True
                end_col_item._update_and_elide_text()

    def update_connections_for_table(self, table_item: TableItem):
        for column in table_item.columns:
            for port in [column.left_port, column.right_port]:
                if hasattr(port, 'connections'):
                    for connection in port.connections:
                        connection.update_position()

    def create_relationship(self, start_port: PortItem, end_port: PortItem):
        start_col = start_port.column
        end_col = end_port.column
        if start_col.data_type != end_col.data_type:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Типы данных не совпадают.")
            msg_box.setInformativeText(
                f"Тип у 🔑 {start_col.raw_name} - <b>{start_col.data_type}</b>, "
                f"а у 🔒 {end_col.raw_name} - <b>{end_col.data_type}</b>.<br><br>"
                f"Хотите изменить тип <b>{end_col.raw_name}</b> на <b>{start_col.data_type}</b> и создать связь?"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            if msg_box.exec() != QMessageBox.Yes: return
            self.controller.update_column_data_type(end_col.column_id, start_col.data_type)
            end_col.update_data_type(start_col.data_type)

        new_rel = self.controller.add_relationship(
            self.current_diagram.project_id, start_col.column_id, end_col.column_id, start_port.side, end_port.side)
        if new_rel:
            self.scene.addItem(ConnectionLine(start_port, end_port, new_rel.relationship_id))
            end_col.is_fk = True
            end_col._update_and_elide_text()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        scene_pos = self.mapToScene(event.pos())
        clicked_item = self.itemAt(event.pos())

        table_under_cursor = clicked_item
        while table_under_cursor and not isinstance(table_under_cursor, TableItem):
            table_under_cursor = table_under_cursor.parentItem()

        selected_items = self.scene.selectedItems()

        if table_under_cursor:
            if not table_under_cursor.isSelected():
                for item in selected_items:
                    item.setSelected(False)
                table_under_cursor.setSelected(True)

            menu.addAction("Изменить цвет...").triggered.connect(lambda: self.change_table_color(table_under_cursor))
            menu.addAction("Сделать цветом по умолчанию").triggered.connect(
                lambda: self.save_default_color(table_under_cursor.custom_header_color))
            menu.addSeparator()

        menu.addAction("Добавить таблицу")
        if any(isinstance(it, TableItem) for it in selected_items):
            menu.addAction("Удалить таблицу(ы)")
        if any(isinstance(it, ConnectionLine) for it in selected_items):
            menu.addAction("Удалить связь(и)")

        if not menu.isEmpty():
            action = menu.exec(event.globalPos())
            if action:
                if action.text() == "Добавить таблицу":
                    self.add_new_table(scene_pos.x(), scene_pos.y())
                elif action.text() == "Удалить таблицу(ы)":
                    self.delete_selected_tables()
                elif action.text() == "Удалить связь(и)":
                    self.delete_selected_lines()

    def change_table_color(self, table: TableItem):
        if not table: return
        new_color = QColorDialog.getColor(table.custom_header_color, self)
        if new_color.isValid():
            table.setColor(new_color)

    def add_new_table(self, x, y):
        name = f"New_Table_{len(self.table_items) + 1}"
        d_obj = self.controller.add_new_table_to_diagram(self.current_diagram.diagram_id,
                                                         self.current_diagram.project_id, name, int(x), int(y))
        if d_obj:
            item = TableItem(
                d_obj.table.table_name, d_obj.pos_x, d_obj.pos_y,
                d_obj.object_id, d_obj.table.table_id, self.controller,
                color=self.default_table_color.name()
            )
            item.setColor(self.default_table_color)
            self.scene.addItem(item)
            self.table_items[d_obj.table.table_id] = item
            item.update_layout()
            self.project_structure_changed.emit()

    def export_as_image(self, file_path: str) -> bool:
        try:
            rect = self.scene.itemsBoundingRect()
            rect.adjust(-50, -50, 50, 50)  # Добавляем поля
            image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
            image.fill(COLOR_BG_DARK)  # Заливаем темным фоном, чтобы было видно на белом

            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter, QRectF(image.rect()), rect)
            painter.end()
            return image.save(file_path)
        except Exception as e:
            print(f"Ошибка при экспорте изображения: {e}")
            return False

    def delete_selected_tables(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, TableItem)]
        if not items: return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} таблицу(ы)?') == QMessageBox.Yes:
            for item in items:
                self.controller.delete_table_from_diagram(item.diagram_object_id)
            self.main_window.load_project_data()

    def delete_selected_lines(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, ConnectionLine)]
        if not items: return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} связь(и)?') == QMessageBox.Yes:
            for item in items:
                end_column = item.end_port.column
                self.controller.delete_relationship(item.relationship_id)
                self.scene.removeItem(item)
                is_still_fk = self.controller.is_column_foreign_key(end_column.column_id)
                if end_column.is_fk != is_still_fk:
                    end_column.is_fk = is_still_fk
                    end_column._update_and_elide_text()

    # --- ИЗМЕНЕНО: РИСОВАНИЕ СЕТКИ ---
    def drawBackground(self, painter, rect):
        # Заливка фона
        painter.fillRect(rect, COLOR_BG_DARK)

        # Настройка сетки
        grid_size = 50
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        # Рисуем очень тонкие линии
        pen = QPen(COLOR_GRID_LINE, 1)
        pen.setCosmetic(True)  # Чтобы ширина не менялась при зуме
        painter.setPen(pen)

        lines = []
        x = left
        while x < rect.right():
            lines.append(QPointF(x, rect.top()))
            lines.append(QPointF(x, rect.bottom()))
            x += grid_size

        y = top
        while y < rect.bottom():
            lines.append(QPointF(rect.left(), y))
            lines.append(QPointF(rect.right(), y))
            y += grid_size

        painter.drawLines(lines)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            old_pos = self.mapToScene(event.position().toPoint())
            zoom = 1.15 if delta > 0 else 1 / 1.15
            self.scale(zoom, zoom)
            new_pos = self.mapToScene(event.position().toPoint())
            delta_scene = new_pos - old_pos
            self.translate(delta_scene.x(), delta_scene.y())
        else:
            super().wheelEvent(event)