from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./solar_explorer.db")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Models
class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    area = Column(String(50), nullable=False, index=True)
    system_price_jpy_kwh = Column(Float)
    area_price_jpy_kwh = Column(Float, nullable=False)
    volume_total_kwh = Column(Float)
    volume_sell_kwh = Column(Float)
    volume_buy_kwh = Column(Float)

    __table_args__ = (
        Index('ix_prices_area_timestamp', 'area', 'timestamp'),
    )

class Radiation(Base):
    __tablename__ = "radiation"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    station = Column(String(50), nullable=False, index=True)
    area = Column(String(50), nullable=False, index=True)
    ghi = Column(Float)
    dni = Column(Float)
    dhi = Column(Float)
    quality_flag = Column(String(10))

    __table_args__ = (
        Index('ix_radiation_area_timestamp', 'area', 'timestamp'),
        Index('ix_radiation_station_timestamp', 'station', 'timestamp'),
    )

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    area = Column(String(50), nullable=False, index=True)
    target_price = Column(Float)
    ghi = Column(Float)
    dni = Column(Float)
    dhi = Column(Float)
    volume_kwh = Column(Float)
    price_lag_1h = Column(Float)
    price_lag_24h = Column(Float)
    ghi_lag_1h = Column(Float)
    ghi_roll3h = Column(Float)
    hour = Column(Integer)
    dow = Column(Integer)
    month = Column(Integer)
    is_weekend = Column(Integer)

    __table_args__ = (
        Index('ix_features_area_timestamp', 'area', 'timestamp'),
    )

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, nullable=False, index=True)
    area = Column(String(50), nullable=False, index=True)
    target = Column(String(50), nullable=False)
    features = Column(String(500))
    mae = Column(Float)
    trained_at = Column(DateTime, nullable=False)
    model_path = Column(String(200))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
