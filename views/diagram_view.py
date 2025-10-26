# views/diagram_view.py

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QMenu, QGraphicsPathItem,
    QGraphicsEllipseItem, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QPainterPath
from typing import Dict, Any, List


class PortItem(QGraphicsEllipseItem):
    def __init__(self, parent_column, side='left'):
        super().__init__(-4, -4, 8, 8, parent_column)
        self.column = parent_column;
        self.side = side
        self.default_brush = QBrush(QColor(100, 180, 255));
        self.hover_brush = QBrush(QColor(120, 200, 255))
        self.setBrush(self.default_brush);
        self.setPen(QPen(Qt.NoPen));
        self.setZValue(10)
        self.setAcceptHoverEvents(True);
        self.setVisible(False);
        self.update_position()

    def update_position(self):
        r = self.column.rect();
        y_center = r.top() + r.height() / 2
        if self.side == 'left':
            self.setPos(r.left(), y_center)
        else:
            self.setPos(r.right(), y_center)

    def hoverEnterEvent(self, event):
        self.setBrush(self.hover_brush); self.setRect(-5, -5, 10, 10); super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush); self.setRect(-4, -4, 8, 8); super().hoverLeaveEvent(event)


class ColumnItem(QGraphicsRectItem):
    def __init__(self, name, parent_table, column_id=None, column_info=None, width=300, height=28):
        super().__init__(QRectF(6, 0, width - 12, height), parent_table)
        self.parent_table = parent_table;
        self.column_id = column_id
        self.setBrush(QBrush(QColor(250, 250, 250)));
        self.setPen(QPen(Qt.black, 1.0));
        self.setZValue(1)
        attr_name = name
        attr_type = "varchar"
        if column_info and 'type' in column_info: attr_type = column_info['type']
        self.name_item = QGraphicsTextItem(attr_name, self);
        self.name_item.setDefaultTextColor(Qt.black);
        self.name_item.setPos(10, 4)
        self.type_item = QGraphicsTextItem(attr_type, self);
        self.type_item.setDefaultTextColor(Qt.black);
        self.type_item.setPos(150, 4)
        self.left_port = PortItem(self, 'left');
        self.right_port = PortItem(self, 'right')


class AddButton(QGraphicsEllipseItem):
    def __init__(self, parent_table, action: str):
        super().__init__(-10, -10, 20, 20, parent_table)
        self.table = parent_table;
        self.action = action
        color = QColor(100, 180, 255) if action == 'add' else QColor(255, 100, 100)
        self.setBrush(QBrush(color));
        self.setPen(QPen(Qt.white, 1));
        self.setZValue(20);
        self.setVisible(False);
        self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event):
        if self.action == 'add':
            self.table.handle_add_column()
        else:
            self.table.handle_remove_column()
        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget);
        painter.setPen(Qt.white);
        painter.drawText(self.rect(), Qt.AlignCenter, "+" if self.action == 'add' else "−")

    def hoverEnterEvent(self, event):
        self.setBrush(self.brush().color().lighter(120)); super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.brush().color().darker(120)); super().hoverLeaveEvent(event)


# views/diagram_view.py -> class TableItem

class TableItem(QGraphicsRectItem):
    def __init__(self, name, x, y, diagram_object_id=None, table_id=None, controller=None, width=300, height=60):
        super().__init__(QRectF(0, 0, width, height))
        self.diagram_object_id, self.table_id, self.controller = diagram_object_id, table_id, controller
        self.columns: List[ColumnItem] = []
        self.width, self.row_height = width, 28

        self.setPos(x, y)
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(QColor(200, 220, 255)))
        self.setPen(QPen(QColor(80, 80, 120), 1.2))
        self.text = QGraphicsTextItem(name, self)
        self.text.setDefaultTextColor(QColor(30, 30, 30))
        self.text.setPos(8, 4)
        self.add_button = AddButton(self, action='add')
        self.remove_button = AddButton(self, action='remove')
        self.update_button_positions()

    def add_column(self, name: str, column_id: int, column_info: dict = None) -> ColumnItem:
        col = ColumnItem(name, self, column_id, column_info, self.width)
        self.columns.append(col)
        self.update_layout()
        self.scene().views()[0].add_column_to_map(col)
        return col

    def handle_add_column(self):
        col_name, ok = QInputDialog.getText(self.scene().views()[0], "Новая колонка", "Введите имя:")
        if ok and col_name:
            new_col = self.controller.add_column_to_table(self.table_id, col_name)
            if new_col:
                self.add_column(new_col.column_name, new_col.column_id, {'type': new_col.data_type})

    def handle_remove_column(self):
        if len(self.columns) <= 1:
            return
        col_to_remove = self.columns[-1]
        if self.controller.delete_column_from_table(col_to_remove.column_id):
            self.scene().views()[0].remove_column_from_map(col_to_remove)
            self.scene().removeItem(col_to_remove)
            self.columns.pop()
            self.update_layout()

    def update_layout(self):
        height = 30 + len(self.columns) * self.row_height + 22
        self.setRect(0, 0, self.width, height)
        for i, col in enumerate(self.columns):
            col.setY(30 + i * self.row_height)
        self.update_button_positions()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and event.scenePos() != event.lastScenePos():
            pos = self.pos()
            self.controller.update_table_position(self.diagram_object_id, int(pos.x()), int(pos.y()))

    def hoverEnterEvent(self, event):
        self.add_button.setVisible(True)
        self.remove_button.setVisible(True)
        for col in self.columns:
            col.left_port.setVisible(True)
            col.right_port.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.add_button.setVisible(False)
        self.remove_button.setVisible(False)
        for col in self.columns:
            col.left_port.setVisible(False)
            col.right_port.setVisible(False)
        super().hoverLeaveEvent(event)

    def update_button_positions(self):
        r = self.rect()
        y = r.bottom() - 18
        self.add_button.setPos(r.right() - 18, y)
        self.remove_button.setPos(r.left() + 18, y)

    def itemChange(self, change, value):
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
            for column in self.columns:
                for port in [column.left_port, column.right_port]:
                    for connection in getattr(port, 'connections', []):
                        connection.update_position()
        return super().itemChange(change, value)


# views/diagram_view.py -> class ConnectionLine

# views/diagram_view.py -> class ConnectionLine

class ConnectionLine(QGraphicsPathItem):
    def __init__(self, start_port, end_port, relationship_id=None):
        super().__init__()
        self.start_port, self.end_port, self.relationship_id = start_port, end_port, relationship_id
        self.setPen(QPen(QColor(80, 80, 80), 2))
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setZValue(-1)
        for port in [start_port, end_port]:
            if not hasattr(port, 'connections'):
                port.connections = []
            port.connections.append(self)
        self.update_position()

    def update_position(self):
        """
        ИСПОЛЬЗУЕТ НОВЫЙ АЛГОРИТМ: S-образные кривые Безье с "полочками".
        """
        path = QPainterPath()
        start_p = self.start_port.scenePos()
        end_p = self.end_port.scenePos()
        path.moveTo(start_p)

        # Рассчитываем динамическую длину "полочек"
        dx = end_p.x() - start_p.x()
        dy = end_p.y() - start_p.y()

        # Длина горизонтальной "полочки" - половина расстояния по X, но не более 100px
        offset = min(abs(dx) * 0.5, 100.0)
        # Если таблицы почти друг под другом, делаем фиксированную полочку, чтобы избежать "схлопывания"
        if abs(dx) < 50:
            offset = 50

        # Определяем направление полочек в зависимости от стороны порта
        start_offset = offset if self.start_port.side == 'right' else -offset
        end_offset = -offset if self.end_port.side == 'left' else offset

        # Создаем контрольные точки для кривой Безье
        # Они лежат на горизонтальных линиях, выходящих из портов
        control1 = QPointF(start_p.x() + start_offset, start_p.y())
        control2 = QPointF(end_p.x() + end_offset, end_p.y())

        # Рисуем плавную S-образную кривую
        path.cubicTo(control1, control2, end_p)

        self.setPath(path)
# views/diagram_view.py -> class DiagramView

class DiagramView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        self.setSceneRect(0, 0, 4000, 3000)

        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        self.setDragMode(QGraphicsView.RubberBandDrag)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        self.controller = None
        self.current_diagram = None
        self.table_items: Dict[int, TableItem] = {}
        self.column_map: Dict[int, ColumnItem] = {}
        self.first_port: PortItem = None

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
            item = TableItem(table.table_name, d_obj.pos_x, d_obj.pos_y, d_obj.object_id, table.table_id, self.controller)
            self.scene.addItem(item)
            self.table_items[table.table_id] = item
            for col in sorted(table.columns, key=lambda c: c.column_id):
                item.add_column(col.column_name, col.column_id, {'type': col.data_type})
        for rel in relationships:
            if not rel.relationship_columns:
                continue
            rel_col = rel.relationship_columns[0]
            start = self.column_map.get(rel_col.start_column_id)
            end = self.column_map.get(rel_col.end_column_id)
            if start and end:
                self.scene.addItem(ConnectionLine(start.right_port, end.left_port, rel.relationship_id))

    def clear_diagram(self):
        self.scene.clear()
        self.table_items.clear()
        self.column_map.clear()
        self.first_port = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, PortItem):
                if not self.first_port:
                    self.first_port = item
                    self.first_port.setBrush(QColor("red"))
                else:
                    self.first_port.setBrush(self.first_port.default_brush)
                    if self.first_port != item:
                        self.create_relationship(self.first_port, item)
                    self.first_port = None

    def create_relationship(self, start, end):
        new_rel = self.controller.add_relationship(self.current_diagram.project_id, start.column.column_id, end.column.column_id)
        if new_rel:
            self.scene.addItem(ConnectionLine(start, end, new_rel.relationship_id))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        selected = self.scene.selectedItems()
        clicked = self.itemAt(event.pos())
        if not isinstance(clicked, ConnectionLine):
            menu.addAction("Добавить таблицу")
        if any(isinstance(it, TableItem) for it in selected):
            menu.addAction("Удалить таблицу(ы)")
        if any(isinstance(it, ConnectionLine) for it in selected):
            menu.addAction("Удалить связь(и)")
        if not menu.isEmpty():
            action = menu.exec(event.globalPos())
            if action:
                if action.text() == "Добавить таблицу":
                    self.add_new_table(self.mapToScene(event.pos()).x(), self.mapToScene(event.pos()).y())
                elif action.text() == "Удалить таблицу(ы)":
                    self.delete_selected_tables()
                elif action.text() == "Удалить связь(и)":
                    self.delete_selected_lines()

    def add_new_table(self, x, y):
        name = f"New_Table_{len(self.table_items) + 1}"
        d_obj = self.controller.add_new_table_to_diagram(self.current_diagram.diagram_id, self.current_diagram.project_id, name, int(x), int(y))
        if d_obj:
            item = TableItem(d_obj.table.table_name, d_obj.pos_x, d_obj.pos_y, d_obj.object_id, d_obj.table.table_id, self.controller)
            self.scene.addItem(item)
            self.table_items[d_obj.table.table_id] = item
            if d_obj.table.columns:
                item.add_column(d_obj.table.columns[0].column_name, d_obj.table.columns[0].column_id)

    def delete_selected_tables(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, TableItem)]
        if not items:
            return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} таблицу(ы)?') == QMessageBox.Yes:
            for item in items:
                self.controller.delete_table_from_diagram(item.diagram_object_id)
            self.parent().load_project_data()

    def delete_selected_lines(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, ConnectionLine)]
        if not items:
            return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} связь(и)?') == QMessageBox.Yes:
            for item in items:
                self.controller.delete_relationship(item.relationship_id)
                self.scene.removeItem(item)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        painter.setPen(QColor(220, 220, 220))
        step = 25
        left, top = int(rect.left()), int(rect.top())
        for x in range(left - (left % step), int(rect.right()), step):
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for y in range(top - (top % step), int(rect.bottom()), step):
            painter.drawLine(rect.left(), y, rect.right(), y)

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