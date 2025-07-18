from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Time, JSON, Numeric
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import URL
from datetime import datetime
from decimal import Decimal

# Define database connection parameters
DATABASE = {
    'drivername': 'mysql+pymysql',  # Or 'mysql', 'sqlite', etc.
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
    rqg_film_id = Column(Integer, nullable=True)  # Rapquocgia film ID
    title = Column(String(100), nullable=True)
    age_limit = Column(String(100), nullable=True)
    movie_type = Column(String(100), nullable=True)
    format = Column(String(100), nullable=True)
    genre = Column(String(100), nullable=True)
    image_url = Column(Text)
    booking_url = Column(Text)
    price = Column(String(30))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class Screentime(Base):
    __tablename__ = "screentimes"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    format = Column(String(100))
    time = Column(Time)
    date = Column(DateTime)
    language = Column(String(100))
    firstclass = Column(String(10))
    cinema_id = Column(String(30), nullable=True)
    film_id = Column(String(50), nullable=True)  # Link to specific film
    created_at = Column(DateTime, default=datetime.now)


class Theater(Base):
    __tablename__ = "cinemas"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    location = Column(String(500))
    theater_id = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class SeatData(Base):
    __tablename__ = "seat_data"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), nullable=False)
    cinema_id = Column(String(30), nullable=False)
    cinema_name = Column(String(200))
    movie_title = Column(String(200))
    movie_format = Column(String(20))
    movie_language = Column(String(50))
    movie_label = Column(String(10))  # T16, P, etc.
    showtime = Column(DateTime)
    screen_name = Column(String(50))
    screen_number = Column(Integer)
    seats_available = Column(Integer)
    expire_time = Column(DateTime)
    
    # Store complex data as JSON
    tickets_data = Column(JSON)  # Ticket types and pricing
    seats_layout = Column(JSON)  # Complete seating layout
    concession_items = Column(JSON)  # Food and beverage options
    
    # Pricing summary (extracted from tickets_data for easy querying)
    standard_price = Column(Numeric(10, 2))
    vip_price = Column(Numeric(10, 2))
    couple_price = Column(Numeric(10, 2))
    
    search_date = Column(String(20))  # The date this data was searched for
    created_at = Column(DateTime, default=datetime.now)
