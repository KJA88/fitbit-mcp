from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.server.transport_security import TransportSecuritySettings

from fitbit_test import (
    get_recent_exercises,
    get_recent_sleep,
    get_resting_heart_rate,
    get_hrv,
    get_oxygen_saturation,
    get_respiratory_rate,
    get_sleep_temperature,
    get_heart_rate,
    get_heart_rate_zones,
    get_weight,

    get_exercise_history,
    get_sleep_history,
    get_resting_heart_rate_history,
    get_hrv_history,
    get_oxygen_saturation_history,
    get_respiratory_rate_history,
    get_sleep_temperature_history,
    get_heart_rate_history,
    get_heart_rate_zones_history,
    get_weight_history,
get_activity_level,
get_activity_level_history,
get_steps,
get_steps_history,
get_distance,
get_distance_history,
get_active_zone_minutes,
get_active_zone_minutes_history,
get_total_calories,
get_total_calories_history,
get_active_energy_burned,
get_active_energy_burned_history,
get_floors,
get_floors_history,
get_active_minutes,
get_active_minutes_history,
get_time_in_heart_rate_zone,
get_time_in_heart_rate_zone_history
)

from fitbit_analysis import (
    analyze_metric_trend,
    compare_metric_periods,
    analyze_exercise_progress,
    get_health_summary,
get_daily_health_summary,
analyze_fitbit_data_quality
)


mcp = MCPServer("Fitbit Health MCP")


# ============================================================
# RECENT DATA
# ============================================================

@mcp.tool()
def get_fitbit_exercises(limit: int = 5):
    return get_recent_exercises(limit)


@mcp.tool()
def get_fitbit_sleep(limit: int = 5):
    return get_recent_sleep(limit)


@mcp.tool()
def get_fitbit_resting_heart_rate(limit: int = 10):
    return get_resting_heart_rate(limit)


@mcp.tool()
def get_fitbit_hrv(limit: int = 10):
    return get_hrv(limit)


@mcp.tool()
def get_fitbit_oxygen_saturation(limit: int = 10):
    return get_oxygen_saturation(limit)


@mcp.tool()
def get_fitbit_respiratory_rate(limit: int = 10):
    return get_respiratory_rate(limit)


@mcp.tool()
def get_fitbit_sleep_temperature(limit: int = 10):
    return get_sleep_temperature(limit)


@mcp.tool()
def get_fitbit_heart_rate(limit: int = 20):
    return get_heart_rate(limit)


@mcp.tool()
def get_fitbit_heart_rate_zones(limit: int = 5):
    return get_heart_rate_zones(limit)


@mcp.tool()
def get_fitbit_weight(limit: int = 10):
    return get_weight(limit)


# ============================================================
# HISTORICAL DATA
# ============================================================

@mcp.tool()
def get_fitbit_exercise_history(
    start_date: str,
    end_date: str,
    exercise_type: str = None
):
    return get_exercise_history(
        start_date,
        end_date,
        exercise_type
    )


@mcp.tool()
def get_fitbit_sleep_history(
    start_date: str,
    end_date: str
):
    return get_sleep_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_resting_heart_rate_history(
    start_date: str,
    end_date: str
):
    return get_resting_heart_rate_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_hrv_history(
    start_date: str,
    end_date: str
):
    return get_hrv_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_oxygen_saturation_history(
    start_date: str,
    end_date: str
):
    return get_oxygen_saturation_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_respiratory_rate_history(
    start_date: str,
    end_date: str
):
    return get_respiratory_rate_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_sleep_temperature_history(
    start_date: str,
    end_date: str
):
    return get_sleep_temperature_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_heart_rate_history(
    start_date: str,
    end_date: str,
    max_records: int = 2000
):
    return get_heart_rate_history(
        start_date,
        end_date,
        max_records
    )


@mcp.tool()
def get_fitbit_heart_rate_zones_history(
    start_date: str,
    end_date: str
):
    return get_heart_rate_zones_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_weight_history(
    start_date: str,
    end_date: str
):
    return get_weight_history(
        start_date,
        end_date
    )


# ============================================================


# ============================================================
# STEPS TOOLS
# ============================================================

@mcp.tool()
def get_fitbit_steps(date: str = None):
    """
    Get Fitbit/Google Health daily step total.
    """
    return get_steps(date)


@mcp.tool()
def get_fitbit_steps_history(
    start_date: str,
    end_date: str
):
    """
    Get Fitbit/Google Health step history.
    """
    return get_steps_history(
        start_date,
        end_date
    )



# ============================================================
# DAILY ACTIVITY MCP TOOLS
# ============================================================

@mcp.tool()
def get_fitbit_distance(date: str = None):
    return get_distance(date)


@mcp.tool()
def get_fitbit_distance_history(
    start_date: str,
    end_date: str
):
    return get_distance_history(start_date, end_date)


@mcp.tool()
def get_fitbit_active_zone_minutes(date: str = None):
    return get_active_zone_minutes(date)


@mcp.tool()
def get_fitbit_active_zone_minutes_history(
    start_date: str,
    end_date: str
):
    return get_active_zone_minutes_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_total_calories(date: str = None):
    return get_total_calories(date)


@mcp.tool()
def get_fitbit_total_calories_history(
    start_date: str,
    end_date: str
):
    return get_total_calories_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_active_energy_burned(
    date: str = None
):
    return get_active_energy_burned(date)


@mcp.tool()
def get_fitbit_active_energy_burned_history(
    start_date: str,
    end_date: str
):
    return get_active_energy_burned_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_floors(date: str = None):
    return get_floors(date)


@mcp.tool()
def get_fitbit_floors_history(
    start_date: str,
    end_date: str
):
    return get_floors_history(
        start_date,
        end_date
    )




# ============================================================
# ACTIVE MINUTES / HEART RATE ZONE TIME MCP TOOLS
# ============================================================

@mcp.tool()
def get_fitbit_active_minutes(date: str = None):
    return get_active_minutes(date)


@mcp.tool()
def get_fitbit_active_minutes_history(
    start_date: str,
    end_date: str
):
    return get_active_minutes_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_time_in_heart_rate_zone(
    date: str = None
):
    return get_time_in_heart_rate_zone(date)


@mcp.tool()
def get_fitbit_time_in_heart_rate_zone_history(
    start_date: str,
    end_date: str
):
    return get_time_in_heart_rate_zone_history(
        start_date,
        end_date
    )



# ============================================================
# ACTIVITY LEVEL MCP TOOLS
# ============================================================

@mcp.tool()
def get_fitbit_activity_level(limit: int = 20):
    return get_activity_level(limit)


@mcp.tool()
def get_fitbit_activity_level_history(
    start_date: str,
    end_date: str
):
    return get_activity_level_history(
        start_date,
        end_date
    )


# ============================================================
# ADDITIONAL HEALTH METRIC MCP TOOLS
# ============================================================

@mcp.tool()
def get_fitbit_vo2_max():
    return get_vo2_max()


@mcp.tool()
def get_fitbit_vo2_max_history(
    start_date: str,
    end_date: str
):
    return get_vo2_max_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_height():
    return get_height()


@mcp.tool()
def get_fitbit_height_history(
    start_date: str,
    end_date: str
):
    return get_height_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_blood_glucose():
    return get_blood_glucose()


@mcp.tool()
def get_fitbit_blood_glucose_history(
    start_date: str,
    end_date: str
):
    return get_blood_glucose_history(
        start_date,
        end_date
    )



# ============================================================
# BATCH 3 HEALTH METRIC MCP TOOLS
# ============================================================

@mcp.tool()
def get_fitbit_daily_vo2_max():
    return get_daily_vo2_max()


@mcp.tool()
def get_fitbit_daily_vo2_max_history(
    start_date: str,
    end_date: str
):
    return get_daily_vo2_max_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_run_vo2_max():
    return get_run_vo2_max()


@mcp.tool()
def get_fitbit_run_vo2_max_history(
    start_date: str,
    end_date: str
):
    return get_run_vo2_max_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_altitude():
    return get_altitude()


@mcp.tool()
def get_fitbit_altitude_history(
    start_date: str,
    end_date: str
):
    return get_altitude_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_sedentary_period():
    return get_sedentary_period()


@mcp.tool()
def get_fitbit_sedentary_period_history(
    start_date: str,
    end_date: str
):
    return get_sedentary_period_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_body_fat():
    return get_body_fat()


@mcp.tool()
def get_fitbit_body_fat_history(
    start_date: str,
    end_date: str
):
    return get_body_fat_history(
        start_date,
        end_date
    )


@mcp.tool()
def get_fitbit_core_body_temperature():
    return get_core_body_temperature()


@mcp.tool()
def get_fitbit_core_body_temperature_history(
    start_date: str,
    end_date: str
):
    return get_core_body_temperature_history(
    start_date,
    end_date
    )


# ANALYSIS TOOLS
# ============================================================

@mcp.tool()
def analyze_fitbit_metric_trend(
    metric: str,
    start_date: str,
    end_date: str
):
    """
    Analyze a Fitbit metric over time.

    Supported metrics:
    resting_heart_rate
    hrv
    spo2
    respiratory_rate
    sleep_temperature
    weight
    """
    return analyze_metric_trend(
        metric,
        start_date,
        end_date
    )


@mcp.tool()
def compare_fitbit_periods(
    metric: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str
):
    """
    Compare the average value of a Fitbit metric
    between two periods.
    """
    return compare_metric_periods(
        metric,
        period1_start,
        period1_end,
        period2_start,
        period2_end
    )


@mcp.tool()
def analyze_fitbit_exercise_progress(
    start_date: str,
    end_date: str,
    exercise_type: str = None
):
    """
    Analyze exercise progress across a date range.

    exercise_type is optional.

    Examples:
    WALKING
    TREADMILL
    WEIGHTS
    ROWING
    YOGA
    """
    return analyze_exercise_progress(
        start_date,
        end_date,
        exercise_type
    )



@mcp.tool()
def get_fitbit_daily_summary(date: str = None):
    """
    Create a single day Fitbit health summary.
    """
    return get_daily_health_summary(date)


@mcp.tool()
def get_fitbit_health_summary(
    start_date: str,
    end_date: str
):
    """
    Create a combined Fitbit health summary.

    Includes exercise, sleep, resting HR,
    HRV, SpO2, respiratory rate,
    sleep temperature, and weight.
    """
    return get_health_summary(
        start_date,
        end_date
    )



@mcp.tool()
def analyze_fitbit_data_quality():
    """
    Assess Fitbit data continuity and baseline reliability.
    """
    return analyze_fitbit_data_quality()


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8010,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[
                "127.0.0.1:*",
                "localhost:*",
                "fitbit.syzygylab.net",
                "fitbit.syzygylab.net:*",
            ],
            allowed_origins=[
                "http://127.0.0.1:*",
                "http://localhost:*",
                "https://fitbit.syzygylab.net",
            ],
        ),
    )