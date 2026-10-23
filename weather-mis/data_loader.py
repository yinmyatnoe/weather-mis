"""Procedural functions for reading and validating hourly CSV data.

Implements Algorithm 1 (data validation) from the design.
"""

import csv

from standards import DATETIME_COLUMN, VALID_RANGE


def load_csv(file_path):
    """Read a CSV file and return its rows as a list of dictionaries.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if a required column is missing.
    """
    with open(file_path, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        header = [name.strip() for name in (reader.fieldnames or [])]
        required = [DATETIME_COLUMN] + list(VALID_RANGE)
        missing_columns = [name for name in required if name not in header]
        if missing_columns:
            raise ValueError(f"Missing columns: {', '.join(missing_columns)}")
        rows = []
        for row in reader:
            rows.append({key.strip(): value for key, value in row.items()})
    return rows


def parse_value(raw_value):
    """Convert a raw CSV value to float.

    Returns:
        (value, reason): the float value and None if valid,
        or None and a short reason if the value is missing or non-numeric.
    """
    if raw_value is None or raw_value.strip() == "":
        return None, "missing"
    try:
        return float(raw_value), None
    except ValueError:
        return None, "non-numeric"


def validate_records(rows):
    """Validate hourly rows (Algorithm 1).

    Duplicate timestamps are skipped. Missing, non-numeric and
    out-of-range values are replaced with None and logged, so the
    remaining valid values in the same record are kept.

    Returns:
        (clean_records, error_log), where error_log is a list of
        (datetime, column, raw_value, reason) tuples.
    """
    seen_timestamps = set()
    clean_records = []
    error_log = []
    for row in rows:
        timestamp = row.get(DATETIME_COLUMN, "").strip()
        if timestamp in seen_timestamps:
            error_log.append((timestamp, "(whole row)", "", "duplicate"))
            continue
        seen_timestamps.add(timestamp)

        record = {DATETIME_COLUMN: timestamp}
        for column, (low, high) in VALID_RANGE.items():
            raw_value = row.get(column)
            value, reason = parse_value(raw_value)
            if value is not None and not low <= value <= high:
                value, reason = None, "out of range"
            if reason is not None:
                error_log.append((timestamp, column, raw_value, reason))
            record[column] = value
        clean_records.append(record)
    return clean_records, error_log
