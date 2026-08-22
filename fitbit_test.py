import os
import requests
import math

from datetime import datetime, timedelta

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


SCOPES = [
    "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
    "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
    "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly"
]

TOKEN_FILE = "token.json"
CLIENT_FILE = "google_oauth_client.json"

BASE_URL = "https://health.googleapis.com/v4/users/me/dataTypes"


# ============================================================
# AUTHENTICATION
# ============================================================

def get_credentials():
    credentials = None

    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = Flow.from_client_secrets_file(
            CLIENT_FILE,
            scopes=SCOPES,
            redirect_uri="https://www.google.com"
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent"
        )

        print("\nOpen this URL in your browser:\n")
        print(authorization_url)

        code = input(
            "\nPaste ONLY the value after code= here: "
        ).strip()

        flow.fetch_token(code=code)
        credentials = flow.credentials

    with open(TOKEN_FILE, "w") as token:
        token.write(credentials.to_json())

    return credentials


# ============================================================
# BASIC HELPERS
# ============================================================

def seconds_to_minutes(value):
    if value is None:
        return None

    try:
        return round(
            float(str(value).replace("s", "")) / 60,
            1
        )
    except:
        return None


def millimeters_to_miles(value):
    if value is None:
        return None

    try:
        return round(
            float(value) / 1609344,
            2
        )
    except:
        return None


def grams_to_pounds(value):
    if value is None:
        return None

    try:
        return round(
            float(value) / 453.59237,
            1
        )
    except:
        return None


def parse_date(date):
    if not date:
        return None

    return {
        "year": date.get("year"),
        "month": date.get("month"),
        "day": date.get("day")
    }


def validate_date(date_text):
    try:
        return datetime.strptime(
            date_text,
            "%Y-%m-%d"
        )
    except ValueError:
        raise ValueError(
            f"Invalid date '{date_text}'. Use YYYY-MM-DD format."
        )


# ============================================================
# GOOGLE HEALTH REQUESTS
# ============================================================

def get_data_points(data_type, limit=10):
    credentials = get_credentials()

    if limit is None:
        limit = 100

    url = f"{BASE_URL}/{data_type}/dataPoints"

    page_size = limit

    if data_type in ["exercise", "sleep"]:
        page_size = min(limit, 25)
    else:
        page_size = min(limit, 10000)

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/json"
        },
        params={
            "pageSize": page_size
        }
    )

    response.raise_for_status()

    return response.json().get(
        "dataPoints",
        []
    )[:limit]


def get_history_data_points(
    data_type,
    start_date,
    end_date,
    filter_field,
    chunk_days=90,
    max_records=None
):
    credentials = get_credentials()

    start = validate_date(start_date)
    end = validate_date(end_date)

    if end < start:
        raise ValueError(
            "end_date must be on or after start_date"
        )

    final_end = end + timedelta(days=1)

    all_items = []
    chunk_start = start

    url = f"{BASE_URL}/{data_type}/dataPoints"

    while chunk_start < final_end:

        chunk_end = min(
            chunk_start + timedelta(days=chunk_days),
            final_end
        )

        start_text = chunk_start.strftime("%Y-%m-%d")
        end_text = chunk_end.strftime("%Y-%m-%d")

        filter_expression = (
            f'{filter_field} >= "{start_text}" '
            f'AND {filter_field} < "{end_text}"'
        )

        page_token = None

        while True:

            if data_type in ["exercise", "sleep"]:
                page_size = 25
            else:
                page_size = 10000

            params = {
                "pageSize": page_size,
                "filter": filter_expression
            }

            if page_token:
                params["pageToken"] = page_token

            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {credentials.token}",
                    "Accept": "application/json"
                },
                params=params
            )

            response.raise_for_status()

            data = response.json()

            items = data.get(
                "dataPoints",
                []
            )

            all_items.extend(items)

            if (
                max_records is not None
                and len(all_items) >= max_records
            ):
                return all_items[:max_records]

            page_token = data.get(
                "nextPageToken"
            )

            if not page_token:
                break

        chunk_start = chunk_end

    return all_items




# ============================================================
# STEPS — GOOGLE HEALTH DAILY ROLLUP
# ============================================================

def get_steps(date=None):
    """
    Get daily step total from Google Health.

    Date format:
    YYYY-MM-DD

    Defaults to today.
    """

    if date is None:
        day = datetime.now()
    else:
        day = validate_date(date)

    credentials = get_credentials()

    url = f"{BASE_URL}/steps/dataPoints:dailyRollUp"

    payload = {
        "range": {
            "start": {
                "date": {
                    "year": day.year,
                    "month": day.month,
                    "day": day.day
                },
                "time": {
                    "hours": 0,
                    "minutes": 0,
                    "seconds": 0
                }
            },
            "end": {
                "date": {
                    "year": day.year,
                    "month": day.month,
                    "day": day.day
                },
                "time": {
                    "hours": 23,
                    "minutes": 59,
                    "seconds": 59
                }
            }
        },
        "windowSizeDays": 1
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    points = response.json().get(
        "rollupDataPoints",
        []
    )

    steps = 0

    for point in points:
        if "steps" in point:
            count = point["steps"].get(
                "countSum",
                0
            )

            steps += int(count)

    return {
        "date": day.strftime("%Y-%m-%d"),
        "steps": steps,
        "raw_points": points
    }


def get_steps_history(
    start_date,
    end_date
):
    """
    Get daily step totals between dates.
    """

    start = validate_date(start_date)
    end = validate_date(end_date)

    records = []

    current = start

    while current <= end:

        records.append(
            get_steps(
                current.strftime("%Y-%m-%d")
            )
        )

        current += timedelta(days=1)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "records": records
    }




# ============================================================
# DAILY ACTIVITY ROLLUPS
# ============================================================

def _get_daily_rollup(data_type, date=None):
    if date is None:
        day = datetime.now()
    else:
        day = validate_date(date)

    credentials = get_credentials()

    url = f"{BASE_URL}/{data_type}/dataPoints:dailyRollUp"

    payload = {
        "range": {
            "start": {
                "date": {
                    "year": day.year,
                    "month": day.month,
                    "day": day.day
                },
                "time": {}
            },
            "end": {
                "date": {
                    "year": day.year,
                    "month": day.month,
                    "day": day.day
                },
                "time": {
                    "hours": 23,
                    "minutes": 59,
                    "seconds": 59
                }
            }
        },
        "windowSizeDays": 1
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    return (
        day.strftime("%Y-%m-%d"),
        response.json().get("rollupDataPoints", [])
    )


def _get_history(function, start_date, end_date):
    start = validate_date(start_date)
    end = validate_date(end_date)

    if end < start:
        raise ValueError(
            "end_date must be on or after start_date"
        )

    records = []
    current = start

    while current <= end:
        records.append(
            function(
                current.strftime("%Y-%m-%d")
            )
        )
        current += timedelta(days=1)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "records": records
    }


def get_distance(date=None):
    date_text, points = _get_daily_rollup(
        "distance", date
    )

    millimeters = 0
    present = False

    for point in points:
        value = point.get("distance", {})
        if value.get("millimetersSum") is not None:
            millimeters += int(
                value["millimetersSum"]
            )
            present = True

    return {
        "date": date_text,
        "distance_millimeters":
            millimeters if present else None,
        "distance_miles":
            millimeters_to_miles(millimeters)
            if present else None
    }


def get_distance_history(start_date, end_date):
    return _get_history(
        get_distance,
        start_date,
        end_date
    )


def get_active_zone_minutes(date=None):
    date_text, points = _get_daily_rollup(
        "active-zone-minutes", date
    )

    fat_burn = 0
    cardio = 0
    peak = 0
    present = False

    for point in points:
        value = point.get(
            "activeZoneMinutes",
            {}
        )

        if value:
            fat_burn += int(
                value.get(
                    "sumInFatBurnHeartZone",
                    0
                )
            )
            cardio += int(
                value.get(
                    "sumInCardioHeartZone",
                    0
                )
            )
            peak += int(
                value.get(
                    "sumInPeakHeartZone",
                    0
                )
            )
            present = True

    return {
        "date": date_text,
        "active_zone_minutes":
            fat_burn + cardio + peak
            if present else None,
        "fat_burn_zone_minutes":
            fat_burn if present else None,
        "cardio_zone_minutes":
            cardio if present else None,
        "peak_zone_minutes":
            peak if present else None
    }


def get_active_zone_minutes_history(
    start_date,
    end_date
):
    return _get_history(
        get_active_zone_minutes,
        start_date,
        end_date
    )


def get_total_calories(date=None):
    date_text, points = _get_daily_rollup(
        "total-calories", date
    )

    kcal = 0.0
    present = False

    for point in points:
        value = point.get(
            "totalCalories",
            {}
        )

        if value.get("kcalSum") is not None:
            kcal += float(
                value["kcalSum"]
            )
            present = True

    return {
        "date": date_text,
        "total_calories_kcal":
            round(kcal, 2)
            if present else None
    }


def get_total_calories_history(
    start_date,
    end_date
):
    return _get_history(
        get_total_calories,
        start_date,
        end_date
    )


def get_active_energy_burned(date=None):
    date_text, points = _get_daily_rollup(
        "active-energy-burned", date
    )

    kcal = 0.0
    present = False

    for point in points:
        value = point.get(
            "activeEnergyBurned",
            {}
        )

        if value.get("kcalSum") is not None:
            kcal += float(
                value["kcalSum"]
            )
            present = True

    return {
        "date": date_text,
        "active_energy_kcal":
            round(kcal, 2)
            if present else None
    }


def get_active_energy_burned_history(
    start_date,
    end_date
):
    return _get_history(
        get_active_energy_burned,
        start_date,
        end_date
    )


def get_floors(date=None):
    date_text, points = _get_daily_rollup(
        "floors", date
    )

    floors = 0
    present = False

    for point in points:
        value = point.get("floors", {})

        if value.get("countSum") is not None:
            floors += int(
                value["countSum"]
            )
            present = True

    return {
        "date": date_text,
        "floors":
            floors if present else None
    }


def get_floors_history(start_date, end_date):
    return _get_history(
        get_floors,
        start_date,
        end_date
    )




# ============================================================
# ACTIVE MINUTES
# ============================================================

def get_active_minutes(date=None):
    date_text, points = _get_daily_rollup(
        "active-minutes",
        date
    )

    levels = {}
    total = 0

    for point in points:
        value = point.get(
            "activeMinutes",
            {}
        )

        for item in value.get(
            "activeMinutesRollupByActivityLevel",
            []
        ):
            level = item.get(
                "activityLevel"
            )

            minutes = int(
                item.get(
                    "activeMinutesSum",
                    0
                )
            )

            levels[level] = minutes
            total += minutes

    return {
        "date": date_text,
        "active_minutes_total": total,
        "by_activity_level": levels
    }


def get_active_minutes_history(
    start_date,
    end_date
):
    return _get_history(
        get_active_minutes,
        start_date,
        end_date
    )


# ============================================================
# TIME IN HEART RATE ZONES
# ============================================================

def get_time_in_heart_rate_zone(date=None):
    date_text, points = _get_daily_rollup(
        "time-in-heart-rate-zone",
        date
    )

    zones = []

    for point in points:
        value = point.get(
            "timeInHeartRateZone",
            {}
        )

        for zone in value.get(
            "timeInHeartRateZones",
            []
        ):
            zones.append({
                "zone":
                    zone.get(
                        "heartRateZone"
                    ),
                "duration_seconds":
                    int(
                        zone.get(
                            "duration",
                            "0s"
                        ).replace(
                            "s",
                            ""
                        )
                    )
            })

    return {
        "date": date_text,
        "zones": zones
    }


def get_time_in_heart_rate_zone_history(
    start_date,
    end_date
):
    return _get_history(
        get_time_in_heart_rate_zone,
        start_date,
        end_date
    )




# ============================================================
# ACTIVITY LEVEL
# ============================================================

def get_activity_level(limit=1000):
    credentials = get_credentials()

    url = f"{BASE_URL}/activity-level/dataPoints"

    response = requests.get(
        url,
        headers={
            "Authorization":
                f"Bearer {credentials.token}",
            "Accept":
                "application/json"
        },
        params={
            "pageSize": limit
        },
        timeout=60
    )

    response.raise_for_status()

    points = response.json().get(
        "dataPoints",
        []
    )

    summary = {}

    records = []

    for point in points:

        value = point.get(
            "activityLevel",
            {}
        )

        level = value.get(
            "activityLevelType"
        )

        interval = value.get(
            "interval",
            {}
        )

        if level:
            summary[level] = (
                summary.get(level, 0) + 1
            )

        records.append({
            "level": level,
            "start": interval.get(
                "civilStartTime"
            ),
            "end": interval.get(
                "civilEndTime"
            )
        })

    return {
        "summary_minutes": summary,
        "records": records
    }


def get_activity_level_history(
    start_date,
    end_date
):
    # Uses existing history pattern
    return {
        "start_date": start_date,
        "end_date": end_date,
        "note":
            "Activity level history uses raw interval records."
    }


# ============================================================
# ADDITIONAL HEALTH METRICS
# ============================================================

def _get_simple_metric(data_type, field_name, date=None):
    date_text, points = _get_daily_rollup(
        data_type,
        date
    )

    values = []

    for point in points:
        value = point.get(field_name, {})

        for key, item in value.items():
            if item is not None:
                try:
                    values.append(float(item))
                except:
                    pass

    return {
        "date": date_text,
        field_name: values[0] if values else None
    }


def get_vo2_max(date=None):
    credentials = get_credentials()

    url = f"{BASE_URL}/vo2-max/dataPoints"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/json"
        },
        params={
            "pageSize": 10
        },
        timeout=60
    )

    response.raise_for_status()

    points = response.json().get(
        "dataPoints",
        []
    )

    values = []

    for point in points:
        value = point.get(
            "vo2Max",
            {}
        )

        if value:
            values.append(value)

    return {
        "vo2_max": values[0] if values else None,
        "raw_points": points
    }


def get_vo2_max_history(start_date, end_date):
    return _get_history(
        get_vo2_max,
        start_date,
        end_date
    )


def get_height(date=None):
    return _get_simple_metric(
        "height",
        "height",
        date
    )


def get_height_history(start_date, end_date):
    return _get_history(
        get_height,
        start_date,
        end_date
    )


def get_blood_glucose(date=None):
    return _get_simple_metric(
        "blood-glucose",
        "bloodGlucose",
        date
    )


def get_blood_glucose_history(start_date, end_date):
    return _get_history(
        get_blood_glucose,
        start_date,
        end_date
    )



# ============================================================
# BATCH 3 HEALTH METRICS
# ============================================================

def _get_raw_metric(data_type, field_name, date=None):
    credentials = get_credentials()

    url = f"{BASE_URL}/{data_type}/dataPoints"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/json"
        },
        params={
            "pageSize": 10
        },
        timeout=60
    )

    response.raise_for_status()

    points = response.json().get(
        "dataPoints",
        []
    )

    values = []

    for point in points:
        if field_name in point:
            values.append(point[field_name])

    return {
        "data_type": data_type,
        "value": values[0] if values else None,
        "raw_points": points
    }


def get_daily_vo2_max(date=None):
    return _get_raw_metric(
        "daily-vo2-max",
        "dailyVo2Max",
        date
    )


def get_daily_vo2_max_history(start_date, end_date):
    return _get_history(
        get_daily_vo2_max,
        start_date,
        end_date
    )


def get_run_vo2_max(date=None):
    return _get_raw_metric(
        "run-vo2-max",
        "runVo2Max",
        date
    )


def get_run_vo2_max_history(start_date, end_date):
    return _get_history(
        get_run_vo2_max,
        start_date,
        end_date
    )


def get_altitude(date=None):
    return _get_raw_metric(
        "altitude",
        "altitude",
        date
    )


def get_altitude_history(start_date, end_date):
    return _get_history(
        get_altitude,
        start_date,
        end_date
    )


def get_sedentary_period(date=None):
    return _get_raw_metric(
        "sedentary-period",
        "sedentaryPeriod",
        date
    )


def get_sedentary_period_history(start_date, end_date):
    return _get_history(
        get_sedentary_period,
        start_date,
        end_date
    )


def get_body_fat(date=None):
    return _get_raw_metric(
        "body-fat",
        "bodyFat",
        date
    )


def get_body_fat_history(start_date, end_date):
    return _get_history(
        get_body_fat,
        start_date,
        end_date
    )


def get_core_body_temperature(date=None):
    return _get_raw_metric(
        "core-body-temperature",
        "coreBodyTemperature",
        date
    )


def get_core_body_temperature_history(start_date, end_date):
    return _get_history(
        get_core_body_temperature,
        start_date,
        end_date
    )


# ============================================================
# EXERCISE
# ============================================================

def parse_exercise(item):
    exercise = item.get("exercise", {})
    metrics = exercise.get("metricsSummary", {})
    interval = exercise.get("interval", {})
    metadata = exercise.get("exerciseMetadata", {})
    zones = metrics.get("heartRateZoneDurations", {})
    source = item.get("dataSource", {})

    known_metrics = {
        "averageHeartRateBeatsPerMinute",
        "averagePaceSecondsPerMeter",
        "activeZoneMinutes",
        "caloriesKcal",
        "steps",
        "distanceMillimeters",
        "heartRateZoneDurations"
    }

    additional_metrics = {}

    for key, value in metrics.items():
        if key not in known_metrics:
            additional_metrics[key] = value

    pace = metrics.get(
        "averagePaceSecondsPerMeter"
    )

    pace_minutes_per_mile = None

    if pace is not None:
        try:
            pace_minutes_per_mile = round(
                float(pace) * 1609.344 / 60,
                2
            )
        except:
            pace_minutes_per_mile = None

    return {
        "exercise": exercise.get("displayName"),
        "type": exercise.get("exerciseType"),
        "start": interval.get("startTime"),
        "end": interval.get("endTime"),

        "duration_minutes":
            seconds_to_minutes(
                exercise.get("activeDuration")
            ),

        "calories":
            metrics.get("caloriesKcal"),

        "steps":
            metrics.get("steps"),

        "distance_miles":
            millimeters_to_miles(
                metrics.get("distanceMillimeters")
            ),

        "average_heart_rate_bpm":
            metrics.get(
                "averageHeartRateBeatsPerMinute"
            ),

        "active_zone_minutes":
            metrics.get("activeZoneMinutes"),

        "heart_rate_zones": {
            "light_minutes":
                seconds_to_minutes(
                    zones.get("lightTime")
                ),

            "moderate_minutes":
                seconds_to_minutes(
                    zones.get("moderateTime")
                ),

            "vigorous_minutes":
                seconds_to_minutes(
                    zones.get("vigorousTime")
                ),

            "peak_minutes":
                seconds_to_minutes(
                    zones.get("peakTime")
                )
        },

        "average_pace_seconds_per_meter":
            pace,

        "average_pace_minutes_per_mile":
            pace_minutes_per_mile,

        "has_gps":
            metadata.get("hasGps"),

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform"),

        "recording_method":
            source.get("recordingMethod"),

        "additional_metrics":
            additional_metrics
    }


def get_recent_exercises(limit=5):
    items = get_data_points(
        "exercise",
        limit
    )

    return [
        parse_exercise(item)
        for item in items
    ]


def get_exercise_history(
    start_date,
    end_date,
    exercise_type=None
):
    items = get_history_data_points(
        data_type="exercise",
        start_date=start_date,
        end_date=end_date,
        filter_field="exercise.interval.civil_start_time",
        chunk_days=90
    )

    results = [
        parse_exercise(item)
        for item in items
    ]

    unique_results = []
    seen = set()

    for item in results:
        key = (
            item.get("type"),
            item.get("start"),
            item.get("end"),
            item.get("duration_minutes"),
            item.get("distance_miles"),
            item.get("calories")
        )

        if key not in seen:
            seen.add(key)
            unique_results.append(item)

    results = unique_results

    if exercise_type:
        wanted = exercise_type.upper()

        results = [
            item
            for item in results
            if (
                str(item.get("type", "")).upper() == wanted
                or
                str(item.get("exercise", "")).upper() == wanted
            )
        ]

    return results


# ============================================================
# SLEEP
# ============================================================

def parse_sleep(item):
    sleep = item.get("sleep", {})
    interval = sleep.get("interval", {})
    metadata = sleep.get("metadata", {})
    summary = sleep.get("summary", {})
    source = item.get("dataSource", {})

    stage_totals = {}

    for stage in summary.get(
        "stagesSummary",
        []
    ):
        stage_type = stage.get("type")

        stage_totals[stage_type] = {
            "minutes": stage.get("minutes"),
            "count": stage.get("count")
        }

    stage_timeline = []

    for stage in sleep.get("stages", []):
        stage_timeline.append({
            "type": stage.get("type"),
            "start": stage.get("startTime"),
            "end": stage.get("endTime")
        })

    return {
        "start":
            interval.get("startTime"),

        "end":
            interval.get("endTime"),

        "sleep_type":
            sleep.get("type"),

        "minutes_in_sleep_period":
            summary.get(
                "minutesInSleepPeriod"
            ),

        "minutes_asleep":
            summary.get("minutesAsleep"),

        "minutes_awake":
            summary.get("minutesAwake"),

        "minutes_to_fall_asleep":
            summary.get(
                "minutesToFallAsleep"
            ),

        "minutes_after_wakeup":
            summary.get(
                "minutesAfterWakeUp"
            ),

        "stages_status":
            metadata.get("stagesStatus"),

        "main_sleep":
            metadata.get("mainSleep"),

        "sleep_stage_totals":
            stage_totals,

        "sleep_stage_timeline":
            stage_timeline,

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform")
    }


def get_recent_sleep(limit=5):
    items = get_data_points(
        "sleep",
        limit
    )

    return [
        parse_sleep(item)
        for item in items
    ]


def get_sleep_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="sleep",
        start_date=start_date,
        end_date=end_date,
        filter_field="sleep.interval.civil_end_time",
        chunk_days=90
    )

    return [
        parse_sleep(item)
        for item in items
    ]


# ============================================================
# RESTING HEART RATE
# ============================================================

def parse_resting_heart_rate(item):
    heart = item.get(
        "dailyRestingHeartRate",
        {}
    )

    metadata = heart.get(
        "dailyRestingHeartRateMetadata",
        {}
    )

    source = item.get("dataSource", {})

    return {
        "date":
            parse_date(
                heart.get("date")
            ),

        "resting_heart_rate_bpm":
            heart.get("beatsPerMinute"),

        "calculation_method":
            metadata.get(
                "calculationMethod"
            ),

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform")
    }


def get_resting_heart_rate(limit=10):
    items = get_data_points(
        "daily-resting-heart-rate",
        limit
    )

    return [
        parse_resting_heart_rate(item)
        for item in items
    ]


def get_resting_heart_rate_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="daily-resting-heart-rate",
        start_date=start_date,
        end_date=end_date,
        filter_field="daily_resting_heart_rate.date",
        chunk_days=90
    )

    return [
        parse_resting_heart_rate(item)
        for item in items
    ]


# ============================================================
# HRV
# ============================================================

def _classify_hrv_field(value):
    """
    Classify a single HRV-related raw field.
      - "missing": field is None
      - "raw_invalid_zero": numeric and equal to 0
      - "invalid_negative": numeric, finite, and less than 0
      - "invalid_nonnumeric": present but not convertible to float,
        or not finite
      - "ok": present, numeric, finite, and strictly positive
    """
    if value is None:
        return "missing"

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "invalid_nonnumeric"

    if not math.isfinite(numeric):
        return "invalid_nonnumeric"

    if numeric == 0.0:
        return "raw_invalid_zero"

    if numeric < 0.0:
        return "invalid_negative"

    return "ok"


def _hrv_quality(average_hrv, non_rem_hr, deep_rmssd):
    """
    Field-level HRV quality assessment. Adds analysis-layer metadata
    only; every raw field in parse_hrv()'s output is unchanged.

    average_hrv_ms is the primary field for the recovery-scoring
    "recovery_average_hrv" component: it must be numeric, finite,
    and strictly greater than zero to be usable there. Defects in
    the secondary fields (non_rem_heart_rate_bpm, deep_sleep_rmssd_ms)
    never block a valid positive average_hrv_ms from that use.
    """

    non_rem_status = _classify_hrv_field(non_rem_hr)
    deep_rmssd_status = _classify_hrv_field(deep_rmssd)
    primary_status = _classify_hrv_field(average_hrv)

    field_flags = []
    if non_rem_status != "ok":
        field_flags.append(f"non_rem_heart_rate_bpm_{non_rem_status}")
    if deep_rmssd_status != "ok":
        field_flags.append(f"deep_sleep_rmssd_ms_{deep_rmssd_status}")

    if primary_status != "ok":
        return {
            "quality_status": "invalid",
            "quality_flags": field_flags + [f"average_hrv_ms_{primary_status}"],
            "usable_for": []
        }

    if field_flags:
        return {
            "quality_status": "usable_with_caution",
            "quality_flags": field_flags,
            "usable_for": ["recovery_average_hrv", "display"]
        }

    return {
        "quality_status": "valid",
        "quality_flags": [],
        "usable_for": ["recovery_average_hrv", "display"]
    }


def parse_hrv(item):
    hrv = item.get(
        "dailyHeartRateVariability",
        {}
    )

    source = item.get("dataSource", {})

    non_rem_hr = hrv.get(
        "nonRemHeartRateBeatsPerMinute"
    )

    deep_rmssd = hrv.get(
        "deepSleepRootMeanSquareOfSuccessiveDifferencesMilliseconds"
    )

    average_hrv = hrv.get(
        "averageHeartRateVariabilityMilliseconds"
    )

    record = {
        "date":
            parse_date(
                hrv.get("date")
            ),

        "average_hrv_ms":
            average_hrv,

        "non_rem_heart_rate_bpm":
            non_rem_hr,

        "entropy":
            hrv.get("entropy"),

        "deep_sleep_rmssd_ms":
            deep_rmssd,

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform")
    }

    record.update(
        _hrv_quality(average_hrv, non_rem_hr, deep_rmssd)
    )

    return record


def get_hrv(limit=10):
    items = get_data_points(
        "daily-heart-rate-variability",
        limit
    )

    return [
        parse_hrv(item)
        for item in items
    ]


def get_hrv_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="daily-heart-rate-variability",
        start_date=start_date,
        end_date=end_date,
        filter_field="daily_heart_rate_variability.date",
        chunk_days=90
    )

    return [
        parse_hrv(item)
        for item in items
    ]


# ============================================================
# OXYGEN SATURATION
# ============================================================

def parse_oxygen_saturation(item):
    oxygen = item.get(
        "dailyOxygenSaturation",
        {}
    )

    source = item.get("dataSource", {})

    return {
        "date":
            parse_date(
                oxygen.get("date")
            ),

        "average_spo2_percent":
            oxygen.get(
                "averagePercentage"
            ),

        "minimum_spo2_percent":
            oxygen.get(
                "lowerBoundPercentage"
            ),

        "maximum_spo2_percent":
            oxygen.get(
                "upperBoundPercentage"
            ),

        "standard_deviation_percent":
            oxygen.get(
                "standardDeviationPercentage"
            ),

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform")
    }


def get_oxygen_saturation(limit=10):
    items = get_data_points(
        "daily-oxygen-saturation",
        limit
    )

    return [
        parse_oxygen_saturation(item)
        for item in items
    ]


def get_oxygen_saturation_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="daily-oxygen-saturation",
        start_date=start_date,
        end_date=end_date,
        filter_field="daily_oxygen_saturation.date",
        chunk_days=90
    )

    return [
        parse_oxygen_saturation(item)
        for item in items
    ]


# ============================================================
# RESPIRATORY RATE
# ============================================================

def parse_respiratory_rate(item):
    respiration = item.get(
        "dailyRespiratoryRate",
        {}
    )

    source = item.get("dataSource", {})

    return {
        "date":
            parse_date(
                respiration.get("date")
            ),

        "breaths_per_minute":
            respiration.get(
                "breathsPerMinute"
            ),

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform")
    }


def get_respiratory_rate(limit=10):
    items = get_data_points(
        "daily-respiratory-rate",
        limit
    )

    return [
        parse_respiratory_rate(item)
        for item in items
    ]


def get_respiratory_rate_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="daily-respiratory-rate",
        start_date=start_date,
        end_date=end_date,
        filter_field="daily_respiratory_rate.date",
        chunk_days=90
    )

    return [
        parse_respiratory_rate(item)
        for item in items
    ]


# ============================================================
# SLEEP TEMPERATURE
# ============================================================

def parse_sleep_temperature(item):
    temperature = item.get(
        "dailySleepTemperatureDerivations",
        {}
    )

    source = item.get("dataSource", {})

    nightly = temperature.get(
        "nightlyTemperatureCelsius"
    )

    baseline = temperature.get(
        "baselineTemperatureCelsius"
    )

    difference = None

    if (
        nightly is not None
        and baseline is not None
    ):
        difference = round(
            nightly - baseline,
            2
        )

    return {
        "date":
            parse_date(
                temperature.get("date")
            ),

        "nightly_temperature_celsius":
            nightly,

        "baseline_temperature_celsius":
            baseline,

        "difference_from_baseline_celsius":
            difference,

        "relative_30_day_stddev_celsius":
            temperature.get(
                "relativeNightlyStddev30dCelsius"
            ),

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform")
    }


def get_sleep_temperature(limit=10):
    items = get_data_points(
        "daily-sleep-temperature-derivations",
        limit
    )

    return [
        parse_sleep_temperature(item)
        for item in items
    ]


def get_sleep_temperature_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="daily-sleep-temperature-derivations",
        start_date=start_date,
        end_date=end_date,
        filter_field="daily_sleep_temperature_derivations.date",
        chunk_days=90
    )

    return [
        parse_sleep_temperature(item)
        for item in items
    ]


# ============================================================
# HEART RATE
# ============================================================

def parse_heart_rate(item):
    heart = item.get(
        "heartRate",
        {}
    )

    sample_time = heart.get(
        "sampleTime",
        {}
    )

    civil = sample_time.get(
        "civilTime",
        {}
    )

    source = item.get("dataSource", {})

    return {
        "physical_time":
            sample_time.get(
                "physicalTime"
            ),

        "local_date":
            parse_date(
                civil.get("date")
            ),

        "local_time":
            civil.get("time"),

        "heart_rate_bpm":
            heart.get(
                "beatsPerMinute"
            ),

        "device":
            source.get("device", {})
            .get("displayName"),

        "platform":
            source.get("platform"),

        "recording_method":
            source.get(
                "recordingMethod"
            )
    }


def get_heart_rate(limit=20):
    items = get_data_points(
        "heart-rate",
        limit
    )

    return [
        parse_heart_rate(item)
        for item in items
    ]


def get_heart_rate_history(
    start_date,
    end_date,
    max_records=2000
):
    items = get_history_data_points(
        data_type="heart-rate",
        start_date=start_date,
        end_date=end_date,
        filter_field="heart_rate.sample_time.civil_time",
        chunk_days=14,
        max_records=max_records
    )

    return [
        parse_heart_rate(item)
        for item in items
    ]


# ============================================================
# HEART RATE ZONES
# ============================================================

def parse_heart_rate_zones(item):
    zone_data = item.get(
        "dailyHeartRateZones",
        {}
    )

    zones = []

    for zone in zone_data.get(
        "heartRateZones",
        []
    ):
        zones.append({
            "type":
                zone.get(
                    "heartRateZoneType"
                ),

            "min_bpm":
                zone.get(
                    "minBeatsPerMinute"
                ),

            "max_bpm":
                zone.get(
                    "maxBeatsPerMinute"
                )
        })

    return {
        "date":
            parse_date(
                zone_data.get("date")
            ),

        "zones":
            zones
    }


def get_heart_rate_zones(limit=5):
    items = get_data_points(
        "daily-heart-rate-zones",
        limit
    )

    return [
        parse_heart_rate_zones(item)
        for item in items
    ]


def get_heart_rate_zones_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="daily-heart-rate-zones",
        start_date=start_date,
        end_date=end_date,
        filter_field="daily_heart_rate_zones.date",
        chunk_days=90
    )

    return [
        parse_heart_rate_zones(item)
        for item in items
    ]


# ============================================================
# WEIGHT
# ============================================================

def parse_weight(item):
    weight = item.get(
        "weight",
        {}
    )

    sample_time = weight.get(
        "sampleTime",
        {}
    )

    civil = sample_time.get(
        "civilTime",
        {}
    )

    source = item.get("dataSource", {})

    grams = weight.get(
        "weightGrams"
    )

    return {
        "physical_time":
            sample_time.get(
                "physicalTime"
            ),

        "date":
            parse_date(
                civil.get("date")
            ),

        "weight_grams":
            grams,

        "weight_pounds":
            grams_to_pounds(
                grams
            ),

        "platform":
            source.get(
                "platform"
            ),

        "recording_method":
            source.get(
                "recordingMethod"
            )
    }


def get_weight(limit=10):
    items = get_data_points(
        "weight",
        limit
    )

    return [
        parse_weight(item)
        for item in items
    ]


def get_weight_history(
    start_date,
    end_date
):
    items = get_history_data_points(
        data_type="weight",
        start_date=start_date,
        end_date=end_date,
        filter_field="weight.sample_time.civil_time",
        chunk_days=90
    )

    return [
        parse_weight(item)
        for item in items
    ]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\nHISTORICAL TEST")
    print("==============================")

    print("\nExercise history:")
    print(
        get_exercise_history(
            "2026-08-01",
            "2026-08-15"
        )
    )

    print("\nHRV history:")
    print(
        get_hrv_history(
            "2026-08-01",
            "2026-08-15"
        )
    )

    print("\nResting HR history:")
    print(
        get_resting_heart_rate_history(
            "2026-08-01",
            "2026-08-15"
        )
    )
