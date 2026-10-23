# Algorithm design (original version - do not edit after first commit)

This file records the algorithms as designed BEFORE implementation.
It is compared with the final Python code in the report (D1).

## Algorithm 1: Data validation

```
ALGORITHM ValidateRecords
INPUT  records, VALID_RANGE
OUTPUT clean_records, error_log
seen <- empty set
FOR each record IN records
    IF record.datetime IN seen THEN
        log "duplicate"; CONTINUE
    END IF
    add record.datetime to seen
    FOR each variable IN VALID_RANGE
        value <- record[variable]
        IF value is missing OR value is not numeric THEN
            record[variable] <- None; log error
        ELSE IF value < minimum OR value > maximum THEN
            record[variable] <- None; log error
        END IF
    END FOR
    add record to clean_records
END FOR
RETURN clean_records, error_log
```

## Algorithm 2: Daily aggregation

```
ALGORITHM AggregateDaily
INPUT  clean_records, MIN_HOURS = 18
OUTPUT daily_values
group clean_records by date
FOR each date
    FOR each variable
        valid <- non-None values for this date
        n <- length(valid)
        IF n < MIN_HOURS THEN
            daily_values[date][variable] <- None
        ELSE IF variable = rainfall THEN
            daily_values[date][variable] <- SUM(valid)
        ELSE
            daily_values[date][variable] <- SUM(valid) / n
        END IF
    END FOR
END FOR
RETURN daily_values
```

## Algorithm 3: Monthly statistics

```
ALGORITHM MonthlyStatistics
INPUT  values (daily values of one variable for one month)
OUTPUT minimum, maximum, average
total <- 0; count <- 0
minimum <- None; maximum <- None
FOR each value IN values
    IF value is None THEN CONTINUE
    total <- total + value
    count <- count + 1
    IF minimum is None OR value < minimum THEN minimum <- value
    IF maximum is None OR value > maximum THEN maximum <- value
END FOR
IF count = 0 THEN RETURN "No valid data"
average <- total / count
RETURN minimum, maximum, average
```

## Algorithm 4: Threshold detection and compliance

```
ALGORITHM DetectExceedances
INPUT  daily_values, LIMITS
OUTPUT alerts, monthly_summary
alerts <- empty list
FOR each date IN daily_values
    FOR each pollutant IN {PM2.5, PM10, NO2}
        value <- daily_values[date][pollutant]
        IF value is None THEN CONTINUE
        FOR each standard IN {WHO, QCVN}
            limit <- GetLimit(standard, pollutant, date)
            IF value > limit THEN
                add (date, pollutant, value, limit, standard) to alerts
            END IF
        END FOR
    END FOR
END FOR
FOR each month, pollutant and standard
    rate <- exceedance_days / valid_days x 100
    compliant <- (exceedance_days = 0)
END FOR
RETURN alerts, monthly_summary
```

## Hand-worked example (expected test values)

Daily PM2.5: 42.0, 55.5, None, 50.0, 61.2, 38.3 (limit 50)
- minimum 38.3, maximum 61.2, average 49.4 (n = 5)
- alerts on day 2 and day 5 only (50.0 is not > 50)
- exceedance rate 2 / 5 x 100 = 40 %
