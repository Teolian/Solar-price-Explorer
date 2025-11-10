from fastapi import FastAPI, Query, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import os
import io
import pytz
from contextlib import asynccontextmanager
import pandas as pd

from database import engine, Base, get_db, Price, Radiation, Feature, Model
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from ml_model import PriceForecaster, compute_correlations

JST = pytz.timezone('Asia/Tokyo')

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
    query = db.query(Price).filter(Price.area == area.upper())

    if from_dt:
        from_timestamp = datetime.fromisoformat(from_dt.replace('Z', '+00:00'))
        query = query.filter(Price.timestamp >= from_timestamp)

    if to_dt:
        to_timestamp = datetime.fromisoformat(to_dt.replace('Z', '+00:00'))
        query = query.filter(Price.timestamp <= to_timestamp)

    prices = query.order_by(Price.timestamp).limit(10000).all()

    data = [
        {
            "timestamp": p.timestamp.isoformat(),
            "area": p.area,
            "price_jpy_kwh": p.area_price_jpy_kwh,
            "volume_kwh": p.volume_total_kwh
        }
        for p in prices
    ]

    return {"area": area, "data": data, "count": len(data)}

@app.get("/api/radiation")
async def get_radiation(
    area: str = Query(...),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Get hourly radiation data for an area"""
    query = db.query(Radiation).filter(Radiation.area == area.upper())

    if from_dt:
        from_timestamp = datetime.fromisoformat(from_dt.replace('Z', '+00:00'))
        query = query.filter(Radiation.timestamp >= from_timestamp)

    if to_dt:
        to_timestamp = datetime.fromisoformat(to_dt.replace('Z', '+00:00'))
        query = query.filter(Radiation.timestamp <= to_timestamp)

    radiation = query.order_by(Radiation.timestamp).limit(10000).all()

    data = [
        {
            "timestamp": r.timestamp.isoformat(),
            "station": r.station,
            "area": r.area,
            "ghi": r.ghi,
            "dni": r.dni,
            "dhi": r.dhi
        }
        for r in radiation
    ]

    return {"area": area, "data": data, "count": len(data)}

@app.get("/api/corr")
async def get_correlations(
    area: str = Query(...),
    period: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Calculate correlations between radiation and prices"""
    # Parse period (e.g., "30d" -> 30 days)
    if period.endswith('d'):
        days = int(period[:-1])
    else:
        days = 30

    end_date = datetime.now(JST)
    start_date = end_date - timedelta(days=days)

    # Fetch features for the period
    features = db.query(Feature).filter(
        and_(
            Feature.area == area.upper(),
            Feature.timestamp >= start_date,
            Feature.timestamp <= end_date
        )
    ).all()

    if not features:
        raise HTTPException(
            status_code=404,
            detail=f"No data available for {area} in period {period}"
        )

    # Convert to dataframe
    df = pd.DataFrame([
        {
            'timestamp': f.timestamp,
            'target_price': f.target_price,
            'ghi': f.ghi,
            'dni': f.dni,
            'dhi': f.dhi,
            'hour': f.hour
        }
        for f in features
    ])

    # Compute correlations
    corr_results = compute_correlations(df)
    corr_results['area'] = area
    corr_results['period'] = period

    return corr_results

@app.post("/api/train", response_model=TrainResponse)
async def train_model(
    request: TrainRequest,
    db: Session = Depends(get_db)
):
    """Train a price prediction model"""
    # Parse validation window
    if request.val_window.endswith('d'):
        val_days = int(request.val_window[:-1])
    else:
        val_days = 7

    # Fetch training data (last 90 days)
    end_date = datetime.now(JST)
    start_date = end_date - timedelta(days=90)

    features = db.query(Feature).filter(
        and_(
            Feature.area == request.area.upper(),
            Feature.timestamp >= start_date,
            Feature.timestamp <= end_date
        )
    ).order_by(Feature.timestamp).all()

    if len(features) < 168:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient training data: {len(features)} samples (need at least 168)"
        )

    # Convert to dataframe
    df = pd.DataFrame([
        {
            'timestamp': f.timestamp,
            'target_price': f.target_price,
            'ghi': f.ghi,
            'dni': f.dni,
            'dhi': f.dhi,
            'volume_kwh': f.volume_kwh,
            'price_lag_1h': f.price_lag_1h,
            'price_lag_24h': f.price_lag_24h,
            'ghi_lag_1h': f.ghi_lag_1h,
            'ghi_roll3h': f.ghi_roll3h,
            'hour': f.hour,
            'dow': f.dow,
            'month': f.month,
            'is_weekend': f.is_weekend
        }
        for f in features
    ])

    # Train model
    forecaster = PriceForecaster()
    val_ratio = val_days / 90
    metrics = forecaster.train(df, request.features, val_ratio)

    # Save model
    trained_at = datetime.now(JST)
    model_id = f"{request.area.upper()}_{trained_at.strftime('%Y%m%d_%H%M%S')}"
    model_path = forecaster.save(model_id)

    # Store model metadata
    model_record = Model(
        model_id=model_id,
        area=request.area.upper(),
        target=request.target,
        features=','.join(request.features),
        mae=metrics['val_mae'],
        trained_at=trained_at,
        model_path=model_path
    )
    db.add(model_record)
    db.commit()

    return TrainResponse(
        model_id=model_id,
        mae=metrics['val_mae'],
        trained_at=trained_at
    )

@app.post("/api/forecast", response_model=ForecastResponse)
async def forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    """Generate price forecast"""
    # Get model
    if request.model_id:
        model = db.query(Model).filter(Model.model_id == request.model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")
    else:
        # Get latest model for area
        model = db.query(Model).filter(
            Model.area == request.area.upper()
        ).order_by(Model.trained_at.desc()).first()

        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"No trained model found for {request.area}"
            )

    # Load model
    forecaster = PriceForecaster()
    forecaster.load(model.model_id)

    # Get latest features
    latest_features = db.query(Feature).filter(
        Feature.area == request.area.upper()
    ).order_by(Feature.timestamp.desc()).limit(24).all()

    if not latest_features:
        raise HTTPException(
            status_code=404,
            detail=f"No recent features available for {request.area}"
        )

    # Convert to dataframe
    df = pd.DataFrame([
        {
            'timestamp': f.timestamp,
            'target_price': f.target_price,
            'ghi': f.ghi,
            'dni': f.dni,
            'dhi': f.dhi,
            'volume_kwh': f.volume_kwh,
            'price_lag_1h': f.price_lag_1h,
            'price_lag_24h': f.price_lag_24h,
            'ghi_lag_1h': f.ghi_lag_1h,
            'ghi_roll3h': f.ghi_roll3h,
            'hour': f.hour,
            'dow': f.dow,
            'month': f.month,
            'is_weekend': f.is_weekend
        }
        for f in reversed(latest_features)
    ])

    # Generate forecast
    forecast_df = forecaster.forecast(
        df,
        request.horizon_hours,
        request.future_radiation
    )

    points = [
        ForecastPoint(
            timestamp=row['timestamp'],
            price_pred=row['price_pred']
        )
        for _, row in forecast_df.iterrows()
    ]

    return ForecastResponse(
        area=request.area,
        model_id=model.model_id,
        points=points
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
    # Determine which table to query
    if kind == "features":
        query = db.query(Feature).filter(Feature.area == area.upper())
    elif kind == "raw":
        # Export joined prices and radiation
        query = db.query(Price).filter(Price.area == area.upper())
    else:
        raise HTTPException(status_code=400, detail="Forecast export not yet implemented")

    # Apply date filters
    if from_dt:
        from_timestamp = datetime.fromisoformat(from_dt.replace('Z', '+00:00'))
        query = query.filter(Price.timestamp >= from_timestamp)

    if to_dt:
        to_timestamp = datetime.fromisoformat(to_dt.replace('Z', '+00:00'))
        query = query.filter(Price.timestamp <= to_timestamp)

    # Execute query
    results = query.order_by(Price.timestamp if kind == "raw" else Feature.timestamp).limit(50000).all()

    if not results:
        raise HTTPException(status_code=404, detail="No data found for export")

    # Convert to dataframe
    if kind == "features":
        df = pd.DataFrame([
            {
                'timestamp': f.timestamp,
                'area': f.area,
                'target_price': f.target_price,
                'ghi': f.ghi,
                'dni': f.dni,
                'dhi': f.dhi,
                'volume_kwh': f.volume_kwh,
                'price_lag_1h': f.price_lag_1h,
                'price_lag_24h': f.price_lag_24h,
                'ghi_lag_1h': f.ghi_lag_1h,
                'ghi_roll3h': f.ghi_roll3h,
                'hour': f.hour,
                'dow': f.dow,
                'month': f.month,
                'is_weekend': f.is_weekend
            }
            for f in results
        ])
    else:
        df = pd.DataFrame([
            {
                'timestamp': p.timestamp,
                'area': p.area,
                'price_jpy_kwh': p.area_price_jpy_kwh,
                'volume_kwh': p.volume_total_kwh
            }
            for p in results
        ])

    # Export to requested format
    output = io.BytesIO()

    if format == "csv":
        df.to_csv(output, index=False)
        media_type = "text/csv"
        filename = f"{area}_{kind}_{datetime.now(JST).strftime('%Y%m%d')}.csv"
    else:
        df.to_parquet(output, index=False)
        media_type = "application/octet-stream"
        filename = f"{area}_{kind}_{datetime.now(JST).strftime('%Y%m%d')}.parquet"

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

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
