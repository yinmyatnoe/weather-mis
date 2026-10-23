# HCMC climate and air quality dataset - October 2025 to September 2026

## Files
### Hourly (raw) - main input if your program does the aggregation
- `hcmc_hourly_2025_10_to_2026_09.csv` - 8,760 hourly records (365 days x 24 h), 6 variables, as delivered by the sources (not cleaned). Contains one GENUINE source error (see below).
- `hcmc_hourly_2025_10_to_2026_09_test_anomalies.csv` - same file plus deliberately injected errors (fault injection) for robustness testing (M4) and unit tests. 8,761 rows (one duplicated row).

### Daily (pre-aggregated) - fallback if time runs short
- `hcmc_climate_2025_10_to_2026_09.csv` - 365 daily records. Pollutants = mean of 24 hourly values; weather = NASA POWER daily product.
- `hcmc_climate_2025_10_to_2026_09_test_anomalies.csv` - daily copy with 10 injected errors.

## Columns (hourly file)
| Column | Unit | Source |
|---|---|---|
| datetime | YYYY-MM-DD HH:00, local time (UTC+7) | - |
| temperature_c | °C | NASA POWER hourly (T2M, MERRA-2) |
| humidity_pct | % | NASA POWER hourly (RH2M) |
| rainfall_mm | mm per hour | NASA POWER hourly (PRECTOTCORR) |
| pm25_ugm3 | µg/m³ | Open-Meteo Air Quality API (CAMS global) |
| pm10_ugm3 | µg/m³ | Open-Meteo Air Quality API (CAMS global) |
| no2_ugm3 | µg/m³ | Open-Meteo Air Quality API (CAMS global) |

Location: Ho Chi Minh City, latitude 10.82, longitude 106.63. Downloaded 23 October 2026.

## Suggested processing pipeline (for your algorithm design, Chapter 3.3)
1. Read hourly CSV.
2. Validate each value: missing, non-numeric, below 0, above a physical maximum (e.g. humidity > 100 %, rainfall > 200 mm/h, temperature outside 0 to 50 °C, PM > 1000 µg/m³). Remove duplicate timestamps.
3. Aggregate to daily: pollutants, temperature, humidity = mean of valid hours; rainfall = SUM of valid hours (mm/day).
4. Data-completeness rule: a day is valid only if it has at least 18 of 24 valid hours (75 %). Otherwise that variable is marked "insufficient data" for that day. Verify and cite the completeness rule you adopt.
5. Group daily values by month: min, max, average (+ rainfall monthly total).
6. Compare daily pollutant values with 24-hour WHO and QCVN limits: alerts + exceedance days per month.

## GENUINE source error (in both hourly files)
| Datetime | Column | Value | Note |
|---|---|---|---|
| 2026-07-02 00:00 to 06:00 | rainfall_mm | 990.0 (7 hours) | Physically impossible (would be about 6,930 mm in one morning). NASA POWER's own daily product gives 1.48 mm for this day, so this is an error in the hourly source data, likely a placeholder value. Your validation should flag it. Good real example for M1 / M4. |

Also worth noticing: the source contains some low humidity values (minimum 19.3 %) in dry-season afternoons. These are possible but unusual for HCMC; you can discuss whether a plausibility check is needed.

## Deliberately injected errors (hourly test file only)
| Datetime | Column | Injected value | Error type |
|---|---|---|---|
| 2025-10-05 14:00 | pm25_ugm3 | (empty) | missing value |
| 2025-11-12 08:00 to 15:00 | pm10_ugm3 | (empty) | sensor outage (8 h block, PM2.5 + PM10) (8 cells) |
| 2025-11-12 08:00 to 15:00 | pm25_ugm3 | (empty) | sensor outage (8 h block, PM2.5 + PM10) (8 cells) |
| 2025-12-20 03:00 | temperature_c | (empty) | missing value |
| 2026-01-15 09:00 | humidity_pct | (empty) | missing value |
| 2026-01-20 13:00 | rainfall_mm | -5.0 | impossible negative |
| 2026-02-02 18:00 | no2_ugm3 | (empty) | missing value |
| 2026-02-14 00:00 to 11:00 | no2_ugm3 | 38.6 | stuck sensor: same value 12 h in a row (optional check) (12 cells) |
| 2026-03-08 15:00 | humidity_pct | 135.0 | out of range (> 100 %) |
| 2026-03-27 05:00 | no2_ugm3 | 'ERR' | non-numeric text |
| 2026-04-01 12:00 | (whole row) | duplicated | duplicate timestamp |
| 2026-04-22 10:00 | pm10_ugm3 | 'abc' | non-numeric text |
| 2026-05-11 07:00 | no2_ugm3 | -12.0 | impossible negative |
| 2026-06-17 19:00 | pm25_ugm3 | 999.0 | extreme outlier / sensor error |
| 2026-07-03 22:00 | pm10_ugm3 | 2500.0 | extreme outlier / sensor error |
| 2026-08-25 12:00 | temperature_c | 85.0 | out of range temperature |
| 2026-09-09 16:00 | rainfall_mm | 'N/A' | non-numeric text |

## Important limitation
Both sources are MODELLED / satellite-reanalysis data on coarse grids (CAMS global about 45 km, 3-hourly interpolated to hourly; NASA POWER MERRA-2 about 0.5°), not measurements from a physical monitoring station. State this in Chapter 3.2 and Chapter 5 (Limitations).

## Suggested references (Harvard) - check format against your school's guide
- NASA Langley Research Center (2026) *POWER Project Data Access Viewer*. Available at: https://power.larc.nasa.gov/ (Accessed: 23 October 2026).
- Open-Meteo (2026) *Air Quality API*. Available at: https://open-meteo.com/en/docs/air-quality-api (Accessed: 23 October 2026). Data based on Copernicus Atmosphere Monitoring Service (CAMS) forecasts.

NASA POWER asks users to acknowledge: "These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program."
