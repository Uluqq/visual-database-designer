# views/diagram_view.py

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QMenu, QGraphicsPathItem,
    QGraphicsEllipseItem, QMessageBox, QInputDialog, QGraphicsItem, QDialog, QMainWindow
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QPainterPath, QFontMetrics
from .table_editor_dialog import TableEditorDialog
from typing import Dict


# КЛАСС DiagramButton ПОЛНОСТЬЮ УДАЛЕН

# --- Классы PortItem, ColumnItem, TableItem, ConnectionLine без изменений ---
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
        self.setZValue(10);
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
    MAX_NAME_WIDTH = 130;
    MAX_TYPE_WIDTH = 120

    def __init__(self, name, parent_table, column_id=None, column_info=None, width=300, height=28):
        super().__init__(QRectF(6, 0, width - 12, height), parent_table)
        self.parent_table = parent_table;
        self.column_id = column_id;
        self.raw_name = name
        self.data_type = column_info.get('type', 'varchar') if column_info else "varchar"
        self.is_pk = column_info.get('pk', False) if column_info else False;
        self.is_fk = False;
        self.is_nn = column_info.get('nn', True) if column_info else True
        self.default_brush = QBrush(QColor(250, 250, 250));
        self.default_pen = QPen(Qt.black, 1.0);
        self.setBrush(self.default_brush);
        self.setPen(self.default_pen);
        self.setZValue(1)
        self.name_item = QGraphicsTextItem("", self);
        self.name_item.setDefaultTextColor(Qt.black);
        self.name_item.setPos(10, 4)
        self.type_item = QGraphicsTextItem("", self);
        self.type_item.setDefaultTextColor(QColor(80, 80, 80));
        self.type_item.setPos(150, 4)
        self.left_port = PortItem(self, 'left');
        self.right_port = PortItem(self, 'right');
        self._update_and_elide_text()

    def _update_and_elide_text(self):
        prefix = "";
        if self.is_pk: prefix += "🔑 "
        if self.is_fk: prefix += "🔒 "
        display_name = f"{prefix}{self.raw_name}";
        suffix = "" if self.is_nn else " [null]";
        display_type = f"{self.data_type}{suffix}"
        font_metrics_name = QFontMetrics(self.name_item.font());
        elided_name = font_metrics_name.elidedText(display_name, Qt.ElideRight, self.MAX_NAME_WIDTH);
        self.name_item.setPlainText(elided_name)
        font_metrics_type = QFontMetrics(self.type_item.font());
        elided_type = font_metrics_type.elidedText(display_type, Qt.ElideRight, self.MAX_TYPE_WIDTH);
        self.type_item.setPlainText(elided_type)

    def update_data_type(self, new_type: str):
        self.data_type = new_type; self._update_and_elide_text()

    def set_highlighted(self, highlighted: bool):
        if highlighted:
            self.setBrush(QBrush(QColor(225, 245, 255))); self.setPen(QPen(QColor(0, 180, 255), 2.0))
        else:
            self.setBrush(self.default_brush); self.setPen(self.default_pen)


class TableItem(QGraphicsRectItem):
    def __init__(self, name, x, y, diagram_object_id=None, table_id=None, controller=None, width=300, height=60):
        super().__init__(QRectF(0, 0, width, height))
        self.diagram_object_id, self.table_id, self.controller = diagram_object_id, table_id, controller;
        self.columns = [];
        self.width, self.row_height = width, 28;
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges);
        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(QColor(200, 220, 255)));
        self.setPen(QPen(QColor(80, 80, 120), 1.2));
        self.text = QGraphicsTextItem(name, self);
        self.text.setDefaultTextColor(QColor(30, 30, 30));
        self.text.setPos(8, 4)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event);
        dialog = TableEditorDialog(self.table_id, self.controller, self.scene().views()[0])
        if dialog.exec() == QDialog.Accepted: self.update_layout(); self.scene().views()[
            0].update_connections_for_table(self)
        event.accept()

    def add_column(self, name: str, column_id: int, column_info: dict = None):
        col = ColumnItem(name, self, column_id, column_info, self.width);
        self.columns.append(col);
        self.scene().views()[0].add_column_to_map(col)

    def update_layout(self):
        for item in self.childItems():
            if isinstance(item, ColumnItem): self.scene().views()[0].remove_column_from_map(
                item); self.scene().removeItem(item)
        self.columns.clear()
        fresh_columns = self.controller.get_columns_for_table(self.table_id)
        for col_data in fresh_columns: info = {'type': col_data.data_type, 'pk': col_data.is_primary_key,
                                               'nn': not col_data.is_nullable}; self.add_column(col_data.column_name,
                                                                                                col_data.column_id,
                                                                                                info)
        height = 30 + len(self.columns) * self.row_height + 10;
        self.setRect(0, 0, self.width, height)
        for i, col in enumerate(self.columns): col.setY(30 + i * self.row_height)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and event.scenePos() != event.lastScenePos(): pos = self.pos(); self.controller.update_table_position(
            self.diagram_object_id, int(pos.x()), int(pos.y()))

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
                    if hasattr(port, 'connections'):
                        for connection in port.connections: connection.update_position()
        return super().itemChange(change, value)


class ConnectionLine(QGraphicsPathItem):
    def __init__(self, start_port, end_port, relationship_id=None):
        super().__init__()
        self.start_port, self.end_port, self.relationship_id = start_port, end_port, relationship_id;
        self.default_pen = QPen(QColor(80, 80, 80), 2);
        self.highlight_pen = QPen(QColor(0, 180, 255), 3.5);
        self.setPen(self.default_pen);
        self.setFlag(QGraphicsItem.ItemIsSelectable, True);
        self.setZValue(-1)
        for port in [start_port, end_port]:
            if not hasattr(port, 'connections'): port.connections = []; port.connections.append(self)
        self.update_position()

    def paint(self, painter, option, widget=None):
        painter.setPen(self.pen()); painter.drawPath(self.path())

    def update_position(self):
        path = QPainterPath();
        start_p = self.start_port.scenePos();
        end_p = self.end_port.scenePos();
        path.moveTo(start_p);
        dx = end_p.x() - start_p.x();
        offset = min(abs(dx) * 0.5, 100.0)
        if abs(dx) < 50: offset = 50
        start_offset = offset if self.start_port.side == 'right' else -offset;
        end_offset = -offset if self.end_port.side == 'left' else offset;
        control1 = QPointF(start_p.x() + start_offset, start_p.y());
        control2 = QPointF(end_p.x() + end_offset, end_p.y());
        path.cubicTo(control1, control2, end_p);
        self.setPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange: self.set_highlighted(value)
        return super().itemChange(change, value)

    def set_highlighted(self, highlighted: bool):
        self.setPen(self.highlight_pen if highlighted else self.default_pen);
        self.start_port.set_highlighted(highlighted);
        self.start_port.column.set_highlighted(highlighted);
        self.end_port.set_highlighted(highlighted);
        self.end_port.column.set_highlighted(highlighted)


class DiagramView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        self.setSceneRect(0, 0, 4000, 3000)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        self.controller = None
        self.current_diagram = None
        self.main_window: QMainWindow = None
        self.table_items: Dict[int, TableItem] = {}
        self.column_map: Dict[int, ColumnItem] = {}
        self.first_port: PortItem = None

    def save_project_state(self):
        if not self.controller or not self.table_items: return
        for table_item in self.table_items.values():
            pos = table_item.pos()
            self.controller.update_table_position(table_item.diagram_object_id, int(pos.x()), int(pos.y()))

        # Показываем сообщение в статус-баре на 3 секунды (3000 мс)
        if self.main_window:
            self.main_window.statusBar().showMessage("Позиции успешно сохранены.", 3000)

    def exit_to_project_selection(self):
        if self.main_window and hasattr(self.main_window, 'show_project_selection'):
            self.main_window.show_project_selection()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            self.save_project_state()
            event.accept()
        else:
            super().keyPressEvent(event)

    def clear_diagram(self):
        items_to_remove = [item for item in self.scene.items() if isinstance(item, (TableItem, ConnectionLine))]
        for item in items_to_remove: self.scene.removeItem(item)
        self.table_items.clear();
        self.column_map.clear();
        self.first_port = None

    def set_main_window(self, main_window: QMainWindow):
        self.main_window = main_window

    def set_controller(self, controller):
        self.controller = controller

    def add_column_to_map(self, col):
        self.column_map[col.column_id] = col

    def remove_column_from_map(self, col):
        if col.column_id in self.column_map: del self.column_map[col.column_id]

    def load_diagram_data(self, diagram, diagram_objects, relationships):
        self.clear_diagram();
        self.current_diagram = diagram
        for d_obj in diagram_objects:
            table = d_obj.table;
            item = TableItem(table.table_name, d_obj.pos_x, d_obj.pos_y, d_obj.object_id, table.table_id,
                             self.controller)
            self.scene.addItem(item);
            self.table_items[table.table_id] = item;
            item.update_layout()
        for rel in relationships:
            if not rel.relationship_columns: continue
            rel_col = rel.relationship_columns[0];
            start_col_item = self.column_map.get(rel_col.start_column_id);
            end_col_item = self.column_map.get(rel_col.end_column_id)
            if start_col_item and end_col_item:
                start_port = start_col_item.left_port if rel_col.start_port_side == 'left' else start_col_item.right_port
                end_port = end_col_item.right_port if rel_col.end_port_side == 'right' else end_col_item.left_port
                self.scene.addItem(ConnectionLine(start_port, end_port, rel.relationship_id));
                end_col_item.is_fk = True;
                end_col_item._update_and_elide_text()

    def update_connections_for_table(self, table_item: TableItem):
        for column in table_item.columns:
            for port in [column.left_port, column.right_port]:
                if hasattr(port, 'connections'):
                    for connection in port.connections: connection.update_position()

    def create_relationship(self, start_port: PortItem, end_port: PortItem):
        new_rel = self.controller.add_relationship(self.current_diagram.project_id, start_port.column.column_id,
                                                   end_port.column.column_id, start_port.side, end_port.side)
        if new_rel: self.scene.addItem(ConnectionLine(start_port, end_port,
                                                      new_rel.relationship_id)); end_port.column.is_fk = True; end_port.column._update_and_elide_text()

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
        name = f"New_Table_{len(self.table_items) + 1}";
        d_obj = self.controller.add_new_table_to_diagram(self.current_diagram.diagram_id,
                                                         self.current_diagram.project_id, name, int(x), int(y))
        if d_obj: item = TableItem(d_obj.table.table_name, d_obj.pos_x, d_obj.pos_y, d_obj.object_id,
                                   d_obj.table.table_id, self.controller); self.scene.addItem(item); self.table_items[
            d_obj.table.table_id] = item; item.update_layout()

    def delete_selected_tables(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, TableItem)];
        if not items: return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} таблицу(ы)?') == QMessageBox.Yes:
            for item in items: self.controller.delete_table_from_diagram(
                item.diagram_object_id); self.main_window.load_project_data()

    def delete_selected_lines(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, ConnectionLine)];
        if not items: return
        if QMessageBox.question(self, 'Подтверждение', f'Удалить {len(items)} связь(и)?') == QMessageBox.Yes:
            for item in items:
                end_column = item.end_port.column;
                self.controller.delete_relationship(item.relationship_id);
                self.scene.removeItem(item)
                is_still_fk = self.controller.is_column_foreign_key(end_column.column_id)
                if end_column.is_fk != is_still_fk: end_column.is_fk = is_still_fk; end_column._update_and_elide_text()

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
            old_pos = self.mapToScene(event.position().toPoint());
            zoom = 1.15 if delta > 0 else 1 / 1.15;
            self.scale(zoom, zoom)
            new_pos = self.mapToScene(event.position().toPoint());
            delta_scene = new_pos - old_pos;
            self.translate(delta_scene.x(), delta_scene.y())
        else:
            super().wheelEvent(event)