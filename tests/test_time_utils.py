from datetime import date, datetime, timezone

import pytest

from habit_tracker.time_utils import (
    day_key,
    iso_week_key,
    parse_iso_week_key,
    iso_week_monday,
    now_utc_iso,
    parse_iso,
    to_local_date,
    local_tzinfo,
    local_datetime_to_utc_iso,
)


def test_now_utc_iso_has_utc_offset_and_no_microseconds():
    """now_utc_iso() should return a clean ISO timestamp in UTC (no microseconds)."""
    timestamp = now_utc_iso()

    # The function returns an ISO string with an explicit UTC offset.
    assert timestamp.endswith("+00:00")

    parsed = parse_iso(timestamp)
    assert parsed.tzinfo is not None
    assert parsed.microsecond == 0


@pytest.mark.parametrize(
    "iso_timestamp, expected_day_key",
    [
        ("2026-01-05T12:00:00", "2026-01-05"),
        ("2020-12-31T23:59:59", "2020-12-31"),
        ("2019-01-01T00:00:00", "2019-01-01"),
    ],
)
def test_day_key_uses_local_day_for_naive_timestamps(iso_timestamp, expected_day_key):
    """Naive timestamps are treated as local time and bucketed by local calendar day."""
    assert day_key(iso_timestamp) == expected_day_key


@pytest.mark.parametrize(
    "iso_timestamp, expected_key",
    [
        # ISO week boundaries are easy to get wrong, so we test a few famous edge cases.
        ("2021-01-01T10:00:00", "2020-W53"),  # Jan 1, 2021 belongs to ISO week 53 of 2020
        ("2018-12-31T10:00:00", "2019-W01"),  # Dec 31, 2018 belongs to ISO week 1 of 2019
        ("2022-01-01T10:00:00", "2021-W52"),  # Jan 1, 2022 belongs to ISO week 52 of 2021
        ("2020-01-01T10:00:00", "2020-W01"),  # normal case
    ],
)
def test_iso_week_key_handles_year_boundaries_correctly(iso_timestamp, expected_key):
    """iso_week_key() should follow ISO week rules across year boundaries."""
    assert iso_week_key(iso_timestamp) == expected_key


def test_parse_iso_week_key_splits_year_and_week_number():
    """parse_iso_week_key should turn 'YYYY-W##' into (YYYY, ##)."""
    assert parse_iso_week_key("2019-W01") == (2019, 1)
    assert parse_iso_week_key("2020-W53") == (2020, 53)


@pytest.mark.parametrize(
    "iso_year, iso_week, expected_monday",
    [
        (2019, 1, date(2018, 12, 31)),  # ISO week 1 of 2019 starts on 2018-12-31
        (2020, 1, date(2019, 12, 30)),
        (2020, 53, date(2020, 12, 28)),
    ],
)
def test_iso_week_monday_returns_expected_start_date(iso_year, iso_week, expected_monday):
    """iso_week_monday should return the Monday date for a given ISO week."""
    assert iso_week_monday(iso_year, iso_week) == expected_monday


def test_to_local_date_keeps_date_when_datetime_is_already_local_timezone():
    """If datetime already has local tzinfo, to_local_date should preserve its calendar date."""
    tz = local_tzinfo()
    local_dt = datetime(2026, 1, 5, 23, 59, 0, tzinfo=tz)

    assert to_local_date(local_dt) == date(2026, 1, 5)


def test_local_datetime_to_utc_iso_roundtrip_preserves_local_date():
    """A local date converted to UTC ISO should still map back to the same local date.

    We pick midday on purpose to avoid edge cases around midnight and DST-like boundaries.
    """
    original_local_date = date(2026, 1, 5)

    utc_iso = local_datetime_to_utc_iso(original_local_date, 12, 0)
    utc_dt = parse_iso(utc_iso)

    assert utc_dt.tzinfo is not None
    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt.microsecond == 0

    assert to_local_date(utc_dt) == original_local_date