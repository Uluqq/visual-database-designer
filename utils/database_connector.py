# utils/database_connector.py
import pymysql
from typing import List


class DatabaseConnector:
    """Класс для управления подключением к MySQL и получения списка БД."""

    def __init__(self):
        self.connection = None

    def get_database_list(self, host: str, port: int, user: str, password: str) -> List[str]:
        """
        Устанавливает соединение и возвращает список всех баз данных.

        :raises Exception: Если соединение не удалось.
        """
        try:
            # Попытка подключения к серверу без выбора конкретной БД
            # Используем local_infile=True для совместимости с некоторыми версиями MySQL/MariaDB
            self.connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5  # Устанавливаем таймаут подключения
            )

            with self.connection.cursor() as cursor:
                # SQL-запрос для получения списка баз данных
                sql = "SHOW DATABASES;"
                cursor.execute(sql)
                result = cursor.fetchall()

                # Извлекаем имена баз данных
                db_list = [row['Database'] for row in result]
                return db_list

        except pymysql.err.OperationalError as e:
            # Преобразуем ошибку pymysql в более понятное сообщение
            raise Exception(f"Ошибка подключения к базе данных. Проверьте хост, порт, логин и пароль. Детали: {e}")
        except Exception as e:
            raise Exception(f"Произошла непредвиденная ошибка: {e}")
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None