"""Constants for data validation and air quality standards.

All valid ranges and limit values used by the system are defined here,
so they can be updated without changing the processing logic.
"""

from datetime import date

# Column names used in the CSV file
DATETIME_COLUMN = "datetime"
VARIABLES = [
    "temperature_c",
    "humidity_pct",
    "rainfall_mm",
    "pm25_ugm3",
    "pm10_ugm3",
    "no2_ugm3",
]
POLLUTANTS = ["pm25_ugm3", "pm10_ugm3", "no2_ugm3"]

# Readable names and units for display
DISPLAY_NAMES = {
    "temperature_c": "Temperature (°C)",
    "humidity_pct": "Humidity (%)",
    "rainfall_mm": "Rainfall (mm)",
    "pm25_ugm3": "PM2.5 (µg/m³)",
    "pm10_ugm3": "PM10 (µg/m³)",
    "no2_ugm3": "NO2 (µg/m³)",
}

# Physically valid range (minimum, maximum) for each hourly value
VALID_RANGE = {
    "temperature_c": (0.0, 50.0),
    "humidity_pct": (0.0, 100.0),
    "rainfall_mm": (0.0, 200.0),
    "pm25_ugm3": (0.0, 1000.0),
    "pm10_ugm3": (0.0, 1000.0),
    "no2_ugm3": (0.0, 1000.0),
}

# A daily value is calculated only if at least 18 of 24 hours are valid (75 %)
MIN_VALID_HOURS = 18

# Variables that are summed per day instead of averaged
SUM_VARIABLES = ["rainfall_mm"]

# 24-hour limit values in µg/m³ (WHO, 2021; MONRE, 2023)
STANDARDS = ["WHO", "QCVN"]
LIMITS_24H = {
    "WHO": {"pm25_ugm3": 15.0, "pm10_ugm3": 45.0, "no2_ugm3": 25.0},
    "QCVN": {"pm25_ugm3": 50.0, "pm10_ugm3": 100.0, "no2_ugm3": 100.0},
}

# QCVN 05:2023/BTNMT lowers the 24-hour PM2.5 limit from 1 January 2026
QCVN_PM25_LIMIT_FROM_2026 = 45.0
QCVN_PM25_CHANGE_DATE = date(2026, 1, 1)


def get_limit(standard, pollutant, day):
    """Return the 24-hour limit that applies on a given day.

    Args:
        standard: "WHO" or "QCVN".
        pollutant: column name of the pollutant, e.g. "pm25_ugm3".
        day: datetime.date of the measurement.

    Returns:
        The limit value in µg/m³ as a float.
    """
    if (standard == "QCVN" and pollutant == "pm25_ugm3"
            and day >= QCVN_PM25_CHANGE_DATE):
        return QCVN_PM25_LIMIT_FROM_2026
    return LIMITS_24H[standard][pollutant]
