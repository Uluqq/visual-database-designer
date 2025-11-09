# controllers/diagram_controller.py

from models.base import SessionLocal
from models.diagram import Diagram, DiagramObject
from models.table import Table, TableColumn
from models.project import Schema
from models.relationships import Relationship, RelationshipColumn
from sqlalchemy.orm import joinedload


class DiagramController:
    def get_or_create_diagram_for_project(self, project_id: int) -> Diagram:
        session = SessionLocal()
        try:
            diagram = session.query(Diagram).filter_by(project_id=project_id).first()
            if not diagram:
                diagram = Diagram(diagram_name="Main Diagram", project_id=project_id)
                session.add(diagram);
                session.commit();
                session.refresh(diagram)
            return diagram
        finally:
            session.close()

    def get_diagram_details(self, diagram_id: int) -> list[DiagramObject]:
        session = SessionLocal()
        try:
            return session.query(DiagramObject).filter_by(diagram_id=diagram_id).options(
                joinedload(DiagramObject.table).joinedload(Table.columns)).all()
        finally:
            session.close()

    def add_new_table_to_diagram(self, diagram_id: int, project_id: int, table_name: str, x: int, y: int) -> (
            DiagramObject | None):
        session = SessionLocal()
        try:
            target_schema = session.query(Schema).filter_by(project_id=project_id).first()
            if not target_schema: raise Exception(f"Не найдено схемы для проекта {project_id}")

            new_table = Table(table_name=table_name, schema_id=target_schema.schema_id)
            session.add(new_table);
            session.commit();
            session.refresh(new_table)

            default_col = TableColumn(column_name="id", data_type="integer", table_id=new_table.table_id,
                                      is_primary_key=True, is_nullable=False)
            session.add(default_col);
            session.commit()

            new_diagram_object = DiagramObject(diagram_id=diagram_id, table_id=new_table.table_id, pos_x=x, pos_y=y)
            session.add(new_diagram_object);
            session.commit()

            session.refresh(new_diagram_object, attribute_names=['table'])
            session.refresh(new_diagram_object.table, attribute_names=['columns'])
            return new_diagram_object
        except Exception as e:
            session.rollback();
            print(f"Ошибка при добавлении таблицы: {e}");
            return None
        finally:
            session.close()

    def update_table_position(self, diagram_object_id: int, x: int, y: int):
        session = SessionLocal()
        try:
            obj = session.get(DiagramObject, diagram_object_id)
            if obj: obj.pos_x = x; obj.pos_y = y; session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def delete_table_from_diagram(self, diagram_object_id: int):
        session = SessionLocal()
        try:
            obj = session.get(DiagramObject, diagram_object_id)
            if obj: session.delete(obj); session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def get_columns_for_table(self, table_id: int) -> list[TableColumn]:
        session = SessionLocal()
        try:
            return session.query(TableColumn).filter_by(table_id=table_id).order_by(TableColumn.column_id).all()
        finally:
            session.close()

    def sync_columns_for_table(self, table_id: int, columns_data: list[dict]):
        session = SessionLocal()
        try:
            existing_columns = {c.column_id: c for c in session.query(TableColumn).filter_by(table_id=table_id)}
            data_ids = {d['id'] for d in columns_data if d.get('id')}

            for col_id, col_obj in existing_columns.items():
                if col_id not in data_ids:
                    session.delete(col_obj)

            for data in columns_data:
                col_id = data.get('id')
                if col_id in existing_columns:
                    col = existing_columns[col_id]
                    col.column_name = data['name']
                    col.data_type = data['type']
                    col.is_primary_key = data['pk']
                    col.is_nullable = not data['nn']
                    col.is_unique = data.get('uq', False)  # Обрабатываем ключ 'uq'
                else:
                    col = TableColumn(table_id=table_id, column_name=data['name'], data_type=data['type'],
                                      is_primary_key=data['pk'], is_nullable=not data['nn'],
                                      is_unique=data.get('uq', False)) # Обрабатываем ключ 'uq'
                    session.add(col)
            session.commit()
        except Exception as e:
            session.rollback();
            print(f"Ошибка при синхронизации колонок: {e}")
        finally:
            session.close()

    def update_column_data_type(self, column_id: int, new_data_type: str):
        """Обновляет только тип данных для одной колонки."""
        session = SessionLocal()
        try:
            column = session.get(TableColumn, column_id)
            if column:
                column.data_type = new_data_type
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при обновлении типа данных колонки: {e}")
        finally:
            session.close()

    def get_relationships_for_project(self, project_id: int) -> list[Relationship]:
        session = SessionLocal()
        try:
            return session.query(Relationship).filter_by(project_id=project_id).options(
                joinedload(Relationship.relationship_columns)).all()
        finally:
            session.close()

    def add_relationship(self, project_id: int, start_col_id: int, end_col_id: int) -> Relationship:
        session = SessionLocal()
        try:
            start_col = session.get(TableColumn, start_col_id)
            end_col = session.get(TableColumn, end_col_id)
            if not start_col or not end_col: return None
            constraint_name = f"fk_{start_col.table.table_name}_{end_col.table.table_name}"
            new_rel = Relationship(project_id=project_id, start_table_id=start_col.table_id,
                                   end_table_id=end_col.table_id, constraint_name=constraint_name)
            rel_col = RelationshipColumn(start_column_id=start_col_id, end_column_id=end_col_id)
            new_rel.relationship_columns.append(rel_col)
            session.add(new_rel);
            session.commit();
            session.refresh(new_rel)
            return new_rel
        except Exception as e:
            session.rollback();
            print(f"Ошибка при создании связи: {e}");
            return None
        finally:
            session.close()

    def delete_relationship(self, relationship_id: int) -> bool:
        session = SessionLocal()
        try:
            rel = session.get(Relationship, relationship_id)
            if rel: session.delete(rel); session.commit(); return True
            return False
        except Exception:
            session.rollback(); return False
        finally:
            session.close()

    def is_column_foreign_key(self, column_id: int) -> bool:

        session = SessionLocal()
        try:
            count = session.query(RelationshipColumn).filter_by(end_column_id=column_id).count()
            return count > 0
        finally:
            session.close()