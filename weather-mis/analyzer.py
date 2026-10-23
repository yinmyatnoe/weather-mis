"""Object-oriented processing layer: aggregation, statistics and alerts.

Implements Algorithms 2, 3 and 4 from the design.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from data_loader import load_csv, validate_records
from standards import (DATETIME_COLUMN, DISPLAY_NAMES, MIN_VALID_HOURS,
                       POLLUTANTS, STANDARDS, SUM_VARIABLES, VARIABLES,
                       get_limit)


@dataclass
class Alert:
    """One day on which a pollutant exceeded a 24-hour limit."""

    date: date
    pollutant: str
    value: float
    limit: float
    standard: str

    def __str__(self):
        name = DISPLAY_NAMES[self.pollutant].split(" ")[0]
        return (f"{self.date} | {name} | {self.value:.1f} > "
                f"{self.limit:.0f} ({self.standard})")


class ClimateAnalyzer:
    """Stores the station data and performs all calculations."""

    def __init__(self):
        self._records = []
        self._daily_values = {}
        self._error_log = []
        self._alerts = []

    @property
    def record_count(self):
        return len(self._records)

    @property
    def error_log(self):
        return list(self._error_log)

    @property
    def daily_values(self):
        return self._daily_values

    @property
    def alerts(self):
        return list(self._alerts)

    def load(self, file_path):
        """Load and validate a CSV file; return the number of records."""
        rows = load_csv(file_path)
        self._records, self._error_log = validate_records(rows)
        self._daily_values = {}
        self._alerts = []
        return len(self._records)

    def aggregate_daily(self):
        """Convert valid hourly values into daily values (Algorithm 2)."""
        hours_by_date = defaultdict(list)
        for record in self._records:
            day = date.fromisoformat(record[DATETIME_COLUMN][:10])
            hours_by_date[day].append(record)

        self._daily_values = {}
        for day in sorted(hours_by_date):
            self._daily_values[day] = {}
            for variable in VARIABLES:
                valid = [record[variable] for record in hours_by_date[day]
                         if record[variable] is not None]
                if len(valid) < MIN_VALID_HOURS:
                    daily_value = None
                elif variable in SUM_VARIABLES:
                    daily_value = sum(valid)
                else:
                    daily_value = sum(valid) / len(valid)
                self._daily_values[day][variable] = daily_value
        return self._daily_values

    @staticmethod
    def calculate_statistics(values):
        """Return min, max, average and total of valid values (Algorithm 3).

        None values are skipped. Returns None if no valid value exists.
        """
        total = 0.0
        count = 0
        minimum = None
        maximum = None
        for value in values:
            if value is None:
                continue
            total += value
            count += 1
            if minimum is None or value < minimum:
                minimum = value
            if maximum is None or value > maximum:
                maximum = value
        if count == 0:
            return None
        return {"min": minimum, "max": maximum,
                "average": total / count, "total": total, "count": count}

    def months(self):
        """Return the sorted list of months ("YYYY-MM") in the daily data."""
        return sorted({day.strftime("%Y-%m") for day in self._daily_values})

    def monthly_statistics(self, variable):
        """Return {month: statistics} for one variable."""
        values_by_month = defaultdict(list)
        for day, values in self._daily_values.items():
            values_by_month[day.strftime("%Y-%m")].append(values[variable])
        return {month: self.calculate_statistics(values)
                for month, values in sorted(values_by_month.items())}

    def detect_exceedances(self):
        """Create an Alert for every daily value above a limit (Algorithm 4)."""
        self._alerts = []
        for day, values in self._daily_values.items():
            for pollutant in POLLUTANTS:
                value = values[pollutant]
                if value is None:
                    continue
                for standard in STANDARDS:
                    limit = get_limit(standard, pollutant, day)
                    if value > limit:
                        self._alerts.append(
                            Alert(day, pollutant, value, limit, standard))
        return self.alerts

    def exceedance_summary(self):
        """Return exceedance days, rate (%) and compliance per month.

        Keys are (month, pollutant, standard) tuples.
        """
        valid_days = defaultdict(int)
        for day, values in self._daily_values.items():
            for pollutant in POLLUTANTS:
                if values[pollutant] is not None:
                    valid_days[(day.strftime("%Y-%m"), pollutant)] += 1

        exceeded_days = defaultdict(int)
        for alert in self._alerts:
            key = (alert.date.strftime("%Y-%m"), alert.pollutant,
                   alert.standard)
            exceeded_days[key] += 1

        summary = {}
        for (month, pollutant), days in sorted(valid_days.items()):
            for standard in STANDARDS:
                key = (month, pollutant, standard)
                count = exceeded_days[key]
                summary[key] = {"days": count, "valid_days": days,
                                "rate": count / days * 100,
                                "compliant": count == 0}
        return summary

    def plot_pollutant(self, pollutant, figure=None):
        """Plot daily values of a pollutant with WHO and QCVN limits."""
        from matplotlib.figure import Figure

        figure = figure or Figure(figsize=(9, 3.5))
        figure.clear()
        axes = figure.add_subplot(111)
        days = sorted(self._daily_values)
        values = [self._daily_values[day][pollutant] for day in days]
        axes.plot(days, values, color="black", linewidth=1,
                  label="Daily average")
        axes.plot(days, [get_limit("QCVN", pollutant, day) for day in days],
                  color="black", linestyle="--", linewidth=1,
                  label="QCVN 24-hour limit")
        axes.plot(days, [get_limit("WHO", pollutant, day) for day in days],
                  color="black", linestyle=":", linewidth=1,
                  label="WHO 24-hour limit")
        axes.set_title(f"Daily {DISPLAY_NAMES[pollutant]} in Ho Chi Minh City")
        axes.set_xlabel("Date")
        axes.set_ylabel(DISPLAY_NAMES[pollutant])
        axes.legend(loc="upper right", fontsize=8)
        figure.autofmt_xdate()
        figure.tight_layout()
        return figure
