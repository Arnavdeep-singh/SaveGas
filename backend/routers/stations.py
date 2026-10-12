from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models import Station
from schemas import StationCreate, StationResponse

router = APIRouter(prefix="/api/stations", tags=["stations"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(payload: StationCreate, db: DatabaseSession):
    station = Station(**payload.model_dump())
    try:
        db.add(station)
        db.commit()
        db.refresh(station)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return station


@router.get("", response_model=list[StationResponse])
def list_stations(db: DatabaseSession):
    try:
        return db.scalars(select(Station).order_by(Station.id)).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
