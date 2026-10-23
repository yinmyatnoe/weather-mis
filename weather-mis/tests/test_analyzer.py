"""Unit tests for the weather monitoring system (run with: pytest)."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer import ClimateAnalyzer  # noqa: E402
from data_loader import parse_value, validate_records  # noqa: E402
from standards import get_limit  # noqa: E402


def make_row(timestamp, **values):
    """Create a CSV-like row with valid default values."""
    row = {"datetime": timestamp, "temperature_c": "28", "humidity_pct": "80",
           "rainfall_mm": "0.5", "pm25_ugm3": "30", "pm10_ugm3": "35",
           "no2_ugm3": "20"}
    row.update(values)
    return row


# ----- Algorithm 3: statistics (expected values from Table 3.3) -----
def test_statistics_match_hand_worked_example():
    values = [42.0, 55.5, None, 50.0, 61.2, 38.3]
    stats = ClimateAnalyzer.calculate_statistics(values)
    assert stats["min"] == 38.3
    assert stats["max"] == 61.2
    assert stats["count"] == 5
    assert stats["average"] == pytest.approx(49.4)


def test_statistics_with_no_valid_values_returns_none():
    assert ClimateAnalyzer.calculate_statistics([None, None]) is None
    assert ClimateAnalyzer.calculate_statistics([]) is None


# ----- Algorithm 1: validation -----
def test_parse_value_detects_missing_and_text():
    assert parse_value("") == (None, "missing")
    assert parse_value("abc") == (None, "non-numeric")
    assert parse_value("12.5") == (12.5, None)


def test_validation_rejects_invalid_values_and_duplicates():
    rows = [make_row("2026-01-01 00:00", humidity_pct="135"),
            make_row("2026-01-01 01:00", rainfall_mm="-5"),
            make_row("2026-01-01 02:00", no2_ugm3="ERR"),
            make_row("2026-01-01 02:00")]
    clean, errors = validate_records(rows)
    assert len(clean) == 3
    assert clean[0]["humidity_pct"] is None
    assert clean[0]["temperature_c"] == 28.0
    reasons = [reason for *_, reason in errors]
    assert reasons.count("out of range") == 2
    assert "non-numeric" in reasons
    assert "duplicate" in reasons


# ----- Algorithm 2: daily aggregation -----
def test_day_with_fewer_than_18_valid_hours_is_insufficient():
    rows = [make_row(f"2026-01-01 {hour:02d}:00",
                     pm25_ugm3="" if hour < 7 else "30")
            for hour in range(24)]
    analyzer = ClimateAnalyzer()
    analyzer._records, _ = validate_records(rows)
    daily = analyzer.aggregate_daily()[date(2026, 1, 1)]
    assert daily["pm25_ugm3"] is None
    assert daily["pm10_ugm3"] == pytest.approx(35.0)


def test_rainfall_is_summed_not_averaged():
    rows = [make_row(f"2026-01-01 {hour:02d}:00") for hour in range(24)]
    analyzer = ClimateAnalyzer()
    analyzer._records, _ = validate_records(rows)
    daily = analyzer.aggregate_daily()[date(2026, 1, 1)]
    assert daily["rainfall_mm"] == pytest.approx(12.0)


# ----- Algorithm 4: thresholds -----
def test_qcvn_pm25_limit_changes_in_2026():
    assert get_limit("QCVN", "pm25_ugm3", date(2025, 12, 31)) == 50.0
    assert get_limit("QCVN", "pm25_ugm3", date(2026, 1, 1)) == 45.0
    assert get_limit("WHO", "pm25_ugm3", date(2026, 1, 1)) == 15.0


def test_value_equal_to_limit_is_not_an_alert():
    analyzer = ClimateAnalyzer()
    analyzer._daily_values = {
        date(2025, 12, 1): {"pm25_ugm3": 50.0, "pm10_ugm3": 10.0,
                            "no2_ugm3": 10.0},
        date(2025, 12, 2): {"pm25_ugm3": 55.5, "pm10_ugm3": 10.0,
                            "no2_ugm3": 10.0},
    }
    qcvn_alerts = [a for a in analyzer.detect_exceedances()
                   if a.standard == "QCVN"]
    assert len(qcvn_alerts) == 1
    assert qcvn_alerts[0].date == date(2025, 12, 2)
