# models/base.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DB_USER = "visual_db_user"
DB_PASSWORD = "HUREHURE123hu"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "visual_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():

    Base.metadata.create_all(bind=engine)