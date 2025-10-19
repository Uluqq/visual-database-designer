# models/table.py
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, PrimaryKeyConstraint
)
from sqlalchemy.orm import relationship
from .base import Base


class Table(Base):
    __tablename__ = 'tables'
    table_id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    schema_id = Column(Integer, ForeignKey('schemas.schema_id'), nullable=False)

    schema = relationship("Schema", back_populates="tables")
    columns = relationship("TableColumn", back_populates="table", cascade="all, delete-orphan")
    indexes = relationship("DbIndex", back_populates="table", cascade="all, delete-orphan")

    # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
    # Заменяем синтаксис "[ClassName.column]" на "ClassName.column"
    # Это помогает SQLAlchemy лучше разрешать циклические зависимости.
    start_relationships = relationship("Relationship", foreign_keys="Relationship.start_table_id",
                                       back_populates="start_table")
    end_relationships = relationship("Relationship", foreign_keys="Relationship.end_table_id",
                                     back_populates="end_table")


class TableColumn(Base):
    __tablename__ = 'columns'
    column_id = Column(Integer, primary_key=True)
    column_name = Column(String(100), nullable=False)
    data_type = Column(String(50), nullable=False)
    col_num = Column(Integer)
    is_nullable = Column(Boolean, default=True, nullable=False)
    default_value = Column(String(255), nullable=True)
    table_id = Column(Integer, ForeignKey('tables.table_id'), nullable=False)
    table = relationship("Table", back_populates="columns")


class DbIndex(Base):
    __tablename__ = 'indexes'
    index_id = Column(Integer, primary_key=True)
    index_name = Column(String(100), nullable=False)
    is_primarykey = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    table_id = Column(Integer, ForeignKey('tables.table_id'), nullable=False)
    table = relationship("Table", back_populates="indexes")
    index_columns = relationship("IndexColumn", back_populates="index", cascade="all, delete-orphan")


class IndexColumn(Base):
    __tablename__ = 'indexColumns'
    index_id = Column(Integer, ForeignKey('indexes.index_id'), primary_key=True)
    column_id = Column(Integer, ForeignKey('columns.column_id'), primary_key=True)
    order = Column(Integer)
    index = relationship("DbIndex", back_populates="index_columns")
    column = relationship("TableColumn")