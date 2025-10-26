# models/base.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- НАСТРОЙКА ПОДКЛЮЧЕНИЯ К POSTGRESQL ---

# Замените 'your_strong_password' на пароль, который вы создали для visual_db_user
DB_USER = "visual_db_user"
DB_PASSWORD = "HUREHURE123hu"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "visual_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем "движок" SQLAlchemy
# echo=True полезно для отладки, т.к. выводит все SQL-запросы в консоль. Потом можно убрать.
engine = create_engine(DATABASE_URL, echo=False)

# Создаем класс для сессий, который будет использоваться для всех взаимодействий с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем базовый класс, от которого будут наследоваться все модели.
Base = declarative_base()

def init_db():
    """Создает все таблицы в базе данных, если их еще нет."""
    # Эта команда просмотрит все классы, унаследованные от Base,
    # и создаст для них таблицы в БД.
    Base.metadata.create_all(bind=engine)