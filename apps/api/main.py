from fastapi import FastAPI, Query, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import os
from contextlib import asynccontextmanager

from database import engine, Base, get_db
from sqlalchemy.orm import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown

app = FastAPI(
    title="Solar×Price Explorer API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class AreaResponse(BaseModel):
    areas: List[str]

class PricePoint(BaseModel):
    timestamp: datetime
    area: str
    price_jpy_kwh: float
    volume_kwh: Optional[float] = None

class RadiationPoint(BaseModel):
    timestamp: datetime
    station: str
    area: str
    ghi: Optional[float] = None
    dni: Optional[float] = None
    dhi: Optional[float] = None

class CorrelationResult(BaseModel):
    area: str
    period: str
    n: int
    r_ghi: Optional[float] = None
    r_dni: Optional[float] = None
    r_dhi: Optional[float] = None

class TrainRequest(BaseModel):
    area: str
    target: str = "area_price"
    features: List[str]
    val_window: str = "7d"

class TrainResponse(BaseModel):
    model_id: str
    mae: float
    trained_at: datetime

class ForecastRequest(BaseModel):
    area: str
    horizon_hours: int = Field(default=24, ge=1, le=168)
    model_id: Optional[str] = None
    future_radiation: Optional[List[dict]] = None

class ForecastPoint(BaseModel):
    timestamp: datetime
    price_pred: float
    p10: Optional[float] = None
    p90: Optional[float] = None

class ForecastResponse(BaseModel):
    area: str
    model_id: str
    points: List[ForecastPoint]

# Security
def verify_token(authorization: Optional[str] = Header(None)):
    expected_token = os.getenv("API_TOKEN")
    if expected_token and authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=403, detail="Invalid token")
    return True

# Endpoints
@app.get("/healthz")
async def healthcheck():
    return {"status": "ok", "timezone": "Asia/Tokyo"}

@app.get("/api/areas", response_model=AreaResponse)
async def get_areas():
    """Get list of available JEPX areas"""
    areas = ["HOKKAIDO", "TOHOKU", "TOKYO", "CHUBU", "HOKURIKU",
             "KANSAI", "CHUGOKU", "SHIKOKU", "KYUSHU"]
    return {"areas": areas}

@app.get("/api/prices")
async def get_prices(
    area: str = Query(...),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Get hourly price data for an area"""
    # TODO: Implement database query
    return {"area": area, "data": [], "note": "Implementation pending"}

@app.get("/api/radiation")
async def get_radiation(
    area: str = Query(...),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Get hourly radiation data for an area"""
    # TODO: Implement database query
    return {"area": area, "data": [], "note": "Implementation pending"}

@app.get("/api/corr")
async def get_correlations(
    area: str = Query(...),
    period: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Calculate correlations between radiation and prices"""
    # TODO: Implement correlation calculation
    return {
        "area": area,
        "period": period,
        "r_ghi": 0.0,
        "r_dni": 0.0,
        "r_dhi": 0.0,
        "n": 0,
        "note": "Implementation pending"
    }

@app.post("/api/train", response_model=TrainResponse)
async def train_model(
    request: TrainRequest,
    db: Session = Depends(get_db)
):
    """Train a price prediction model"""
    # TODO: Implement model training
    return TrainResponse(
        model_id=f"{request.area}_baseline",
        mae=0.0,
        trained_at=datetime.now()
    )

@app.post("/api/forecast", response_model=ForecastResponse)
async def forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    """Generate price forecast"""
    # TODO: Implement forecasting
    return ForecastResponse(
        area=request.area,
        model_id=request.model_id or f"{request.area}_baseline",
        points=[]
    )

@app.get("/api/export")
async def export_data(
    area: str = Query(...),
    kind: str = Query(..., regex="^(features|raw|forecast)$"),
    format: str = Query("csv", regex="^(csv|parquet)$"),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Export dataset"""
    # TODO: Implement export
    return {"url": None, "note": "Implementation pending"}

@app.post("/api/etl/run")
async def run_etl(
    source: str = Query(..., regex="^(jepx|jma|features)$"),
    _: bool = Depends(verify_token)
):
    """Trigger ETL process (protected endpoint)"""
    # TODO: Implement ETL trigger
    return {"source": source, "status": "triggered", "note": "Implementation pending"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
