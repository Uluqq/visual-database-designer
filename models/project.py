# models/project.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Project(Base):
    __tablename__ = 'projects'

    project_id = Column(Integer, primary_key=True)
    project_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)

    user = relationship("User", back_populates="projects")

    # Связи "один ко многим"
    schemas = relationship("Schema", back_populates="project", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="project", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.project_id}, name='{self.project_name}')>"


class Schema(Base):
    __tablename__ = 'schemas'

    schema_id = Column(Integer, primary_key=True)
    schema_name = Column(String(100), nullable=False)

    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)

    project = relationship("Project", back_populates="schemas")
    tables = relationship("Table", back_populates="schema", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Schema(id={self.schema_id}, name='{self.schema_name}')>"