# views/diagram_view.py

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QMenu, QGraphicsPathItem,
    QGraphicsEllipseItem, QMessageBox, QInputDialog, QGraphicsItem, QDialog, QMainWindow
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QPainterPath
from .table_editor_dialog import TableEditorDialog


# ... (Классы PortItem, ColumnItem, AddButton, ConnectionLine остаются без изменений, но привожу их для полноты)
class PortItem(QGraphicsEllipseItem):
    def __init__(self, parent_column, side='left'):
        super().__init__(-4, -4, 8, 8, parent_column)
        self.column = parent_column;
        self.side = side
        self.default_brush = QBrush(QColor(100, 180, 255));
        self.hover_brush = QBrush(QColor(120, 200, 255));
        self.highlight_brush = QBrush(QColor(0, 180, 255))
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

    def set_highlighted(self, highlighted: bool):
        if highlighted:
            self.setBrush(self.highlight_brush); self.setRect(-6, -6, 12, 12)
        else:
            self.setBrush(self.default_brush); self.setRect(-4, -4, 8, 8)


class ColumnItem(QGraphicsRectItem):
    def __init__(self, name, parent_table, column_id=None, column_info=None, width=300, height=28):
        super().__init__(QRectF(6, 0, width - 12, height), parent_table)
        self.parent_table = parent_table;
        self.column_id = column_id
        self.default_brush = QBrush(QColor(250, 250, 250));
        self.default_pen = QPen(Qt.black, 1.0)
        self.setBrush(self.default_brush);
        self.setPen(self.default_pen);
        self.setZValue(1)
        attr_name = name;
        attr_type = "varchar"
        if column_info:
            attr_type = column_info.get('type', 'varchar')
            if column_info.get('pk', False): attr_name = f"🔑 {attr_name}"
            if not column_info.get('nn', True): attr_type += " [null]"
        self.name_item = QGraphicsTextItem(attr_name, self);
        self.name_item.setDefaultTextColor(Qt.black);
        self.name_item.setPos(10, 4)
        self.type_item = QGraphicsTextItem(attr_type, self);
        self.type_item.setDefaultTextColor(QColor(80, 80, 80));
        self.type_item.setPos(150, 4)
        self.left_port = PortItem(self, 'left');
        self.right_port = PortItem(self, 'right')

    def set_highlighted(self, highlighted: bool):
        if highlighted:
            self.setBrush(QBrush(QColor(225, 245, 255))); self.setPen(QPen(QColor(0, 180, 255), 2.0))
        else:
            self.setBrush(self.default_brush); self.setPen(self.default_pen)


class AddButton(QGraphicsEllipseItem): pass


class TableItem(QGraphicsRectItem):
    def __init__(self, name, x, y, diagram_object_id=None, table_id=None, controller=None, width=300, height=60):
        super().__init__(QRectF(0, 0, width, height))
        self.diagram_object_id, self.table_id, self.controller = diagram_object_id, table_id, controller
        self.columns = [];
        self.width, self.row_height = width, 28
        self.setPos(x, y);
        self.setFlags(
            QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges);
        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(QColor(200, 220, 255)));
        self.setPen(QPen(QColor(80, 80, 120), 1.2))
        self.text = QGraphicsTextItem(name, self);
        self.text.setDefaultTextColor(QColor(30, 30, 30));
        self.text.setPos(8, 4)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        dialog = TableEditorDialog(self.table_id, self.controller, self.scene().views()[0])
        if dialog.exec() == QDialog.Accepted:
            # ИСПРАВЛЕНИЕ: Используем прямую ссылку на main_window
            self.scene().views()[0].main_window.load_project_data()
        event.accept()

    def add_column(self, name: str, column_id: int, column_info: dict = None):
        col = ColumnItem(name, self, column_id, column_info, self.width)
        self.columns.append(col)
        # ИСПРАВЛЕНИЕ: Убираем рекурсивный вызов
        self.scene().views()[0].add_column_to_map(col)

    def update_layout(self):
        # Очищаем только визуальные элементы, не трогая данные
        for item in self.childItems():
            if isinstance(item, ColumnItem):
                self.scene().views()[0].remove_column_from_map(item)
                self.scene().removeItem(item)
        self.columns.clear()

        # Загружаем свежие данные и перерисовываем
        fresh_columns = self.controller.get_columns_for_table(self.table_id)
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
            pos = self.pos();
            self.controller.update_table_position(self.diagram_object_id, int(pos.x()), int(pos.y()))

    def hoverEnterEvent(self, event):
        for col in self.columns: col.left_port.setVisible(True); col.right_port.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        for col in self.columns: col.left_port.setVisible(False); col.right_port.setVisible(False)
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for column in self.columns:
                for port in [column.left_port, column.right_port]:
                    for connection in getattr(port, 'connections', []):
                        connection.update_position()
        return super().itemChange(change, value)


class ConnectionLine(QGraphicsPathItem):
    def __init__(self, start_port, end_port, relationship_id=None):
        super().__init__()
        self.start_port, self.end_port, self.relationship_id = start_port, end_port, relationship_id
        self.default_pen = QPen(QColor(80, 80, 80), 2);
        self.highlight_pen = QPen(QColor(0, 180, 255), 3.5)
        self.setPen(self.default_pen);
        self.setFlag(QGraphicsItem.ItemIsSelectable, True);
        self.setZValue(-1)
        for port in [start_port, end_port]:
            if not hasattr(port, 'connections'): port.connections = []
            port.connections.append(self)
        self.update_position()

    def paint(self, painter, option, widget=None):
        painter.setPen(self.pen()); painter.drawPath(self.path())

    def update_position(self):
        path = QPainterPath();
        start_p = self.start_port.scenePos();
        end_p = self.end_port.scenePos()
        path.moveTo(start_p);
        dx = end_p.x() - start_p.x();
        offset = min(abs(dx) * 0.5, 100.0)
        if abs(dx) < 50: offset = 50
        start_offset = offset if self.start_port.side == 'right' else -offset;
        end_offset = -offset if self.end_port.side == 'left' else offset
        control1 = QPointF(start_p.x() + start_offset, start_p.y());
        control2 = QPointF(end_p.x() + end_offset, end_p.y())
        path.cubicTo(control1, control2, end_p);
        self.setPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange: self.set_highlighted(value)
        return super().itemChange(change, value)

    def set_highlighted(self, highlighted: bool):
        self.setPen(self.highlight_pen if highlighted else self.default_pen)
        self.start_port.set_highlighted(highlighted);
        self.start_port.column.set_highlighted(highlighted)
        self.end_port.set_highlighted(highlighted);
        self.end_port.column.set_highlighted(highlighted)


class DiagramView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene();
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing);
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        self.setSceneRect(0, 0, 4000, 3000);
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.controller = None;
        self.current_diagram = None;
        self.main_window: QMainWindow = None
        self.table_items: Dict[int, TableItem] = {}
        self.column_map: Dict[int, ColumnItem] = {}
        self.first_port: PortItem = None

    def set_main_window(self, main_window: QMainWindow):
        self.main_window = main_window

    def set_controller(self, controller):
        self.controller = controller

    def add_column_to_map(self, col):
        self.column_map[col.column_id] = col

    def remove_column_from_map(self, col):
        if col.column_id in self.column_map: del self.column_map[col.column_id]

    def clear_column_map_for_table(self, table_id: int):
        ids_to_remove = [cid for cid, c in self.column_map.items() if c.parent_table.table_id == table_id]
        for cid in ids_to_remove: del self.column_map[cid]

    def load_diagram_data(self, diagram, diagram_objects, relationships):
        self.clear_diagram();
        self.current_diagram = diagram
        for d_obj in diagram_objects:
            table = d_obj.table
            item = TableItem(table.table_name, d_obj.pos_x, d_obj.pos_y, d_obj.object_id, table.table_id,
                             self.controller)
            self.scene.addItem(item);
            self.table_items[table.table_id] = item
            item.update_layout()  # Обновляем колонки из БД
        for rel in relationships:
            if not rel.relationship_columns: continue
            rel_col = rel.relationship_columns[0]
            start = self.column_map.get(rel_col.start_column_id);
            end = self.column_map.get(rel_col.end_column_id)
            if start and end: self.scene.addItem(ConnectionLine(start.right_port, end.left_port, rel.relationship_id))

    def clear_diagram(self):
        self.scene.clear(); self.table_items.clear(); self.column_map.clear(); self.first_port = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event);
        item = self.itemAt(event.pos())
        if event.button() == Qt.LeftButton and not item:
            for sel_item in self.scene.selectedItems(): sel_item.setSelected(False)
            if self.first_port: self.first_port.set_highlighted(False); self.first_port = None
        elif isinstance(item, PortItem):
            if not self.first_port:
                self.first_port = item; self.first_port.set_highlighted(True)
            else:
                self.first_port.set_highlighted(False)
                if self.first_port.column.parent_table != item.column.parent_table: self.create_relationship(
                    self.first_port, item)
                self.first_port = None

    def create_relationship(self, start, end):
        new_rel = self.controller.add_relationship(self.current_diagram.project_id, start.column.column_id,
                                                   end.column.column_id)
        if new_rel: self.scene.addItem(ConnectionLine(start, end, new_rel.relationship_id))

    def contextMenuEvent(self, event):
        menu = QMenu(self);
        selected = self.scene.selectedItems();
        clicked = self.itemAt(event.pos())
        if not isinstance(clicked, ConnectionLine): menu.addAction("Добавить таблицу")
        if any(isinstance(it, TableItem) for it in selected): menu.addAction("Удалить таблицу(ы)")
        if any(isinstance(it, ConnectionLine) for it in selected): menu.addAction("Удалить связь(и)")
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
        d_obj = self.controller.add_new_table_to_diagram(self.current_diagram.diagram_id,
                                                         self.current_diagram.project_id, name, int(x), int(y))
        if d_obj:
            item = TableItem(d_obj.table.table_name, d_obj.pos_x, d_obj.pos_y, d_obj.object_id, d_obj.table.table_id,
                             self.controller)
            self.scene.addItem(item);
            self.table_items[d_obj.table.table_id] = item
            item.update_layout()

    def delete_selected_tables(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, TableItem)]
        if not items: return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} таблицу(ы)?') == QMessageBox.Yes:
            for item in items: self.controller.delete_table_from_diagram(item.diagram_object_id)
            self.main_window.load_project_data()

    def delete_selected_lines(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, ConnectionLine)]
        if not items: return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} связь(и)?') == QMessageBox.Yes:
            for item in items: self.controller.delete_relationship(item.relationship_id); self.scene.removeItem(item)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect);
        painter.setPen(QColor(220, 220, 220));
        step = 25
        left, top = int(rect.left()), int(rect.top())
        for x in range(left - (left % step), int(rect.right()), step): painter.drawLine(x, rect.top(), x, rect.bottom())
        for y in range(top - (top % step), int(rect.bottom()), step): painter.drawLine(rect.left(), y, rect.right(), y)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y();
            old_pos = self.mapToScene(event.position().toPoint())
            zoom = 1.15 if delta > 0 else 1 / 1.15;
            self.scale(zoom, zoom)
            new_pos = self.mapToScene(event.position().toPoint());
            delta_scene = new_pos - old_pos
            self.translate(delta_scene.x(), delta_scene.y())
        else:
            super().wheelEvent(event)