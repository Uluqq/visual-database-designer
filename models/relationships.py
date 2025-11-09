# models/relationships.py
from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from .base import Base


class Relationship(Base):
    __tablename__ = 'relationships'

    relationship_id = Column(Integer, primary_key=True)
    constraint_name = Column(String(100), nullable=True)

    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    start_table_id = Column(Integer, ForeignKey('tables.table_id'), nullable=False)
    end_table_id = Column(Integer, ForeignKey('tables.table_id'), nullable=False)

    project = relationship("Project", back_populates="relationships")

    start_table = relationship("Table", foreign_keys=[start_table_id], back_populates="start_relationships")
    end_table = relationship("Table", foreign_keys=[end_table_id], back_populates="end_relationships")

    relationship_columns = relationship("RelationshipColumn", back_populates="parent_relationship",
                                        cascade="all, delete-orphan")


class RelationshipColumn(Base):
    __tablename__ = 'relationshipsColumns'

    __table_args__ = (
        PrimaryKeyConstraint('relationship_id', 'start_column_id', 'end_column_id'),
    )

    relationship_id = Column(Integer, ForeignKey('relationships.relationship_id'))
    start_column_id = Column(Integer, ForeignKey('columns.column_id'))
    end_column_id = Column(Integer, ForeignKey('columns.column_id'))

    # V-- ДОБАВЬТЕ ЭТИ ДВА СТОЛБЦА --V
    start_port_side = Column(String(5), nullable=False, server_default='right')  # 'left' or 'right'
    end_port_side = Column(String(5), nullable=False, server_default='left')    # 'left' or 'right'
    # ^-- КОНЕЦ ДОБАВЛЕНИЯ --^

    parent_relationship = relationship("Relationship", back_populates="relationship_columns")

    start_column = relationship("TableColumn", foreign_keys=[start_column_id])
    end_column = relationship("TableColumn", foreign_keys=[end_column_id])