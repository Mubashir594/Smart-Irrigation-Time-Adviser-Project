from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# --- User & Authentication Schemas ---

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full Name")
    username: str = Field(..., min_length=3, max_length=50, description="Unique Username")
    password: str = Field(..., min_length=4, max_length=100, description="Password")
    confirm_password: str = Field(..., min_length=4, max_length=100, description="Confirm Password")

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Terminal Auth ID")
    password: str = Field(..., min_length=4, max_length=100, description="Security Token")

class UserOut(BaseModel):
    id: int
    full_name: Optional[str] = ""
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# --- Irrigation Calculation & History Schemas ---

class IrrigationCalculateRequest(BaseModel):
    crop_type: str = Field(..., description="Selected crop species (e.g. Rice, Tomato)")
    soil_type: str = Field(..., description="Selected soil texture classification (e.g. loamy, clay)")
    weather_condition: str = Field(..., description="Environmental weather preset (e.g. normal, hot)")
    hours_since_irrigation: int = Field(..., ge=0, le=168, description="Elapsed hours since last watering event (0-168)")

class IrrigationCalculationResult(BaseModel):
    crop_type: str
    soil_type: str
    weather_condition: str
    hours_since_irrigation: int
    eto_estimate: float = Field(..., description="Reference evapotranspiration (mm/day)")
    crop_coefficient: float = Field(..., description="Mid-season crop factor (Kc)")
    soil_capacity_mm: float = Field(..., description="Available Water Capacity (AWC) in active root-zone (mm)")
    etc_loss_rate: float = Field(..., description="Crop evapotranspiration rate (mm/day)")
    estimated_moisture: float = Field(..., description="Estimated soil moisture percentage (5.0 - 100.0%)")
    estimated_time_to_critical_deficit: float = Field(..., description="Predicted hours remaining before critical depletion")
    irrigation_status: str = Field(..., description="Status summary (SYSTEM OPTIMAL, CRITICAL ALERT, OVER-SATURATED)")
    recommendation: str = Field(..., description="Advisory action recommendation")
    title: str = Field(..., description="Advisory classification title")
    description: str = Field(..., description="Agronomic explanation")
    alert_level: str = Field(..., description="Alert severity level: success, warning, critical")
    health_index: str = Field(..., description="Canopy health status: PRIME, RISK, WET")

class IrrigationHistoryOut(BaseModel):
    id: int
    user_id: int
    crop_type: str
    soil_type: str
    weather_condition: str
    hours_since_irrigation: int
    eto_estimate: float
    crop_coefficient: float
    etc_loss_rate: float
    estimated_moisture: float
    estimated_time_to_critical_deficit: float
    irrigation_status: str
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- User Settings Schemas ---

class SettingsUpdate(BaseModel):
    sensor_frequency: str = Field(..., description="Simulated sensor polling frequency")
    autonomous_mode: bool = Field(..., description="Autonomous mode simulation flag")

class SettingsOut(BaseModel):
    id: int
    user_id: int
    sensor_frequency: str
    autonomous_mode: bool
    updated_at: datetime

    class Config:
        from_attributes = True

# --- General Response Schemas ---

class MessageResponse(BaseModel):
    message: str
