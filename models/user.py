# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hash_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}')>"


class Connection(Base):
    __tablename__ = 'connections'

    connection_id = Column(Integer, primary_key=True)
    connection_name = Column(String(100), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    db_username = Column(String(100), nullable=False)
    db_password_hash = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    user = relationship("User", back_populates="connections")

    def __repr__(self):
        return f"<Connection(id={self.connection_id}, name='{self.connection_name}')>"