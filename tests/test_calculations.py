import pytest
import sys
import os

# Add backend directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from calculations import (
    get_reference_eto,
    get_crop_coefficient,
    get_soil_capacity_mm,
    calculate_etc,
    estimate_soil_moisture,
    calculate_time_to_critical_deficit,
    perform_irrigation_calculation
)

def test_five_representative_combinations():
    """
    Test the 5 specific representative agronomic combinations specified in requirements:
    1. Rice + Clay + Hot
    2. Maize + Loamy + Normal
    3. Tomato + Sandy-loam + Warm
    4. Wheat + Sandy + Cool
    5. Banana + Peat + Rainy
    """
    # 1. Rice + Clay + Hot (12h)
    r1 = perform_irrigation_calculation("Rice", "clay", "hot", 12)
    assert r1["eto_estimate"] == 9.2
    assert r1["crop_coefficient"] == 1.20
    assert r1["etc_loss_rate"] == 11.04
    assert 5.0 <= r1["estimated_moisture"] <= 100.0
    assert r1["estimated_time_to_critical_deficit"] >= 0.0
    assert r1["irrigation_status"] in ["SYSTEM OPTIMAL", "CRITICAL ALERT", "OVER-SATURATED"]

    # 2. Maize + Loamy + Normal (12h)
    r2 = perform_irrigation_calculation("Maize", "loamy", "normal", 12)
    assert r2["eto_estimate"] == 4.8
    assert r2["crop_coefficient"] == 1.15
    assert r2["etc_loss_rate"] == 5.52
    assert 5.0 <= r2["estimated_moisture"] <= 100.0

    # 3. Tomato + Sandy-loam + Warm (12h)
    r3 = perform_irrigation_calculation("Tomato", "sandy-loam", "warm", 12)
    assert r3["eto_estimate"] == 6.8
    assert r3["crop_coefficient"] == 1.15
    assert r3["etc_loss_rate"] == 7.82
    assert 5.0 <= r3["estimated_moisture"] <= 100.0

    # 4. Wheat + Sandy + Cool (12h)
    r4 = perform_irrigation_calculation("Wheat", "sandy", "cool", 12)
    assert r4["eto_estimate"] == 2.8
    assert r4["crop_coefficient"] == 1.10
    assert r4["etc_loss_rate"] == 3.08
    assert 5.0 <= r4["estimated_moisture"] <= 100.0

    # 5. Banana + Peat + Rainy (12h)
    r5 = perform_irrigation_calculation("Banana", "peat", "rainy", 12)
    assert r5["eto_estimate"] == 1.2
    assert r5["crop_coefficient"] == 1.20
    assert r5["etc_loss_rate"] == 1.44
    assert 5.0 <= r5["estimated_moisture"] <= 100.0
    # Rainy adds +35% precipitation offset, so moisture should be near or at 100%
    assert r5["estimated_moisture"] >= 95.0

def test_zero_elapsed_time():
    """At 0 hours, soil is at field capacity (100% moisture)."""
    res = perform_irrigation_calculation("Tomato", "loamy", "normal", 0)
    assert res["estimated_moisture"] == 100.0
    assert res["estimated_time_to_critical_deficit"] > 0.0
    assert res["irrigation_status"] == "OVER-SATURATED" or res["irrigation_status"] == "SYSTEM OPTIMAL"

def test_maximum_elapsed_time():
    """At prolonged elapsed time (e.g. 168 hours), moisture hits 5.0% floor and time remaining is 0.0."""
    res = perform_irrigation_calculation("Tomato", "sandy", "hot", 168)
    assert res["estimated_moisture"] == 5.0
    assert res["estimated_time_to_critical_deficit"] == 0.0
    assert res["irrigation_status"] == "CRITICAL ALERT"
    assert res["alert_level"] == "critical"

def test_invalid_inputs_raise_errors():
    """Verify that unsupported parameters are caught with descriptive ValueErrors."""
    with pytest.raises(ValueError, match="Unsupported crop species"):
        perform_irrigation_calculation("Dragonfruit", "loamy", "normal", 10)

    with pytest.raises(ValueError, match="Unsupported soil type"):
        perform_irrigation_calculation("Rice", "volcanic_ash", "normal", 10)

    with pytest.raises(ValueError, match="Unsupported weather condition"):
        perform_irrigation_calculation("Rice", "loamy", "tornado", 10)

    with pytest.raises(ValueError, match="negative"):
        perform_irrigation_calculation("Rice", "loamy", "normal", -5)

def test_no_nan_or_inf():
    """Check across multiple combinations that outputs are valid numeric values."""
    crops = ["Rice", "Maize", "Wheat", "Tomato", "Barley", "Coffee", "Citrus"]
    soils = ["clay", "loamy", "sandy", "sandy-loam"]
    weathers = ["hot", "warm", "normal", "cool", "rainy", "humid"]

    for c in crops:
        for s in soils:
            for w in weathers:
                res = perform_irrigation_calculation(c, s, w, 24)
                assert not str(res["estimated_moisture"]).lower() in ["nan", "inf", "-inf"]
                assert not str(res["estimated_time_to_critical_deficit"]).lower() in ["nan", "inf", "-inf"]
                assert 5.0 <= res["estimated_moisture"] <= 100.0

if __name__ == "__main__":
    pytest.main(["-v", __file__])

