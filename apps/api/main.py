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

class HourlyPattern(BaseModel):
    hour: int
    avg_price: float
    avg_ghi: float
    avg_dni: Optional[float] = None
    avg_dhi: Optional[float] = None
    count: int

class HourlyPatternsResponse(BaseModel):
    area: str
    date_range: dict
    patterns: List[HourlyPattern]

class AreaStats(BaseModel):
    area: str
    avg_price: float
    min_price: float
    max_price: float
    avg_ghi: float
    correlation: Optional[float] = None
    data_points: int

class MultiAreaComparisonResponse(BaseModel):
    date_range: dict
    areas: List[AreaStats]

class StatsSummary(BaseModel):
    area: str
    date_range: dict
    price_stats: dict
    radiation_stats: dict
    correlation: Optional[float] = None
    top_expensive_hours: List[dict]
    top_cheap_hours: List[dict]
    total_records: int

class ConsumptionScenario(BaseModel):
    daily_consumption_kwh: float
    monthly_savings_jpy: float
    annual_savings_jpy: float

class SavingsAnalysis(BaseModel):
    peak_price_avg: float
    solar_price_avg: float
    price_difference: float
    savings_percentage: float
    best_hours: List[int]
    worst_hours: List[int]
    example_scenarios: dict

class SavingsPotentialResponse(BaseModel):
    area: str
    period: str
    date_range: dict
    savings_analysis: SavingsAnalysis

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

@app.get("/api/stats/hourly-patterns", response_model=HourlyPatternsResponse)
async def get_hourly_patterns(
    area: str = Query(..., description="Area code (e.g., TOKYO, HOKKAIDO)"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get hourly patterns showing average prices and solar radiation by hour of day.
    This reveals how solar generation affects prices throughout the day.
    """
    # Parse dates
    if from_date and to_date:
        start_date = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    else:
        # Default to last 30 days
        end_date = datetime.now(JST)
        start_date = end_date - timedelta(days=30)

    # Fetch prices and radiation data
    prices = db.query(
        func.extract('hour', Price.timestamp).label('hour'),
        func.avg(Price.area_price_jpy_kwh).label('avg_price'),
        func.count(Price.id).label('count')
    ).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date
        )
    ).group_by(func.extract('hour', Price.timestamp)).all()

    radiation = db.query(
        func.extract('hour', Radiation.timestamp).label('hour'),
        func.avg(Radiation.ghi).label('avg_ghi'),
        func.avg(Radiation.dni).label('avg_dni'),
        func.avg(Radiation.dhi).label('avg_dhi')
    ).filter(
        and_(
            Radiation.area == area.upper(),
            Radiation.timestamp >= start_date,
            Radiation.timestamp <= end_date
        )
    ).group_by(func.extract('hour', Radiation.timestamp)).all()

    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No price data available for {area}"
        )

    # Merge prices and radiation by hour
    radiation_by_hour = {int(r.hour): r for r in radiation}

    patterns = []
    for p in prices:
        hour = int(p.hour)
        rad = radiation_by_hour.get(hour)

        patterns.append(HourlyPattern(
            hour=hour,
            avg_price=round(p.avg_price, 2),
            avg_ghi=round(rad.avg_ghi, 2) if rad and rad.avg_ghi else 0.0,
            avg_dni=round(rad.avg_dni, 2) if rad and rad.avg_dni else None,
            avg_dhi=round(rad.avg_dhi, 2) if rad and rad.avg_dhi else None,
            count=p.count
        ))

    # Sort by hour
    patterns.sort(key=lambda x: x.hour)

    return HourlyPatternsResponse(
        area=area.upper(),
        date_range={
            "from": start_date.isoformat(),
            "to": end_date.isoformat()
        },
        patterns=patterns
    )

@app.get("/api/stats/multi-area-comparison", response_model=MultiAreaComparisonResponse)
async def get_multi_area_comparison(
    areas: str = Query(..., description="Comma-separated list of areas (e.g., TOKYO,OSAKA,HOKKAIDO)"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Compare statistics across multiple areas.
    Returns aggregated metrics for each area including avg/min/max price, solar radiation, and correlation.
    """
    # Parse areas
    area_list = [a.strip().upper() for a in areas.split(',')]

    # Parse dates - default to last 30 days
    if from_date and to_date:
        start_date = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    else:
        end_date = datetime.now(JST)
        start_date = end_date - timedelta(days=30)

    area_stats_list = []

    for area in area_list:
        # Fetch price statistics
        price_stats = db.query(
            func.avg(Price.area_price_jpy_kwh).label('avg_price'),
            func.min(Price.area_price_jpy_kwh).label('min_price'),
            func.max(Price.area_price_jpy_kwh).label('max_price'),
            func.count(Price.id).label('count')
        ).filter(
            and_(
                Price.area == area,
                Price.timestamp >= start_date,
                Price.timestamp <= end_date
            )
        ).first()

        # Fetch radiation statistics
        rad_stats = db.query(
            func.avg(Radiation.ghi).label('avg_ghi')
        ).filter(
            and_(
                Radiation.area == area,
                Radiation.timestamp >= start_date,
                Radiation.timestamp <= end_date
            )
        ).first()

        # Calculate correlation for this area
        # Fetch daytime (6-18) prices and radiation
        prices_for_corr = db.query(Price).filter(
            and_(
                Price.area == area,
                Price.timestamp >= start_date,
                Price.timestamp <= end_date,
                func.extract('hour', Price.timestamp) >= 6,
                func.extract('hour', Price.timestamp) <= 18
            )
        ).all()

        radiation_for_corr = db.query(Radiation).filter(
            and_(
                Radiation.area == area,
                Radiation.timestamp >= start_date,
                Radiation.timestamp <= end_date,
                func.extract('hour', Radiation.timestamp) >= 6,
                func.extract('hour', Radiation.timestamp) <= 18
            )
        ).all()

        correlation = None
        if prices_for_corr and radiation_for_corr:
            try:
                corr_result = compute_correlations(prices_for_corr, radiation_for_corr)
                correlation = corr_result.get('r_ghi')
            except:
                correlation = None

        if price_stats and price_stats.count > 0:
            area_stats_list.append(AreaStats(
                area=area,
                avg_price=round(price_stats.avg_price, 2) if price_stats.avg_price else 0.0,
                min_price=round(price_stats.min_price, 2) if price_stats.min_price else 0.0,
                max_price=round(price_stats.max_price, 2) if price_stats.max_price else 0.0,
                avg_ghi=round(rad_stats.avg_ghi, 2) if rad_stats and rad_stats.avg_ghi else 0.0,
                correlation=round(correlation, 3) if correlation is not None else None,
                data_points=price_stats.count
            ))

    if not area_stats_list:
        raise HTTPException(
            status_code=404,
            detail="No data available for the specified areas"
        )

    return MultiAreaComparisonResponse(
        date_range={
            "from": start_date.isoformat(),
            "to": end_date.isoformat()
        },
        areas=area_stats_list
    )

@app.get("/api/stats/summary", response_model=StatsSummary)
async def get_stats_summary(
    area: str = Query(..., description="Area code (e.g., TOKYO, HOKKAIDO)"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistical summary for an area including:
    - Price statistics (avg, min, max, std dev)
    - Solar radiation statistics
    - Correlation metrics
    - Top 10 most expensive and cheapest hours
    - Total record counts
    """
    # Parse dates - default to last 30 days
    if from_date and to_date:
        start_date = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    else:
        end_date = datetime.now(JST)
        start_date = end_date - timedelta(days=30)

    # Fetch price statistics
    from sqlalchemy import func as sql_func

    price_stats_query = db.query(
        sql_func.avg(Price.area_price_jpy_kwh).label('avg_price'),
        sql_func.min(Price.area_price_jpy_kwh).label('min_price'),
        sql_func.max(Price.area_price_jpy_kwh).label('max_price'),
        sql_func.stddev(Price.area_price_jpy_kwh).label('std_price'),
        sql_func.count(Price.id).label('count')
    ).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date
        )
    ).first()

    if not price_stats_query or not price_stats_query.count:
        raise HTTPException(
            status_code=404,
            detail=f"No price data available for {area} in the specified date range"
        )

    # Fetch radiation statistics
    rad_stats_query = db.query(
        sql_func.avg(Radiation.ghi).label('avg_ghi'),
        sql_func.min(Radiation.ghi).label('min_ghi'),
        sql_func.max(Radiation.ghi).label('max_ghi'),
        sql_func.avg(Radiation.dni).label('avg_dni'),
        sql_func.avg(Radiation.dhi).label('avg_dhi'),
        sql_func.count(Radiation.id).label('count')
    ).filter(
        and_(
            Radiation.area == area.upper(),
            Radiation.timestamp >= start_date,
            Radiation.timestamp <= end_date
        )
    ).first()

    # Calculate correlation (daytime hours only)
    prices_for_corr = db.query(Price).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date,
            sql_func.extract('hour', Price.timestamp) >= 6,
            sql_func.extract('hour', Price.timestamp) <= 18
        )
    ).all()

    radiation_for_corr = db.query(Radiation).filter(
        and_(
            Radiation.area == area.upper(),
            Radiation.timestamp >= start_date,
            Radiation.timestamp <= end_date,
            sql_func.extract('hour', Radiation.timestamp) >= 6,
            sql_func.extract('hour', Radiation.timestamp) <= 18
        )
    ).all()

    correlation = None
    if prices_for_corr and radiation_for_corr:
        try:
            corr_result = compute_correlations(prices_for_corr, radiation_for_corr)
            correlation = corr_result.get('r_ghi')
        except:
            correlation = None

    # Get top 10 most expensive hours
    top_expensive = db.query(
        Price.timestamp,
        Price.area_price_jpy_kwh
    ).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date
        )
    ).order_by(Price.area_price_jpy_kwh.desc()).limit(10).all()

    # Get top 10 cheapest hours
    top_cheap = db.query(
        Price.timestamp,
        Price.area_price_jpy_kwh
    ).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date
        )
    ).order_by(Price.area_price_jpy_kwh.asc()).limit(10).all()

    return StatsSummary(
        area=area.upper(),
        date_range={
            "from": start_date.isoformat(),
            "to": end_date.isoformat()
        },
        price_stats={
            "avg": round(price_stats_query.avg_price, 2) if price_stats_query.avg_price else 0.0,
            "min": round(price_stats_query.min_price, 2) if price_stats_query.min_price else 0.0,
            "max": round(price_stats_query.max_price, 2) if price_stats_query.max_price else 0.0,
            "std": round(price_stats_query.std_price, 2) if price_stats_query.std_price else 0.0,
        },
        radiation_stats={
            "avg_ghi": round(rad_stats_query.avg_ghi, 2) if rad_stats_query and rad_stats_query.avg_ghi else 0.0,
            "min_ghi": round(rad_stats_query.min_ghi, 2) if rad_stats_query and rad_stats_query.min_ghi else 0.0,
            "max_ghi": round(rad_stats_query.max_ghi, 2) if rad_stats_query and rad_stats_query.max_ghi else 0.0,
            "avg_dni": round(rad_stats_query.avg_dni, 2) if rad_stats_query and rad_stats_query.avg_dni else 0.0,
            "avg_dhi": round(rad_stats_query.avg_dhi, 2) if rad_stats_query and rad_stats_query.avg_dhi else 0.0,
        },
        correlation=round(correlation, 3) if correlation is not None else None,
        top_expensive_hours=[
            {
                "timestamp": t.timestamp.isoformat(),
                "price": round(t.area_price_jpy_kwh, 2)
            }
            for t in top_expensive
        ],
        top_cheap_hours=[
            {
                "timestamp": t.timestamp.isoformat(),
                "price": round(t.area_price_jpy_kwh, 2)
            }
            for t in top_cheap
        ],
        total_records=price_stats_query.count
    )

@app.get("/api/stats/savings-potential", response_model=SavingsPotentialResponse)
async def get_savings_potential(
    area: str = Query(..., description="Area code (e.g., TOKYO)"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Calculate potential savings by shifting energy consumption from peak to solar hours.
    Returns average prices during peak vs solar hours, savings percentage, and example scenarios.
    """
    # Parse dates - default to last 30 days
    if from_date and to_date:
        start_date = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    else:
        end_date = datetime.now(JST)
        start_date = end_date - timedelta(days=30)

    # Define peak hours (morning/evening high demand) and solar hours (midday low prices)
    peak_hours = [7, 8, 9, 18, 19, 20]  # Morning and evening peaks
    solar_hours = [10, 11, 12, 13, 14]  # Midday solar generation hours

    # Calculate average price during peak hours
    peak_prices = db.query(
        func.avg(Price.area_price_jpy_kwh).label('avg_price')
    ).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date,
            func.extract('hour', Price.timestamp).in_(peak_hours)
        )
    ).first()

    # Calculate average price during solar hours
    solar_prices = db.query(
        func.avg(Price.area_price_jpy_kwh).label('avg_price')
    ).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date,
            func.extract('hour', Price.timestamp).in_(solar_hours)
        )
    ).first()

    if not peak_prices or not solar_prices or not peak_prices.avg_price or not solar_prices.avg_price:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient price data for {area}"
        )

    peak_avg = round(peak_prices.avg_price, 2)
    solar_avg = round(solar_prices.avg_price, 2)
    price_diff = round(peak_avg - solar_avg, 2)
    savings_pct = round((price_diff / peak_avg) * 100, 1) if peak_avg > 0 else 0.0

    # Calculate example scenarios for different consumption levels
    # Assuming 30% of consumption can be shifted to solar hours
    shift_percentage = 0.30
    days_per_month = 30

    scenarios = {
        "small_business": {
            "daily_consumption_kwh": 100,
            "monthly_savings_jpy": round(100 * shift_percentage * price_diff * days_per_month, 0),
            "annual_savings_jpy": round(100 * shift_percentage * price_diff * 365, 0)
        },
        "medium_factory": {
            "daily_consumption_kwh": 1000,
            "monthly_savings_jpy": round(1000 * shift_percentage * price_diff * days_per_month, 0),
            "annual_savings_jpy": round(1000 * shift_percentage * price_diff * 365, 0)
        },
        "large_factory": {
            "daily_consumption_kwh": 5000,
            "monthly_savings_jpy": round(5000 * shift_percentage * price_diff * days_per_month, 0),
            "annual_savings_jpy": round(5000 * shift_percentage * price_diff * 365, 0)
        }
    }

    # Find the best and worst hours by average price
    hourly_avgs = db.query(
        func.extract('hour', Price.timestamp).label('hour'),
        func.avg(Price.area_price_jpy_kwh).label('avg_price')
    ).filter(
        and_(
            Price.area == area.upper(),
            Price.timestamp >= start_date,
            Price.timestamp <= end_date
        )
    ).group_by(func.extract('hour', Price.timestamp)).all()

    sorted_hours = sorted(hourly_avgs, key=lambda x: x.avg_price)
    best_hours = [int(h.hour) for h in sorted_hours[:5]]  # Top 5 cheapest
    worst_hours = [int(h.hour) for h in sorted_hours[-5:]]  # Top 5 most expensive

    return SavingsPotentialResponse(
        area=area.upper(),
        period="30d",
        date_range={
            "from": start_date.isoformat(),
            "to": end_date.isoformat()
        },
        savings_analysis=SavingsAnalysis(
            peak_price_avg=peak_avg,
            solar_price_avg=solar_avg,
            price_difference=price_diff,
            savings_percentage=savings_pct,
            best_hours=sorted(best_hours),
            worst_hours=sorted(worst_hours),
            example_scenarios=scenarios
        )
    )

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
