from statistics import mean

from fitbit_test import (
    get_exercise_history,
    get_sleep_history,
    get_resting_heart_rate_history,
    get_hrv_history,
    get_oxygen_saturation_history,
    get_respiratory_rate_history,
    get_sleep_temperature_history,
    get_weight_history
)


# ============================================================
# BASIC HELPERS
# ============================================================

def to_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except:
        return None


def average(values):
    clean = [
        to_float(value)
        for value in values
        if to_float(value) is not None
    ]

    if not clean:
        return None

    return round(mean(clean), 2)


def total(values):
    clean = [
        to_float(value)
        for value in values
        if to_float(value) is not None
    ]

    if not clean:
        return 0

    return round(sum(clean), 2)


def percent_change(old, new):
    old = to_float(old)
    new = to_float(new)

    if old is None or new is None:
        return None

    if old == 0:
        return None

    return round(
        ((new - old) / old) * 100,
        2
    )


def describe_direction(first, last):
    first = to_float(first)
    last = to_float(last)

    if first is None or last is None:
        return "unknown"

    difference = last - first

    if abs(difference) < 0.01:
        return "stable"

    if difference > 0:
        return "increased"

    return "decreased"


def summarize_values(values):
    clean = [
        to_float(value)
        for value in values
        if to_float(value) is not None
    ]

    if not clean:
        return {
            "record_count": 0,
            "average": None,
            "minimum": None,
            "maximum": None,
            "first": None,
            "last": None,
            "change": None,
            "percent_change": None,
            "direction": "unknown"
        }

    first = clean[0]
    last = clean[-1]

    return {
        "record_count": len(clean),
        "average": round(mean(clean), 2),
        "minimum": round(min(clean), 2),
        "maximum": round(max(clean), 2),
        "first": round(first, 2),
        "last": round(last, 2),
        "change": round(last - first, 2),

        "percent_change":
            percent_change(
                first,
                last
            ),

        "direction":
            describe_direction(
                first,
                last
            )
    }


# ============================================================
# GENERIC METRIC TREND
# ============================================================

def analyze_metric_trend(
    metric,
    start_date,
    end_date
):
    metric = metric.lower().strip()

    if metric in [
        "resting_heart_rate",
        "resting heart rate",
        "rhr"
    ]:
        records = get_resting_heart_rate_history(
            start_date,
            end_date
        )

        values = [
            item.get(
                "resting_heart_rate_bpm"
            )
            for item in reversed(records)
        ]

        metric_name = "resting_heart_rate_bpm"

    elif metric in [
        "hrv",
        "heart_rate_variability",
        "heart rate variability"
    ]:
        records = get_hrv_history(
            start_date,
            end_date
        )

        values = [
            item.get("average_hrv_ms")
            for item in reversed(records)
        ]

        metric_name = "average_hrv_ms"

    elif metric in [
        "spo2",
        "oxygen",
        "oxygen_saturation",
        "oxygen saturation"
    ]:
        records = get_oxygen_saturation_history(
            start_date,
            end_date
        )

        values = [
            item.get(
                "average_spo2_percent"
            )
            for item in reversed(records)
        ]

        metric_name = "average_spo2_percent"

    elif metric in [
        "respiratory_rate",
        "respiratory rate",
        "breathing_rate"
    ]:
        records = get_respiratory_rate_history(
            start_date,
            end_date
        )

        values = [
            item.get(
                "breaths_per_minute"
            )
            for item in reversed(records)
        ]

        metric_name = "breaths_per_minute"

    elif metric in [
        "temperature",
        "sleep_temperature",
        "sleep temperature"
    ]:
        records = get_sleep_temperature_history(
            start_date,
            end_date
        )

        values = [
            item.get(
                "difference_from_baseline_celsius"
            )
            for item in reversed(records)
        ]

        metric_name = (
            "difference_from_baseline_celsius"
        )

    elif metric in [
        "weight",
        "body_weight",
        "body weight"
    ]:
        records = get_weight_history(
            start_date,
            end_date
        )

        values = [
            item.get("weight_pounds")
            for item in reversed(records)
        ]

        metric_name = "weight_pounds"

    else:
        raise ValueError(
            "Unsupported metric. Use one of: "
            "resting_heart_rate, hrv, spo2, "
            "respiratory_rate, sleep_temperature, "
            "weight"
        )

    summary = summarize_values(values)

    halfway = len(values) // 2

    first_half = values[:halfway]
    second_half = values[halfway:]

    summary.update({
        "metric":
            metric_name,

        "start_date":
            start_date,

        "end_date":
            end_date,

        "first_half_average":
            average(first_half),

        "second_half_average":
            average(second_half),

        "records":
            records
    })

    return summary


# ============================================================
# PERIOD COMPARISON
# ============================================================

def compare_metric_periods(
    metric,
    period1_start,
    period1_end,
    period2_start,
    period2_end
):
    period1 = analyze_metric_trend(
        metric,
        period1_start,
        period1_end
    )

    period2 = analyze_metric_trend(
        metric,
        period2_start,
        period2_end
    )

    average1 = period1.get("average")
    average2 = period2.get("average")

    difference = None

    if (
        average1 is not None
        and average2 is not None
    ):
        difference = round(
            average2 - average1,
            2
        )

    return {
        "metric":
            period1.get("metric"),

        "period_1": {
            "start":
                period1_start,

            "end":
                period1_end,

            "record_count":
                period1.get(
                    "record_count"
                ),

            "average":
                average1
        },

        "period_2": {
            "start":
                period2_start,

            "end":
                period2_end,

            "record_count":
                period2.get(
                    "record_count"
                ),

            "average":
                average2
        },

        "difference":
            difference,

        "percent_change":
            percent_change(
                average1,
                average2
            ),

        "direction":
            describe_direction(
                average1,
                average2
            )
    }


# ============================================================
# EXERCISE CLEANUP / DERIVED METRICS
# ============================================================

def clean_exercise_records(records):
    cleaned = []

    for item in records:
        duration = to_float(
            item.get("duration_minutes")
        )

        distance = to_float(
            item.get("distance_miles")
        )

        # Remove accidental / junk exercise records
        if duration is None or duration < 5:
            continue

        pace = to_float(
            item.get(
                "average_pace_minutes_per_mile"
            )
        )

        # Fitbit often leaves treadmill pace blank.
        # Calculate pace using duration / distance.
        if (
            pace is None
            and distance is not None
            and distance > 0
        ):
            pace = round(
                duration / distance,
                2
            )

        cleaned_item = dict(item)

        cleaned_item[
            "average_pace_minutes_per_mile"
        ] = pace

        cleaned.append(
            cleaned_item
        )

    return cleaned


# ============================================================
# EXERCISE SUMMARY
# ============================================================

def exercise_summary(records):
    if not records:
        return {
            "workouts": 0,
            "total_duration_minutes": 0,
            "average_duration_minutes": None,
            "total_distance_miles": 0,
            "average_distance_miles": None,
            "total_calories": 0,
            "total_active_zone_minutes": 0,
            "average_heart_rate_bpm": None,
            "average_pace_minutes_per_mile": None
        }

    durations = [
        item.get("duration_minutes")
        for item in records
    ]

    distances = [
        item.get("distance_miles")
        for item in records
    ]

    calories = [
        item.get("calories")
        for item in records
    ]

    zone_minutes = [
        item.get("active_zone_minutes")
        for item in records
    ]

    heart_rates = [
        item.get(
            "average_heart_rate_bpm"
        )
        for item in records
    ]

    paces = [
        item.get(
            "average_pace_minutes_per_mile"
        )
        for item in records
    ]

    return {
        "workouts":
            len(records),

        "total_duration_minutes":
            total(durations),

        "average_duration_minutes":
            average(durations),

        "total_distance_miles":
            total(distances),

        "average_distance_miles":
            average(distances),

        "total_calories":
            total(calories),

        "total_active_zone_minutes":
            total(zone_minutes),

        "average_heart_rate_bpm":
            average(heart_rates),

        "average_pace_minutes_per_mile":
            average(paces)
    }


# ============================================================
# EXERCISE PROGRESS
# ============================================================

def analyze_exercise_progress(
    start_date,
    end_date,
    exercise_type=None
):
    records = get_exercise_history(
        start_date,
        end_date,
        exercise_type
    )

    records = clean_exercise_records(
        records
    )

    # Oldest first
    records = list(reversed(records))

    full_summary = exercise_summary(
        records
    )

    halfway = len(records) // 2

    first_half_records = records[:halfway]
    second_half_records = records[halfway:]

    first_half = exercise_summary(
        first_half_records
    )

    second_half = exercise_summary(
        second_half_records
    )

    heart_rate_change = None

    if (
        first_half.get(
            "average_heart_rate_bpm"
        ) is not None
        and second_half.get(
            "average_heart_rate_bpm"
        ) is not None
    ):
        heart_rate_change = round(
            second_half[
                "average_heart_rate_bpm"
            ]
            -
            first_half[
                "average_heart_rate_bpm"
            ],
            2
        )

    pace_change = None

    if (
        first_half.get(
            "average_pace_minutes_per_mile"
        ) is not None
        and second_half.get(
            "average_pace_minutes_per_mile"
        ) is not None
    ):
        pace_change = round(
            second_half[
                "average_pace_minutes_per_mile"
            ]
            -
            first_half[
                "average_pace_minutes_per_mile"
            ],
            2
        )

    distance_change = None

    if (
        first_half.get(
            "average_distance_miles"
        ) is not None
        and second_half.get(
            "average_distance_miles"
        ) is not None
    ):
        distance_change = round(
            second_half[
                "average_distance_miles"
            ]
            -
            first_half[
                "average_distance_miles"
            ],
            2
        )

    duration_change = None

    if (
        first_half.get(
            "average_duration_minutes"
        ) is not None
        and second_half.get(
            "average_duration_minutes"
        ) is not None
    ):
        duration_change = round(
            second_half[
                "average_duration_minutes"
            ]
            -
            first_half[
                "average_duration_minutes"
            ],
            2
        )

    return {
        "start_date":
            start_date,

        "end_date":
            end_date,

        "exercise_type":
            exercise_type,

        "overall":
            full_summary,

        "first_half":
            first_half,

        "second_half":
            second_half,

        "changes": {
            "average_heart_rate_bpm":
                heart_rate_change,

            "average_pace_minutes_per_mile":
                pace_change,

            "average_distance_miles":
                distance_change,

            "average_duration_minutes":
                duration_change
        },

        "workouts":
            records
    }


# ============================================================
# HEALTH SUMMARY
# ============================================================

def get_health_summary(
    start_date,
    end_date
):
    resting = get_resting_heart_rate_history(
        start_date,
        end_date
    )

    hrv = get_hrv_history(
        start_date,
        end_date
    )

    oxygen = get_oxygen_saturation_history(
        start_date,
        end_date
    )

    respiratory = get_respiratory_rate_history(
        start_date,
        end_date
    )

    temperature = get_sleep_temperature_history(
        start_date,
        end_date
    )

    sleep = get_sleep_history(
        start_date,
        end_date
    )

    exercise = get_exercise_history(
        start_date,
        end_date
    )

    exercise = clean_exercise_records(
        exercise
    )

    weight = get_weight_history(
        start_date,
        end_date
    )

    sleep_minutes = [
        item.get("minutes_asleep")
        for item in sleep
    ]

    deep_sleep_minutes = []
    rem_sleep_minutes = []

    for item in sleep:
        totals = item.get(
            "sleep_stage_totals",
            {}
        )

        deep = totals.get("DEEP", {})
        rem = totals.get("REM", {})

        if deep.get("minutes") is not None:
            deep_sleep_minutes.append(
                deep.get("minutes")
            )

        if rem.get("minutes") is not None:
            rem_sleep_minutes.append(
                rem.get("minutes")
            )

    minimum_spo2_values = [
        to_float(
            item.get(
                "minimum_spo2_percent"
            )
        )
        for item in oxygen
        if to_float(
            item.get(
                "minimum_spo2_percent"
            )
        ) is not None
    ]

    return {
        "start_date":
            start_date,

        "end_date":
            end_date,

        "resting_heart_rate": {
            "records":
                len(resting),

            "average_bpm":
                average([
                    item.get(
                        "resting_heart_rate_bpm"
                    )
                    for item in resting
                ])
        },

        "hrv": {
            "records":
                len(hrv),

            "average_ms":
                average([
                    item.get(
                        "average_hrv_ms"
                    )
                    for item in hrv
                ])
        },

        "oxygen_saturation": {
            "records":
                len(oxygen),

            "average_percent":
                average([
                    item.get(
                        "average_spo2_percent"
                    )
                    for item in oxygen
                ]),

            "lowest_recorded_bound_percent":
                min(minimum_spo2_values)
                if minimum_spo2_values
                else None
        },

        "respiratory_rate": {
            "records":
                len(respiratory),

            "average_breaths_per_minute":
                average([
                    item.get(
                        "breaths_per_minute"
                    )
                    for item in respiratory
                ])
        },

        "sleep_temperature": {
            "records":
                len(temperature),

            "average_difference_from_baseline_c":
                average([
                    item.get(
                        "difference_from_baseline_celsius"
                    )
                    for item in temperature
                ])
        },

        "sleep": {
            "sessions":
                len(sleep),

            "average_minutes_asleep":
                average(
                    sleep_minutes
                ),

            "average_deep_sleep_minutes":
                average(
                    deep_sleep_minutes
                ),

            "average_rem_sleep_minutes":
                average(
                    rem_sleep_minutes
                )
        },

        "exercise":
            exercise_summary(
                exercise
            ),

        "weight": {
            "records":
                len(weight),

            "average_pounds":
                average([
                    item.get(
                        "weight_pounds"
                    )
                    for item in weight
                ]),

            "records_raw":
                weight
        }
    }

# ============================================================
# DAILY HEALTH SUMMARY
# ============================================================

def get_daily_health_summary(date=None):

    from fitbit_test import (
        get_steps,
        get_distance,
        get_total_calories,
        get_active_energy_burned,
        get_active_zone_minutes,
        get_resting_heart_rate,
        get_hrv,
        get_recent_sleep
    )

    return {
        "steps":
            get_steps(date),

        "distance":
            get_distance(date),

        "calories":
            get_total_calories(date),

        "active_energy":
            get_active_energy_burned(date),

        "active_zone_minutes":
            get_active_zone_minutes(date),

        "resting_heart_rate":
            get_resting_heart_rate(date),

        "hrv":
            get_hrv(date),

        "sleep":
            get_recent_sleep()
    }


# ============================================================
# DATA QUALITY ASSESSMENT
# ============================================================

def analyze_fitbit_data_quality():

    history = get_resting_heart_rate_history(
        "2024-01-01",
        "2026-12-31"
    )

    records = len(history)

    if records == 0:
        return {
            "device": "Fitbit Charge 5",
            "status": "no_data"
        }

    dates = []

    for item in history:
        date = item.get("date")

        if date:
            dates.append(date)

    return {
        "device": "Fitbit Charge 5",
        "status": "available",
        "historical_records": records,
        "baseline_assessment": "rebuilding",
        "notes": [
            "Historical Fitbit data contains gaps",
            "Current August 2026 measurements should be treated as a new baseline"
        ]
    }
