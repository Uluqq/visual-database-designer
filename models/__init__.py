# models/__init__.py
from .base import Base
from .user import User, Connection
from .project import Project, Schema
from .diagram import Diagram, DiagramObject
# ИЗМЕНЕНО: импортируем TableColumn вместо Column
from .table import Table, TableColumn, DbIndex, IndexColumn
from .relationships import Relationship, RelationshipColumn

__all__ = [
    'Base',
    'User',
    'Connection',
    'Project',
    'Schema',
    'Diagram',
    'DiagramObject',
    'Table',
    'TableColumn', # ИЗМЕНЕНО
    'DbIndex',
    'IndexColumn',
    'Relationship',
    'RelationshipColumn',
]