# controllers/table_controller.py
from models.base import SessionLocal
from models.table import Table, TableColumn, DbIndex, IndexColumn
from sqlalchemy.orm import joinedload, selectinload

class TableController:
    def get_table_details(self, table_id: int) -> Table | None:
        session = SessionLocal()
        try:
            return session.query(Table).filter_by(table_id=table_id).options(
                selectinload(Table.columns),
                selectinload(Table.indexes).selectinload(DbIndex.index_columns).joinedload(IndexColumn.column)
            ).one_or_none()
        finally:
            session.close()

    # --- VVV НОВЫЙ МЕТОД VVV ---
    def update_table_name(self, table_id: int, new_name: str):
        session = SessionLocal()
        try:
            table = session.query(Table).filter(Table.table_id == table_id).first()
            if table:
                table.table_name = new_name
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при переименовании таблицы: {e}")
        finally:
            session.close()
    # --- ^^^ ---------------- ^^^ ---

    def update_table_notes(self, table_id: int, notes: str):
        session = SessionLocal()
        try:
            table = session.query(Table).filter(Table.table_id == table_id).first()
            if table: table.notes = notes; session.commit()
        except Exception as e:
            session.rollback(); print(f"Ошибка: {e}")
        finally: session.close()

    def get_columns_for_table(self, table_id: int) -> list[TableColumn]:
        session = SessionLocal()
        try: return session.query(TableColumn).filter_by(table_id=table_id).order_by(TableColumn.column_id).all()
        finally: session.close()

    def sync_columns_for_table(self, table_id: int, columns_data: list[dict]):
        session = SessionLocal()
        try:
            existing_columns = {c.column_id: c for c in session.query(TableColumn).filter_by(table_id=table_id)}
            data_ids = {d['id'] for d in columns_data if d.get('id')}
            for col_id, col_obj in existing_columns.items():
                if col_id not in data_ids: session.delete(col_obj)
            for data in columns_data:
                col_id = data.get('id')
                if col_id in existing_columns:
                    col = existing_columns[col_id]
                    col.column_name = data['name']; col.data_type = data['type']; col.is_primary_key = data['pk']
                    col.is_nullable = not data['nn']; col.is_unique = data.get('uq', False); col.default_value = data.get('default')
                else:
                    col = TableColumn(table_id=table_id, column_name=data['name'], data_type=data['type'], is_primary_key=data['pk'], is_nullable=not data['nn'], is_unique=data.get('uq', False), default_value=data.get('default'))
                    session.add(col)
            session.commit()
        except Exception as e:
            session.rollback(); print(f"Ошибка: {e}")
        finally: session.close()

    def get_indexes_for_table(self, table_id: int) -> list[DbIndex]:
        session = SessionLocal()
        try:
            return session.query(DbIndex).filter_by(table_id=table_id).options(
                selectinload(DbIndex.index_columns).joinedload(IndexColumn.column)
            ).order_by(DbIndex.index_name).all()
        finally: session.close()

    def create_or_update_index(self, table_id: int, index_id: int | None, data: dict):
        session = SessionLocal()
        try:
            if index_id:
                index = session.query(DbIndex).filter_by(index_id=index_id).one()
                for ic in index.index_columns: session.delete(ic)
            else:
                index = DbIndex(table_id=table_id); session.add(index)
            index.index_name = data['name']; index.is_unique = data['is_unique']
            for i, col_id in enumerate(data['column_ids']):
                index.index_columns.append(IndexColumn(column_id=col_id, order=i))
            session.commit()
        except Exception as e:
            session.rollback(); print(f"Ошибка: {e}")
        finally: session.close()

    def delete_index(self, index_id: int):
        session = SessionLocal()
        try:
            index = session.query(DbIndex).filter_by(index_id=index_id).one()
            session.delete(index); session.commit()
        except Exception as e:
            session.rollback(); print(f"Ошибка: {e}")
        finally: session.close()