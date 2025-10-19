# models/diagram.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Diagram(Base):
    __tablename__ = 'diagrams'

    diagram_id = Column(Integer, primary_key=True)
    diagram_name = Column(String(100), nullable=False)

    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)

    project = relationship("Project", back_populates="diagrams")
    objects = relationship("DiagramObject", back_populates="diagram", cascade="all, delete-orphan")


class DiagramObject(Base):
    __tablename__ = 'diagramobjects'

    object_id = Column(Integer, primary_key=True)
    pos_x = Column(Integer, default=0)
    pos_y = Column(Integer, default=0)
    color = Column(String(20), nullable=True)

    diagram_id = Column(Integer, ForeignKey('diagrams.diagram_id'), nullable=False)
    table_id = Column(Integer, ForeignKey('tables.table_id'), nullable=False)  # Связь с конкретной таблицей

    diagram = relationship("Diagram", back_populates="objects")
    table = relationship("Table")  # Однонаправленная связь с таблицей, которую представляет объект