import importlib.util
import os
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path


def _install_google_stubs():
    requests_module = types.ModuleType("requests")

    modules = {
        "requests": requests_module,
        "google_auth_oauthlib": types.ModuleType("google_auth_oauthlib"),
        "google_auth_oauthlib.flow": types.ModuleType(
            "google_auth_oauthlib.flow"
        ),
        "google": types.ModuleType("google"),
        "google.oauth2": types.ModuleType("google.oauth2"),
        "google.oauth2.credentials": types.ModuleType(
            "google.oauth2.credentials"
        ),
        "google.auth": types.ModuleType("google.auth"),
        "google.auth.transport": types.ModuleType(
            "google.auth.transport"
        ),
        "google.auth.transport.requests": types.ModuleType(
            "google.auth.transport.requests"
        ),
    }

    modules["google_auth_oauthlib.flow"].Flow = object
    modules["google.oauth2.credentials"].Credentials = object
    modules["google.auth.transport.requests"].Request = object

    sys.modules.update(modules)


_install_google_stubs()

MODULE_PATH = Path(__file__).with_name("fitbit_test.py")
SPEC = importlib.util.spec_from_file_location(
    "fitbit_test_under_test",
    MODULE_PATH
)
FITBIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FITBIT)


def make_sleep_item(
    *,
    start,
    end,
    duration,
    awake,
    stage_awake,
    main_sleep,
    sleep_type="STAGES",
    stages_status="SUCCEEDED",
):
    stages_summary = []

    if stage_awake is not None:
        stages_summary.append({
            "type": "AWAKE",
            "minutes": stage_awake,
            "count": 1,
        })

    return {
        "sleep": {
            "type": sleep_type,
            "interval": {
                "startTime": start,
                "endTime": end,
            },
            "metadata": {
                "mainSleep": main_sleep,
                "stagesStatus": stages_status,
            },
            "summary": {
                "minutesInSleepPeriod": duration,
                "minutesAsleep": (
                    duration - awake
                    if isinstance(duration, (int, float))
                    and isinstance(awake, (int, float))
                    else None
                ),
                "minutesAwake": awake,
                "stagesSummary": stages_summary,
            },
            "stages": [],
        },
        "dataSource": {
            "device": {"displayName": "Fitbit Charge 5"},
            "platform": "FITBIT",
        },
    }


class SleepQualityTests(unittest.TestCase):
    def test_timezone_conversion_and_wake_date(self):
        item = make_sleep_item(
            start="2026-08-17T22:23:00Z",
            end="2026-08-18T02:15:00Z",
            duration=232,
            awake=23,
            stage_awake=23,
            main_sleep=True,
        )

        record = FITBIT.parse_sleep(item)

        self.assertEqual(record["local_wake_date"], "2026-08-17")
        self.assertTrue(record["local_end"].endswith("-07:00"))
        self.assertEqual(record["sleep_role"], "main_sleep")

    def test_known_naps_and_nocturnal_counterexample(self):
        cases = [
            (
                "2026-08-17T17:11:00Z",
                "2026-08-17T20:53:00Z",
                222,
                "nap",
            ),
            (
                "2026-06-02T14:25:00Z",
                "2026-06-02T16:24:00Z",
                119,
                "nap",
            ),
            (
                "2026-08-18T01:00:00-07:00",
                "2026-08-18T07:00:00-07:00",
                360,
                "fragment",
            ),
        ]

        for start, end, duration, expected_role in cases:
            with self.subTest(start=start):
                item = make_sleep_item(
                    start=start,
                    end=end,
                    duration=duration,
                    awake=10,
                    stage_awake=10,
                    main_sleep=None,
                )
                record = FITBIT.parse_sleep(item)
                self.assertEqual(record["sleep_role"], expected_role)

    def test_one_minute_rounding_difference_is_valid(self):
        item = make_sleep_item(
            start="2026-08-20T11:55:00Z",
            end="2026-08-20T14:25:00Z",
            duration=150,
            awake=4,
            stage_awake=3,
            main_sleep=True,
        )

        record = FITBIT.parse_sleep(item)

        self.assertEqual(record["sleep_measurement_quality"], "stages")
        self.assertEqual(record["quality_status"], "valid")
        self.assertIn("recovery_sleep_stages", record["usable_for"])

    def test_large_awake_mismatch_withholds_stage_scoring(self):
        item = make_sleep_item(
            start="2026-08-01T11:58:00Z",
            end="2026-08-01T15:11:00Z",
            duration=193,
            awake=0,
            stage_awake=28,
            main_sleep=True,
            sleep_type="CLASSIC",
            stages_status=None,
        )

        record = FITBIT.parse_sleep(item)

        self.assertEqual(
            record["sleep_measurement_quality"],
            "contradictory",
        )
        self.assertEqual(
            record["quality_status"],
            "usable_with_caution",
        )
        self.assertIn("awake_minutes_mismatch", record["quality_flags"])
        self.assertIn("recovery_sleep_duration", record["usable_for"])
        self.assertNotIn(
            "recovery_sleep_stages",
            record["usable_for"],
        )

    def test_rejected_stages_keep_duration_and_timing(self):
        item = make_sleep_item(
            start="2026-08-18T11:23:00Z",
            end="2026-08-18T13:23:00Z",
            duration=120,
            awake=0,
            stage_awake=None,
            main_sleep=True,
            sleep_type="CLASSIC",
            stages_status="REJECTED_COVERAGE",
        )

        record = FITBIT.parse_sleep(item)

        self.assertEqual(record["sleep_measurement_quality"], "rejected")
        self.assertEqual(
            record["quality_status"],
            "usable_with_caution",
        )
        self.assertIn("recovery_sleep_duration", record["usable_for"])
        self.assertIn("recovery_sleep_timing", record["usable_for"])
        self.assertNotIn(
            "recovery_sleep_continuity",
            record["usable_for"],
        )

    def test_high_awake_ratio_is_caution_not_invalidation(self):
        item = make_sleep_item(
            start="2026-06-01T19:37:00Z",
            end="2026-06-02T12:03:00Z",
            duration=986,
            awake=352,
            stage_awake=352,
            main_sleep=True,
        )

        record = FITBIT.parse_sleep(item)

        self.assertEqual(
            record["quality_status"],
            "usable_with_caution",
        )
        self.assertIn(
            "unusual_high_awake_ratio",
            record["quality_flags"],
        )
        self.assertIn("recovery_sleep_duration", record["usable_for"])
        self.assertIn("recovery_sleep_stages", record["usable_for"])

    def test_nap_uses_nap_components_only(self):
        item = make_sleep_item(
            start="2026-06-02T14:25:00Z",
            end="2026-06-02T16:24:00Z",
            duration=119,
            awake=31,
            stage_awake=30,
            main_sleep=None,
        )

        record = FITBIT.parse_sleep(item)

        self.assertIn("recovery_nap_duration", record["usable_for"])
        self.assertIn("recovery_nap_timing", record["usable_for"])
        self.assertNotIn(
            "recovery_sleep_duration",
            record["usable_for"],
        )

    def test_bad_timestamp_does_not_crash_or_erase_duration(self):
        item = make_sleep_item(
            start="not-a-timestamp",
            end="2026-08-21 07:28:00",
            duration=343,
            awake=25,
            stage_awake=25,
            main_sleep=True,
        )

        record = FITBIT.parse_sleep(item)

        self.assertIsNone(record["local_wake_date"])
        self.assertIn(
            "start_timestamp_malformed",
            record["quality_flags"],
        )
        self.assertIn(
            "end_timestamp_timezone_missing",
            record["quality_flags"],
        )
        self.assertIn("recovery_sleep_duration", record["usable_for"])
        self.assertNotIn("recovery_sleep_timing", record["usable_for"])
        self.assertEqual(
            record["quality_status"],
            "usable_with_caution",
        )

    def test_malformed_stage_totals_fail_safely(self):
        quality, flags = FITBIT._classify_measurement_quality(
            "STAGES",
            "SUCCEEDED",
            5,
            None,
        )

        self.assertEqual(quality, "stages")
        self.assertIn("awake_minutes_partial_comparison", flags)

    def test_explicit_invalid_timezone_fails(self):
        old_value = os.environ.get("FITBIT_LOCAL_TIMEZONE")

        try:
            os.environ["FITBIT_LOCAL_TIMEZONE"] = "Not/A_Timezone"
            with self.assertRaises(RuntimeError):
                FITBIT._load_local_timezone()
        finally:
            if old_value is None:
                os.environ.pop("FITBIT_LOCAL_TIMEZONE", None)
            else:
                os.environ["FITBIT_LOCAL_TIMEZONE"] = old_value


if __name__ == "__main__":
    unittest.main()
