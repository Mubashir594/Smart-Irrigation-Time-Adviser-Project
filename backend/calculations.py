"""
AURA Irrigation Calculation Engine
Scientifically reviewed agronomic formulas based on FAO-56 Penman-Monteith principles.
"""

from typing import Dict, Any

# --- Authoritative Agronomic Dictionaries ---

# FAO-56 representative Reference Evapotranspiration (ETo) estimates in mm/day
# Based on prevailing regional meteorological conditions
ETO_ESTIMATES: Dict[str, float] = {
    "hot": 9.2,       # Extreme Arid / High Heat
    "warm": 6.8,      # Sunny / Warm Dry
    "normal": 4.8,    # Mild / Clear Standard
    "cool": 2.8,      # Cool / Overcast
    "rainy": 1.2,     # Rainy / Low Solar Irradiance
    "humid": 3.5,     # Tropical / Humid
}

# FAO-56 single crop coefficients (Kc) for mid-season growth stage
CROP_COEFFICIENTS: Dict[str, float] = {
    # Cereals
    "Rice": 1.20,
    "Maize": 1.15,
    "Wheat": 1.10,
    "Barley": 1.00,
    # Vegetables
    "Tomato": 1.15,
    "Potato": 1.10,
    "Onion": 1.05,
    "Carrot": 1.00,
    # Fruits & Specialty
    "Grapes": 0.85,
    "Citrus": 0.75,
    "Coffee": 0.95,
    "Banana": 1.20,
}

# Available Water Capacity (AWC) in mm for active topsoil root-zone depth
# Represents the estimated water volume available to plants between field capacity and permanent wilting point.
# Note: These values serve as approximate application parameters rather than experimentally measured soil properties.
SOIL_WATER_CAPACITY_MM: Dict[str, float] = {
    "clay": 39.0,        # Heavy Clay (High retention, slow infiltration)
    "silty-clay": 33.0,  # Silty Clay
    "loamy": 26.0,       # Silt Loam / Loamy (Balanced medium retention)
    "sandy-loam": 19.0,  # Sandy Loam
    "sandy": 13.0,       # Coarse Sand (Low retention, rapid drainage)
    "peat": 52.0,        # Peat / High Organic Matter
}

def get_reference_eto(weather: str) -> float:
    """Retrieve the estimated reference evapotranspiration (ETo) in mm/day."""
    clean_weather = weather.lower().strip()
    if clean_weather not in ETO_ESTIMATES:
        raise ValueError(f"Unsupported weather condition '{weather}'. Supported: {list(ETO_ESTIMATES.keys())}")
    return ETO_ESTIMATES[clean_weather]

def get_crop_coefficient(crop: str) -> float:
    """Retrieve the mid-season crop coefficient (Kc) for the selected species."""
    # Match by key (case-insensitive fallback)
    for c_name, kc in CROP_COEFFICIENTS.items():
        if c_name.lower() == crop.lower().strip():
            return kc
    raise ValueError(f"Unsupported crop species '{crop}'. Supported: {list(CROP_COEFFICIENTS.keys())}")

def get_soil_capacity_mm(soil: str) -> float:
    """Retrieve estimated Available Water Capacity (AWC) in mm."""
    clean_soil = soil.lower().strip()
    if clean_soil not in SOIL_WATER_CAPACITY_MM:
        raise ValueError(f"Unsupported soil type '{soil}'. Supported: {list(SOIL_WATER_CAPACITY_MM.keys())}")
    return SOIL_WATER_CAPACITY_MM[clean_soil]

def calculate_etc(eto: float, kc: float) -> float:
    """
    Calculate Crop Evapotranspiration (ETc) in mm/day:
    ETc = ETo * Kc
    """
    return round(eto * kc, 2)

def estimate_soil_moisture(hours: int, etc_daily: float, capacity_mm: float, weather: str) -> float:
    """
    Estimate remaining soil moisture percentage based on elapsed time, daily ETc,
    soil available water capacity, and meteorological adjustments.
    
    Formula:
    Loss (mm) = hours * (ETc / 24)
    Depletion (%) = (Loss / capacity_mm) * 100
    Base Moisture (%) = 100 - Depletion
    Adjustments: +35% for rainfall precipitation, +8% for high humidity
    Bounds: Strictly clamped between 5.0% (residual wilting floor) and 100.0% (field capacity).
    """
    if hours < 0:
        raise ValueError("Elapsed hours since last irrigation cannot be negative.")

    loss_mm = hours * (etc_daily / 24.0)
    base_moisture = 100.0 - ((loss_mm / capacity_mm) * 100.0)

    clean_weather = weather.lower().strip()
    if clean_weather == "rainy":
        base_moisture += 35.0
    elif clean_weather == "humid":
        base_moisture += 8.0

    # Clamp strictly between 5.0% and 100.0%
    clamped_moisture = max(5.0, min(100.0, base_moisture))
    return round(clamped_moisture, 1)

def calculate_time_to_critical_deficit(moisture_pct: float, capacity_mm: float, etc_daily: float) -> float:
    """
    Estimate time in hours before soil moisture drops below critical depletion threshold.
    
    Managed Allowed Depletion (MAD) threshold is defined at 35% of available water capacity.
    Critical Water (mm) = 0.35 * capacity_mm
    Current Water (mm) = (moisture_pct / 100) * capacity_mm
    Loss per hour (mm/h) = ETc / 24
    
    If moisture is already <= critical threshold, time remaining is 0.0 hours.
    """
    loss_per_hour = etc_daily / 24.0
    if loss_per_hour <= 0.0001:
        # Near zero evaporation; virtually indefinite moisture retention
        return 999.0

    current_water_mm = (moisture_pct / 100.0) * capacity_mm
    critical_water_mm = 0.35 * capacity_mm

    if current_water_mm <= critical_water_mm:
        return 0.0

    hours_remaining = (current_water_mm - critical_water_mm) / loss_per_hour
    return round(max(0.0, hours_remaining), 1)

def classify_irrigation_status(moisture_pct: float, hours_remaining: float, crop: str) -> Dict[str, str]:
    """
    Classify the advisory status into one of three defined agronomic states:
    1. Critical Water Deficit (< 45% moisture)
    2. Over-Saturation (> 85% moisture)
    3. Optimal Equilibrium (45% - 85% moisture)
    """
    if moisture_pct < 45.0:
        return {
            "status": "CRITICAL ALERT",
            "title": "Urgent: Water Deficit",
            "description": f"AURA detects {crop} approaching permanent wilting threshold. Time to critical deficit is {hours_remaining}h. Soil matric potential is declining.",
            "recommendation": "ACTIVATE VALVES NOW (20min)",
            "alert_level": "critical",
            "health_index": "RISK"
        }
    elif moisture_pct > 85.0:
        return {
            "status": "OVER-SATURATED",
            "title": "Saturation Warning",
            "description": f"Field capacity exceeded. AURA predicts root hypoxia if moisture remains elevated for extended intervals.",
            "recommendation": "ENABLE DRAINAGE / SUSPEND IRRIGATION",
            "alert_level": "warning",
            "health_index": "WET"
        }
    else:
        return {
            "status": "SYSTEM OPTIMAL",
            "title": "Optimal Equilibrium",
            "description": f"Stomatal conductance is normal. Next scheduled irrigation cycle is anticipated in approximately {hours_remaining} hours.",
            "recommendation": "MAINTAIN STATUS QUO",
            "alert_level": "success",
            "health_index": "PRIME"
        }

def perform_irrigation_calculation(
    crop_type: str,
    soil_type: str,
    weather_condition: str,
    hours_since_irrigation: int
) -> Dict[str, Any]:
    """
    Master computation pipeline executed on the FastAPI backend:
    1. Input validation & parameter lookup
    2. Reference ETo estimation
    3. Crop ETc calculation
    4. Moisture percentage determination
    5. Critical deficit depletion timeline prediction
    6. Agronomic status and advisory classification
    """
    eto = get_reference_eto(weather_condition)
    kc = get_crop_coefficient(crop_type)
    capacity_mm = get_soil_capacity_mm(soil_type)

    etc = calculate_etc(eto, kc)
    moisture = estimate_soil_moisture(hours_since_irrigation, etc, capacity_mm, weather_condition)
    hours_remaining = calculate_time_to_critical_deficit(moisture, capacity_mm, etc)
    status_info = classify_irrigation_status(moisture, hours_remaining, crop_type)

    return {
        "crop_type": crop_type,
        "soil_type": soil_type,
        "weather_condition": weather_condition,
        "hours_since_irrigation": hours_since_irrigation,
        "eto_estimate": eto,
        "crop_coefficient": kc,
        "soil_capacity_mm": capacity_mm,
        "etc_loss_rate": etc,
        "estimated_moisture": moisture,
        "estimated_time_to_critical_deficit": hours_remaining,
        "irrigation_status": status_info["status"],
        "recommendation": status_info["recommendation"],
        "title": status_info["title"],
        "description": status_info["description"],
        "alert_level": status_info["alert_level"],
        "health_index": status_info["health_index"]
    }

