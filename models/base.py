# models/base.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Загружаем переменные из файла .env
load_dotenv()

# 2. Читаем настройки (или берем дефолтные, если .env нет)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "visual_db")
DB_USER = os.getenv("DB_USER", "visual_db_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "HUREHURE123hu")

# Формируем строку подключения
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем движок
# echo=False, чтобы не засорять консоль SQL-логами
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Создает все таблицы в базе данных, если их еще нет."""
    Base.metadata.create_all(bind=engine)