from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserSettings
from schemas import SettingsUpdate, SettingsOut
from auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["User Node Settings"])

@router.get("/settings", response_model=SettingsOut)
def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve hardware node configuration settings for the current user.
    Creates default settings if not already present.
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            sensor_frequency="Standard (15m)",
            autonomous_mode=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return SettingsOut.model_validate(settings)

@router.put("/settings", response_model=SettingsOut)
def update_user_settings(
    update_data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save hardware node configuration settings (sensor frequency, autonomous mode) to SQLite.
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            sensor_frequency=update_data.sensor_frequency,
            autonomous_mode=update_data.autonomous_mode
        )
        db.add(settings)
    else:
        settings.sensor_frequency = update_data.sensor_frequency
        settings.autonomous_mode = update_data.autonomous_mode
        settings.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(settings)
    return SettingsOut.model_validate(settings)

