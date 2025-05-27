from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import URL
from datetime import datetime

# Define database connection parameters
DATABASE = {
    'drivername': 'mysql',  # Or 'mysql', 'sqlite', etc.
    'host': 'localhost',
    'port': '3306',
    'username': 'root',
    'password': '123quan123',
    'database': 'hanoicinema'
}


def db_connect():
    """
    Creates database connection using database settings from settings.py
    Returns sqlalchemy engine instance
    """
    return create_engine(URL.create(**DATABASE))


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


def create_table(engine):
    """
    Create the tables if they don't exist
    """
    Base.metadata.create_all(engine)

# Define your items as SQLAlchemy models


class Film(Base):
    __tablename__ = "films"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=True)
    age_limit = Column(String(100), nullable=True)
    movie_type = Column(String(100), nullable=True)
    format = Column(String(100), nullable=True)
    genre = Column(String(100), nullable=True)
    image_url = Column(Text)
    price = Column(String(30))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class Screentime(Base):
    __tablename__ = "cinemas"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    location = Column(String(100))
    screentime = Column(String(100))
    date = Column(DateTime)
    cinema_id = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
