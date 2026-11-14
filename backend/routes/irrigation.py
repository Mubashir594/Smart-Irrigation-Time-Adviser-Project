from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, IrrigationHistory
from schemas import (
    IrrigationCalculateRequest,
    IrrigationCalculationResult,
    IrrigationHistoryOut,
    MessageResponse
)
from auth import get_current_user
from calculations import perform_irrigation_calculation

router = APIRouter(prefix="/api/irrigation", tags=["Irrigation Calculation & History"])

@router.post("/calculate", response_model=IrrigationCalculationResult, status_code=status.HTTP_201_CREATED)
def calculate_and_save_irrigation(
    payload: IrrigationCalculateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute the Python-based irrigation calculation engine and persist the
    resulting advisory telemetry in the SQLite database.
    """
    try:
        # Run authoritative Python calculation pipeline
        result = perform_irrigation_calculation(
            crop_type=payload.crop_type,
            soil_type=payload.soil_type,
            weather_condition=payload.weather_condition,
            hours_since_irrigation=payload.hours_since_irrigation
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    # Persist calculation record in SQLite
    db_record = IrrigationHistory(
        user_id=current_user.id,
        crop_type=result["crop_type"],
        soil_type=result["soil_type"],
        weather_condition=result["weather_condition"],
        hours_since_irrigation=result["hours_since_irrigation"],
        eto_estimate=result["eto_estimate"],
        crop_coefficient=result["crop_coefficient"],
        etc_loss_rate=result["etc_loss_rate"],
        estimated_moisture=result["estimated_moisture"],
        estimated_time_to_critical_deficit=result["estimated_time_to_critical_deficit"],
        irrigation_status=result["irrigation_status"],
        recommendation=result["recommendation"]
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return IrrigationCalculationResult(**result)

@router.get("/history", response_model=List[IrrigationHistoryOut])
def get_irrigation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve past calculation history records for the authenticated user,
    ordered with the latest entries first.
    """
    records = db.query(IrrigationHistory)\
                .filter(IrrigationHistory.user_id == current_user.id)\
                .order_by(IrrigationHistory.created_at.desc())\
                .all()
    return [IrrigationHistoryOut.model_validate(r) for r in records]

@router.get("/history/{record_id}", response_model=IrrigationHistoryOut)
def get_single_history_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a single calculation record by ID.
    Enforces that an operator can only inspect their own records.
    """
    record = db.query(IrrigationHistory)\
               .filter(IrrigationHistory.id == record_id, IrrigationHistory.user_id == current_user.id)\
               .first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Irrigation calculation record #{record_id} not found."
        )
    return IrrigationHistoryOut.model_validate(record)

@router.delete("/history", response_model=MessageResponse)
def clear_irrigation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear all saved irrigation records for the authenticated user from SQLite.
    """
    count = db.query(IrrigationHistory)\
              .filter(IrrigationHistory.user_id == current_user.id)\
              .delete(synchronize_session=False)
    db.commit()
    return MessageResponse(message=f"Purged {count} calculation records from database.")
