# controllers/diagram_controller.py
from models.base import SessionLocal
from models.diagram import DBTable, DiagramObject

def create_table(name: str, notes: str = None):
    session = SessionLocal()
    t = DBTable(table_name=name, notes=notes)
    session.add(t)
    session.commit()
    session.refresh(t)
    session.close()
    return t

def create_diagram_object(diagram_id: int, table_id: int, x: float, y: float, color: str = None):
    session = SessionLocal()
    obj = DiagramObject(diagram_id=diagram_id, table_id=table_id, pos_x=x, pos_y=y, color=color)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    session.close()
    return obj
