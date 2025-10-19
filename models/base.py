# models/base.py
from sqlalchemy.orm import declarative_base

# Создаем базовый класс, от которого будут наследоваться все модели.
# SQLAlchemy будет использовать метаданные этого класса для создания таблиц.
Base = declarative_base()