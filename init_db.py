import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Импортируем базовый класс и все модели, чтобы они были зарегистрированы в метаданных Base
from models import Base
from models import * # Это нужно, чтобы Python "увидел" все ваши классы моделей

def create_tables():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is required")

    engine = create_engine(DATABASE_URL)

    print("Создание таблиц в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы.")

if __name__ == "__main__":
    create_tables()