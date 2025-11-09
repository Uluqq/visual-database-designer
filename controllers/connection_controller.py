# controllers/connection_controller.py

from models.base import SessionLocal
from models.user import Connection


class ConnectionController:
    def get_connections_for_user(self, user_id: int) -> list[Connection]:
        session = SessionLocal()
        try:
            return session.query(Connection).filter_by(user_id=user_id).order_by(Connection.connection_name).all()
        finally:
            session.close()

    # --- ИЗМЕНЕНИЕ: Убираем dbname из аргументов ---
    def add_connection(self, user_id, name, host, port, user, password, **kwargs) -> (Connection | None, str):
        session = SessionLocal()
        try:
            existing = session.query(Connection).filter_by(user_id=user_id, connection_name=name).first()
            if existing:
                return None, "Подключение с таким именем уже существует."
            new_conn = Connection(
                user_id=user_id, connection_name=name, host=host, port=int(port),
                db_username=user, db_password_hash=password
            )
            session.add(new_conn);
            session.commit();
            session.refresh(new_conn)
            return new_conn, "Подключение успешно сохранено."
        except Exception as e:
            session.rollback()
            return None, f"Ошибка при сохранении подключения: {e}"
        finally:
            session.close()