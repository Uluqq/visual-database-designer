# controllers/diagram_controller.py

from models.base import SessionLocal
from models.diagram import Diagram, DiagramObject
from models.table import Table, TableColumn
from models.project import Project, Schema
from models.relationships import Relationship, RelationshipColumn
from sqlalchemy.orm import joinedload, Session, selectinload
from sqlalchemy.sql import func


class DiagramController:
    # --- VVV --- НОВЫЙ МЕТОД --- VVV ---
    def get_diagrams_for_project(self, project_id: int) -> list[Diagram]:
        """Возвращает список всех диаграмм для указанного проекта."""
        session = SessionLocal()
        try:
            return session.query(Diagram).filter_by(project_id=project_id).order_by(Diagram.diagram_name).all()
        finally:
            session.close()

    # --- VVV --- НОВЫЙ МЕТОД --- VVV ---
    def create_diagram(self, project_id: int, name: str) -> Diagram | None:
        """Создает новую диаграмму для проекта."""
        session = SessionLocal()
        try:
            # Проверяем, есть ли уже диаграмма с таким именем в проекте
            existing = session.query(Diagram).filter_by(project_id=project_id, diagram_name=name).first()
            if existing:
                print(f"Диаграмма с именем '{name}' уже существует в этом проекте.")
                return None

            new_diagram = Diagram(project_id=project_id, diagram_name=name)
            session.add(new_diagram)
            session.commit()
            session.refresh(new_diagram)
            return new_diagram
        except Exception as e:
            session.rollback()
            print(f"Ошибка при создании диаграммы: {e}")
            return None
        finally:
            session.close()

    def get_or_create_diagram_for_project(self, project_id: int, session: Session = None) -> Diagram:
        should_close_session = False
        if session is None:
            session = SessionLocal();
            should_close_session = True
        try:
            diagram = session.query(Diagram).filter_by(project_id=project_id).first()
            if not diagram:
                diagram = Diagram(diagram_name="Main Diagram", project_id=project_id)
                session.add(diagram);
                session.commit();
                session.refresh(diagram)
            return diagram
        finally:
            if should_close_session: session.close()

    def get_diagram_details(self, diagram_id: int) -> list[DiagramObject]:
        session = SessionLocal()
        try:
            return session.query(DiagramObject).filter_by(diagram_id=diagram_id).options(
                joinedload(DiagramObject.table).joinedload(Table.columns)).all()
        finally:
            session.close()

    def add_existing_table_to_diagram(self, diagram_id: int, table_id: int, x: int, y: int,
                                      session: Session = None) -> DiagramObject:
        should_close_session = False
        if session is None:
            session = SessionLocal();
            should_close_session = True
        try:
            new_diagram_object = DiagramObject(diagram_id=diagram_id, table_id=table_id, pos_x=x, pos_y=y)
            session.add(new_diagram_object)
            if should_close_session: session.commit()
            return new_diagram_object
        except Exception as e:
            if should_close_session: session.rollback()
            return None
        finally:
            if should_close_session: session.close()

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
            new_diagram_object = self.add_existing_table_to_diagram(diagram_id, new_table.table_id, x, y,
                                                                    session=session)
            session.commit()
            session.refresh(new_diagram_object, attribute_names=['table']);
            session.refresh(new_diagram_object.table, attribute_names=['columns'])
            return new_diagram_object
        except Exception as e:
            session.rollback();
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

    def update_project_timestamp(self, project_id: int):
        session = SessionLocal()
        try:
            project = session.query(Project).filter(Project.project_id == project_id).first()
            if project: project.updated_at = func.now(); session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

    def update_table_color(self, diagram_object_id: int, color_hex: str):
        session = SessionLocal()
        try:
            obj = session.get(DiagramObject, diagram_object_id)
            if obj: obj.color = color_hex; session.commit()
        except Exception as e:
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

    def update_column_data_type(self, column_id: int, new_data_type: str):
        session = SessionLocal()
        try:
            column = session.get(TableColumn, column_id)
            if column: column.data_type = new_data_type; session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

    def get_relationships_for_project(self, project_id: int) -> list[Relationship]:
        """
        Возвращает все связи для проекта, "жадно" подгружая все необходимые
        для экспорта данные (колонки и таблицы).
        """
        session = SessionLocal()
        try:
            return session.query(Relationship).filter_by(project_id=project_id).options(
                selectinload(Relationship.relationship_columns).options(
                    joinedload(RelationshipColumn.start_column).joinedload(TableColumn.table),
                    joinedload(RelationshipColumn.end_column).joinedload(TableColumn.table)
                )
            ).all()
        finally:
            session.close()

    def add_relationship(self, project_id: int, start_col_id: int, end_col_id: int, start_port_side: str,
                         end_port_side: str) -> Relationship:
        session = SessionLocal()
        try:
            start_col = session.get(TableColumn, start_col_id);
            end_col = session.get(TableColumn, end_col_id)
            if not start_col or not end_col: return None
            constraint_name = f"fk_{start_col.table.table_name}_{end_col.table.table_name}"
            new_rel = Relationship(project_id=project_id, start_table_id=start_col.table_id,
                                   end_table_id=end_col.table_id, constraint_name=constraint_name)
            rel_col = RelationshipColumn(
                start_column_id=start_col_id, end_column_id=end_col_id,
                start_port_side=start_port_side, end_port_side=end_port_side)
            new_rel.relationship_columns.append(rel_col)
            session.add(new_rel);
            session.commit();
            session.refresh(new_rel)
            return new_rel
        except Exception as e:
            session.rollback();
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
            session.rollback();
            return False
        finally:
            session.close()

    def is_column_foreign_key(self, column_id: int) -> bool:
        session = SessionLocal()
        try:
            count = session.query(RelationshipColumn).filter_by(end_column_id=column_id).count()
            return count > 0
        finally:
            session.close()

    # controllers/diagram_controller.py

    # 1. ПРОВЕРЬТЕ ИМПОРТЫ В НАЧАЛЕ ФАЙЛА
    from models.base import SessionLocal
    from models.diagram import DiagramObject
    from models.table import Table
    # !!! ВАЖНО: Добавьте RelationshipColumn в импорт !!!
    from models.relationships import Relationship, RelationshipColumn

    # ... код класса ...

    def delete_table_completely(self, table_id: int) -> bool:
        """
        Полное удаление таблицы.
        Порядок удаления (от зависимых к главным):
        1. DiagramObject (визуальное представление)
        2. RelationshipColumn (детали связей - какие колонки связаны)
        3. Relationship (сами связи между таблицами)
        4. Table (сама таблица)
        """
        session = SessionLocal()
        try:
            # 1. Удаляем визуальные объекты (DiagramObject)
            session.query(DiagramObject).filter(DiagramObject.table_id == table_id).delete()

            # 2. Находим ID всех связей, где участвует эта таблица
            # (как родительская или как дочерняя)
            rels_to_delete = session.query(Relationship).filter(
                (Relationship.start_table_id == table_id) |
                (Relationship.end_table_id == table_id)
            ).all()

            # Собираем список ID этих связей
            rel_ids = [r.relationship_id for r in rels_to_delete]

            if rel_ids:
                # 3. Сначала удаляем детали связей (RelationshipColumn).
                # Именно это вызывало вашу ошибку.
                session.query(RelationshipColumn).filter(
                    RelationshipColumn.relationship_id.in_(rel_ids)
                ).delete(synchronize_session=False)

                # 4. Теперь безопасно удаляем сами связи (Relationship)
                session.query(Relationship).filter(
                    Relationship.relationship_id.in_(rel_ids)
                ).delete(synchronize_session=False)

            # 5. И наконец, удаляем саму таблицу
            table = session.get(Table, table_id)
            if table:
                session.delete(table)
                session.commit()
                return True
            return False

        except Exception as e:
            session.rollback()
            print(f"Критическая ошибка при удалении таблицы ID {table_id}: {e}")
            return False
        finally:
            session.close()