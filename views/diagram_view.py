from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QMenu, QGraphicsPathItem,
    QGraphicsEllipseItem, QGraphicsTextItem
)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, QEasingCurve
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath, QPainter
from typing import Dict, Any, List  # <<< ИСПРАВЛЕНО: Добавлен импорт типов


# --- ПОРТ (точка для соединения) ---
class PortItem(QGraphicsEllipseItem):
    # ... (код PortItem) ...
    def __init__(self, parent_column, side='left'):
        super().__init__(-4, -4, 8, 8, parent_column)
        self.column = parent_column
        self.side = side
        self.is_right = (side == 'right')
        self.default_brush = QBrush(QColor(100, 180, 255))
        self.hover_brush = QBrush(QColor(120, 200, 255))
        self.setBrush(self.default_brush)
        self.setPen(QPen(Qt.NoPen))
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        self.setVisible(False)  # 🔹 изначально скрыт
        self.update_position()

    def update_position(self):
        r = self.column.rect()
        if self.side == 'left':
            self.setPos(r.left(), r.center().y())
        else:
            self.setPos(r.right(), r.center().y())

    def hoverEnterEvent(self, event):
        self.setBrush(self.hover_brush)
        self.setRect(-5, -5, 10, 10)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush)
        self.setRect(-4, -4, 8, 8)
        super().hoverLeaveEvent(event)


# --- ЯЧЕЙКА (атрибут) ---
# -------------------------
# ColumnItem (обновлённый)
# -------------------------
# --- ЯЧЕЙКА (атрибут) ---
# --- ЯЧЕЙКА (атрибут) ---
class ColumnItem(QGraphicsRectItem):
    def __init__(self, name, y_offset, parent_table, width=300, height=26, column_info=None):
        super().__init__(QRectF(6, y_offset, width - 12, height), parent_table)
        self.parent_table = parent_table
        self.setBrush(QBrush(QColor(250, 250, 250)))
        self.setPen(QPen(QColor(0, 0, 0), 1.0))
        self.setZValue(1)
        self.setFlags(QGraphicsRectItem.ItemIsSelectable)

        # --- данные колонки ---
        attr_name = column_info.get("name") if column_info else name
        attr_type = column_info.get("type", "unknown") if column_info else "unknown"

        # Формируем статус: PK, FK, NN, N
        status_flags = []
        if column_info:
            if column_info.get("is_pk"):
                status_flags.append("PK")
            if column_info.get("is_fk"):
                status_flags.append("FK")
            if column_info.get("not_null"):
                status_flags.append("NN")
            else:
                status_flags.append("N")
        status = ", ".join(status_flags) if status_flags else ""

        # --- три текстовых элемента ---
        self.name_item = QGraphicsTextItem(attr_name, self)
        self.name_item.setDefaultTextColor(QColor(30, 30, 30))
        self.name_item.setPos(10, 2)

        self.type_item = QGraphicsTextItem(attr_type, self)
        self.type_item.setDefaultTextColor(QColor(70, 70, 70))
        self.type_item.setPos(130, 2)

        self.status_item = QGraphicsTextItem(status, self)
        self.status_item.setDefaultTextColor(QColor(100, 100, 100))
        self.status_item.setPos(230, 2)

        for item in (self.name_item, self.type_item, self.status_item):
            item.setZValue(2)
            item.setTextInteractionFlags(Qt.NoTextInteraction)

        # --- два порта ---
        self.left_port = PortItem(self, 'left')
        self.right_port = PortItem(self, 'right')

    def paint(self, painter, option, widget=None):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())

        # 🔹 линии-разделители между столбцами
        r = self.rect()
        painter.setPen(QPen(QColor(200, 200, 200), 0.8))
        painter.drawLine(r.left() + 120, r.top(), r.left() + 120, r.bottom())
        painter.drawLine(r.left() + 220, r.top(), r.left() + 220, r.bottom())

    def set_editable(self, editable: bool):
        for item in (self.name_item, self.type_item, self.status_item):
            item.setTextInteractionFlags(Qt.TextEditorInteraction if editable else Qt.NoTextInteraction)
        if editable:
            self.name_item.setFocus()

    def mouseDoubleClickEvent(self, event):
        self.set_editable(True)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.set_editable(False)
        super().focusOutEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            self.left_port.update_position()
            self.right_port.update_position()
            for conn in list(getattr(self.left_port, "connections", [])) + list(
                    getattr(self.right_port, "connections", [])):
                try:
                    conn.update_position()
                except Exception:
                    pass
        return super().itemChange(change, value)


# --- КНОПКИ + / - ---
class AddButton(QGraphicsEllipseItem):
    def __init__(self, parent_table, side='right'):
        super().__init__(-10, -10, 20, 20, parent_table)
        self.table = parent_table
        self.side = side
        self.setBrush(QBrush(QColor(100, 180, 255)))
        self.setPen(QPen(QColor(50, 120, 200), 1))
        self.setZValue(20)
        self.setVisible(False)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(120, 200, 255)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(100, 180, 255)))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.side == 'right':
            self.table.add_column()
        else:
            self.table.remove_last_column()
        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(Qt.white)
        painter.drawText(self.rect(), Qt.AlignCenter, "+" if self.side == 'right' else "−")


# -------------------------
# TableItem (обновлённый)
# -------------------------
class TableItem(QGraphicsRectItem):
    def __init__(self, name, x, y, width=300, height=60):  # ИСПРАВЛЕНИЕ 1: Увеличена ширина по умолчанию с 200 до 300
        super().__init__(QRectF(0, 0, width, height))
        self.connections = []  # список соединений, привязанных к таблице (будет заполняться при создании ConnectionLine)
        self.columns = []
        self.column_map = {}  # Добавим карту для быстрого поиска колонок по имени
        self.width = width
        self.row_height = 28
        self.setBrush(QBrush(QColor(200, 220, 255)))
        self.setPen(QPen(QColor(80, 80, 120), 1.2))
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setPos(x, y)
        self.setAcceptHoverEvents(True)

        self.text = QGraphicsTextItem(name, self)
        self.text.setDefaultTextColor(QColor(30, 30, 30))
        self.text.setPos(8, 4)
        self.table_name = name  # Сохраняем имя таблицы

        # кнопки + и -
        self.add_button = AddButton(self, 'right')
        self.remove_button = AddButton(self, 'left')
        self.update_button_positions()

    def hoverEnterEvent(self, event):
        self.add_button.setVisible(True)
        self.remove_button.setVisible(True)
        for c in self.columns:
            c.left_port.setVisible(True)
            c.right_port.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.add_button.setVisible(False)
        self.remove_button.setVisible(False)
        for c in self.columns:
            c.left_port.setVisible(False)
            c.right_port.setVisible(False)
        super().hoverLeaveEvent(event)

    def update_button_positions(self):
        r = self.rect()
        y = r.bottom() - 18
        self.add_button.setPos(r.right() - 18, y)
        self.remove_button.setPos(r.left() + 18, y)

    def add_column(self, name=None, column_info=None):
        if name is None:
            name = f"col_{len(self.columns) + 1}"

        y = 26 + len(self.columns) * self.row_height
        col = ColumnItem(name, y, self, self.width, self.row_height, column_info=column_info)
        self.columns.append(col)
        self.column_map[name] = col
        self.update_size()
        self.update_button_positions()
        return col

    def remove_last_column(self):
        if not self.columns:
            return
        col = self.columns.pop()
        # Удаляем из карты
        # Примечание: тут используется упрощенный способ извлечения имени, который может быть неточен,
        # если имя колонки содержит пробелы или скобки, но для генерации из БД это ОК.

        # ИСПРАВЛЕНИЕ 3: Использовать name_item вместо несуществующего text_item
        original_name = col.name_item.toPlainText()

        if original_name in self.column_map:
            del self.column_map[original_name]

        # удаляем линии, привязанные к этой колонке (их может быть немного)
        for line in list(getattr(self.connections, '__iter__', lambda: [])()):
            # старая логика могла не работать; безопасно пробегаем все и удаляем те, что ссылаются на удаляемую колонку
            if getattr(line, 'start_item', None) in (getattr(col, 'left_port', None),
                                                     getattr(col, 'right_port', None)) or \
                    getattr(line, 'end_item', None) in (getattr(col, 'left_port', None),
                                                        getattr(col, 'right_port', None)):
                try:
                    self.scene().removeItem(line)
                except Exception:
                    pass
        try:
            self.scene().removeItem(col)
        except Exception:
            pass
        self.update_size()
        self.update_button_positions()

    def update_size(self):
        """Пересчитывает высоту таблицы и обновляет позиции колонок и портов."""
        new_height = 30 + len(self.columns) * self.row_height + 22
        self.setRect(0, 0, self.width, new_height)

        for idx, c in enumerate(self.columns):
            new_y = 26 + idx * self.row_height
            c.setRect(QRectF(6, new_y, self.width - 12, self.row_height))

            # текст теперь сам позиционируется внутри, поэтому без new_y
            c.name_item.setPos(10, new_y + 2)
            c.type_item.setPos(130, new_y + 2)
            c.status_item.setPos(230, new_y + 2)

            # обновляем позиции портов
            c.left_port.update_position()
            c.right_port.update_position()

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            # обновляем порты и все линии, привязанные к таблице
            for c in self.columns:
                c.left_port.update_position()
                c.right_port.update_position()
            for line in list(getattr(self, "connections", [])):
                try:
                    line.update_position()
                except Exception:
                    pass
        return super().itemChange(change, value)


# -------------------------
# ConnectionLine
# -------------------------
class ConnectionLine(QGraphicsPathItem):
    """Линия связи с выделением и подсветкой связанных ячеек (по границе)"""

    def __init__(self, start_item, start_side, end_item, end_side):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.start_side = start_side
        self.end_side = end_side

        self.default_pen = QPen(QColor(50, 50, 50), 2)
        self.highlight_pen = QPen(QColor(0, 200, 0), 3)
        self.setPen(self.default_pen)

        # кликабельность и селект
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsPathItem.ItemIsFocusable, True)

        # Привязываем соединение к портам
        if not hasattr(self.start_item, "connections"):
            self.start_item.connections = []
        if not hasattr(self.end_item, "connections"):
            self.end_item.connections = []
        self.start_item.connections.append(self)
        self.end_item.connections.append(self)

        # Привязываем соединение также к колонкам и таблицам, чтобы их itemChange могли обновлять линии
        for port in (self.start_item, self.end_item):
            col = getattr(port, "column", None)
            if col is not None:
                if not hasattr(col, "connections"):
                    col.connections = []
                col.connections.append(self)
                table = getattr(col, "parent_table", None)
                if table is not None:
                    if not hasattr(table, "connections"):
                        table.connections = []
                    table.connections.append(self)

        self.full_path = None
        self.animating = False
        self.update_position()
        # self.animate_drawing() # Отключаем анимацию для быстрого реверс-инжиниринга

    def get_anchor_point(self, item, side):
        # Примечание: Поскольку item здесь является PortItem, scenePos() более точно отражает точку привязки.
        # Однако, сохраняем оригинальную структуру, если она предполагалась для других типов элементов.
        rect = item.sceneBoundingRect()
        if side == 'left':
            return QPointF(rect.left(), rect.center().y())
        elif side == 'right':
            return QPointF(rect.right(), rect.center().y())
        elif side == 'top':
            return QPointF(rect.center().x(), rect.top())
        elif side == 'bottom':
            return QPointF(rect.center().x(), rect.bottom())

    def update_position(self):
        # Используем scenePos() для PortItem, так как это центр порта
        start = self.start_item.scenePos()
        end = self.end_item.scenePos()
        path = QPainterPath(start)
        offset = 20

        # алгоритм построения аналогичен твоему: отступ от порта, затем L-образный маршрут
        if self.start_item.side == 'right':
            p1 = QPointF(start.x() + offset, start.y())
        elif self.start_item.side == 'left':
            p1 = QPointF(start.x() - offset, start.y())
        else:
            p1 = start

        if self.end_item.side == 'right':
            p4 = QPointF(end.x() + offset, end.y())
        elif self.end_item.side == 'left':
            p4 = QPointF(end.x() - offset, end.y())
        else:
            p4 = end

        # Используем горизонтальный путь, если возможно, иначе вертикальный
        if abs(start.y() - end.y()) < 50:  # Если таблицы близко по Y, делаем прямой путь
            mid_x = (p1.x() + p4.x()) / 2
            path.lineTo(p1)
            path.lineTo(mid_x, p1.y())
            path.lineTo(mid_x, p4.y())
            path.lineTo(p4)
            path.lineTo(end)
        else:  # Иначе используем L-образный маршрут с серединой Y
            mid_y = (start.y() + end.y()) / 2
            path.lineTo(p1)
            path.lineTo(p1.x(), mid_y)
            path.lineTo(p4.x(), mid_y)
            path.lineTo(p4)
            path.lineTo(end)

        self.full_path = path
        if not getattr(self, "animating", False):
            self.setPath(path)

    def animate_drawing(self):
        if not self.full_path:
            return
        self.animating = True
        steps = 25
        interval_ms = 6
        curve = QEasingCurve(QEasingCurve.OutCubic)
        total_samples = 40
        frame = {'i': 0}
        timer = QTimer()

        def on_frame():
            i = frame['i']
            t = i / steps
            progress = curve.valueForProgress(t)
            samples = max(1, int(progress * total_samples))
            path_portion = QPainterPath()
            for s in range(samples + 1):
                frac = (s / samples) * progress
                pt = self.full_path.pointAtPercent(frac)
                if s == 0:
                    path_portion.moveTo(pt)
                else:
                    path_portion.lineTo(pt)
            self.setPath(path_portion)
            frame['i'] += 1
            if frame['i'] > steps:
                timer.stop()
                self.setPath(self.full_path)
                self.animating = False

        timer.timeout.connect(on_frame)
        timer.start(interval_ms)
        self._anim_timer = timer

    def shape(self):
        # используем stroker для адекватной кликабельной области; fallback на bounding rect
        try:
            from PySide6.QtGui import QPainterPathStroker
            stroker = QPainterPathStroker()
            stroker.setWidth(8)
            return stroker.createStroke(self.path())
        except Exception:
            r = self.path().boundingRect().adjusted(-5, -5, 5, 5)
            p = QPainterPath()
            p.addRect(r)
            return p

    def mousePressEvent(self, event):
        # выделяем линию при клике
        self.setSelected(True)
        event.accept()

    def setSelected(self, selected):
        # подсветка линии + подсветка границ колонок и портов
        super().setSelected(selected)
        self.setPen(self.highlight_pen if selected else self.default_pen)

        border_color = QColor(0, 200, 0) if selected else QColor(0, 0, 0)
        # подсветить соответствующие колонки
        for port in (self.start_item, self.end_item):
            col = getattr(port, "column", None)
            if isinstance(col, QGraphicsRectItem):
                pen = col.pen()
                pen.setColor(border_color)
                pen.setWidth(2 if selected else 1)
                col.setPen(pen)
                col.update()
            # подсветить порт
            try:
                # PortItem хранит default_brush
                if selected:
                    port.setBrush(QBrush(QColor(0, 200, 0)))
                else:
                    # вернуть к дефолту, если есть
                    port.setBrush(getattr(port, "default_brush", QBrush(QColor(100, 180, 255))))
            except Exception:
                pass

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen())
        painter.drawPath(self.path())


# -------------------------
# DiagramView (обновлённый: добавление load_schema)
# -------------------------
class DiagramView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHints(self.renderHints() | QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        self.setSceneRect(0, 0, 4000, 3000)
        self.table_counter = 1
        self.connect_mode = True  # у тебя раньше было True — оставил как до этого
        self.first_port = None
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setInteractive(True)
        self.setFocusPolicy(Qt.ClickFocus)

        # Карта для быстрого доступа к объектам TableItem по имени таблицы
        self.table_items: Dict[str, TableItem] = {}

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        painter.setPen(QColor(220, 220, 220))
        step = 25
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)
        for x in range(left, int(rect.right()), step):
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for y in range(top, int(rect.bottom()), step):
            painter.drawLine(rect.left(), y, rect.right(), y)

    def mousePressEvent(self, event):
        # если клик по пустому месту — снять все выделения
        if event.button() == Qt.LeftButton and not self.itemAt(event.pos()):
            for it in list(self.scene.selectedItems()):
                it.setSelected(False)

        # режим соединений через порты
        if self.connect_mode and event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            # кликаем по порту (PortItem)
            if isinstance(item, PortItem):
                if not self.first_port:
                    self.first_port = item
                else:
                    # создаём линию между двумя портами
                    line = ConnectionLine(self.first_port, self.first_port.side, item, item.side)
                    self.scene.addItem(line)
                    self.first_port = None
                    return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, TableItem):
            return
        menu = QMenu()
        add_action = menu.addAction("Добавить таблицу")
        delete_action = menu.addAction("Удалить выбранное")
        selected_action = menu.exec(event.globalPos())
        if selected_action == add_action:
            self.add_table_at(event)
        elif selected_action == delete_action:
            for it in list(self.scene.selectedItems()):
                self.scene.removeItem(it)

    def add_table_at(self, event):
        if event is None:
            # Если вызывается из тулбара, размещаем в центре видимой области
            center = self.mapToScene(self.viewport().rect().center())
            pos = center
        else:
            pos = self.mapToScene(event.pos())

        table = TableItem(f"Table_{self.table_counter}", pos.x(), pos.y())
        self.scene.addItem(table)
        self.table_items[table.table_name] = table
        self.table_counter += 1
        table.add_column("col_1")
        table.add_column("col_2")
        return table  # Возвращаем созданную таблицу

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            old_pos = self.mapToScene(event.position().toPoint())
            zoom = 1.25 if delta > 0 else 0.8
            self.scale(zoom, zoom)
            new_pos = self.mapToScene(event.position().toPoint())
            delta_scene = new_pos - old_pos
            self.translate(delta_scene.x(), delta_scene.y())
        elif modifiers & Qt.ShiftModifier:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta / 2)
        else:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta / 2)

    def clear_diagram(self):
        """Очищает текущую диаграмму."""
        self.scene.clear()
        self.table_items = {}
        self.table_counter = 1

    def load_schema(self, schema_data: Dict[str, Any]):
        """
        Загружает схему БД, создавая TableItems и ConnectionLines.
        """
        self.clear_diagram()

        tables = schema_data.get('tables', [])
        columns_data = schema_data.get('columns', {})
        foreign_keys = schema_data.get('foreign_keys', [])

        # 1. Создание таблиц и колонок
        x_offset = 50
        y_offset = 50
        row_height_limit = 800  # Максимальная высота ряда перед переходом на новую колонку

        for table_name in tables:
            # Простая эвристика для размещения:
            if y_offset > row_height_limit:
                x_offset += 350  # ИСПРАВЛЕНИЕ 2: Увеличен шаг смещения по X (300 ширина + 50 отступ)
                y_offset = 50

            table_item = TableItem(table_name, x_offset, y_offset)
            self.scene.addItem(table_item)
            self.table_items[table_name] = table_item

            # Добавление колонок
            cols = columns_data.get(table_name, [])
            for col_info in cols:
                # В качестве имени передаем оригинальное имя колонки, а форматирование происходит внутри add_column
                table_item.add_column(col_info['name'], col_info)

            # Обновление смещения Y для следующей таблицы
            y_offset += table_item.rect().height() + 30

        # 2. Создание связей (Foreign Keys)
        for fk in foreign_keys:
            source_table_name = fk['source_table']
            source_col_name = fk['source_column']
            target_table_name = fk['target_table']
            target_col_name = fk['target_column']

            if source_table_name in self.table_items and target_table_name in self.table_items:
                source_table = self.table_items[source_table_name]
                target_table = self.table_items[target_table_name]

                # Находим ColumnItem по имени колонки
                # Используем column_map, где ключи — оригинальные имена колонок
                source_col_item = source_table.column_map.get(source_col_name)
                target_col_item = target_table.column_map.get(target_col_name)

                if source_col_item and target_col_item:
                    # Устанавливаем связь: от правого порта источника к левому порту цели

                    start_port = source_col_item.right_port
                    end_port = target_col_item.left_port

                    line = ConnectionLine(start_port, 'right', end_port, 'left')
                    self.scene.addItem(line)

                    print(
                        f"Создана связь: {source_table_name}.{source_col_name} -> {target_table_name}.{target_col_name}")