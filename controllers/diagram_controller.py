# controllers/diagram_controller.py

from models.base import SessionLocal
from models.diagram import Diagram, DiagramObject
from models.table import Table
from models.project import Schema  # <-- Импортируем Schema
from sqlalchemy.orm import joinedload, Session


class DiagramController:

    def get_or_create_diagram_for_project(self, project_id: int) -> Diagram:
        session = SessionLocal()
        try:
            diagram = session.query(Diagram).filter_by(project_id=project_id).first()
            if not diagram:
                diagram = Diagram(diagram_name="Main Diagram", project_id=project_id)
                session.add(diagram)
                session.commit()
                session.refresh(diagram)
            return diagram
        finally:
            session.close()

    def get_diagram_details(self, diagram_id: int) -> list[DiagramObject]:
        session = SessionLocal()
        try:
            diagram_objects = (
                session.query(DiagramObject)
                .filter_by(diagram_id=diagram_id)
                .options(joinedload(DiagramObject.table).joinedload(Table.columns))
                .all()
            )
            return diagram_objects
        finally:
            session.close()

    def add_new_table_to_diagram(self, diagram_id: int, project_id: int, table_name: str, x: int, y: int) -> (
            DiagramObject | None):
        """
        Создает новую таблицу в БД и связанный с ней объект диаграммы (позицию).
        ИЗМЕНЕНИЕ: Теперь метод принимает project_id, чтобы найти правильную схему.
        """
        session = SessionLocal()
        try:
            # 1. Находим первую попавшуюся схему для данного проекта
            target_schema = session.query(Schema).filter_by(project_id=project_id).first()
            if not target_schema:
                # Если по какой-то причине схема не найдена, прерываем операцию
                raise Exception(f"Не найдено ни одной схемы для проекта с ID {project_id}")

            # 2. Создаем саму таблицу, указывая найденный ID схемы
            new_table = Table(table_name=table_name, schema_id=target_schema.schema_id)
            session.add(new_table)
            # Нужно сделать коммит здесь, чтобы получить new_table.table_id
            session.commit()
            session.refresh(new_table)

            # 3. Создаем объект диаграммы, который хранит позицию этой таблицы
            new_diagram_object = DiagramObject(
                diagram_id=diagram_id,
                table_id=new_table.table_id,
                pos_x=x,
                pos_y=y
            )
            session.add(new_diagram_object)
            session.commit()
            session.refresh(new_diagram_object)

            # Подгружаем связанную таблицу, чтобы вернуть полный объект
            session.refresh(new_diagram_object, attribute_names=['table'])

            return new_diagram_object
        except Exception as e:
            session.rollback()
            print(f"Ошибка при добавлении таблицы на диаграмму: {e}")
            return None
        finally:
            session.close()

    def update_table_position(self, diagram_object_id: int, x: int, y: int):
        session = SessionLocal()
        try:
            obj_to_update = session.query(DiagramObject).get(diagram_object_id)
            if obj_to_update:
                obj_to_update.pos_x = x
                obj_to_update.pos_y = y
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при обновлении позиции: {e}")
        finally:
            session.close()

    def delete_table_from_diagram(self, diagram_object_id: int):
        session = SessionLocal()
        try:
            obj_to_delete = session.query(DiagramObject).get(diagram_object_id)
            if obj_to_delete:
                table_to_delete = session.query(Table).get(obj_to_delete.table_id)
                if table_to_delete:
                    session.delete(table_to_delete)
                session.delete(obj_to_delete)
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при удалении таблицы: {e}")
        finally:
            session.close()