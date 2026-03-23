"""Unit tests for drift detection logic."""

from __future__ import annotations

from envsync.core.drift_detector import detect_drift
from envsync.models.types import ParsedVariable


def test_detect_drift_reports_missing_extra_and_differences() -> None:
    """It reports missing/extra keys and detects value drift."""
    environments = {
        "dev": {
            "API_URL": ParsedVariable("https://dev.example.com", is_secret=False),
            "JWT_SECRET": ParsedVariable("token-1", is_secret=True),
            "ONLY_DEV": ParsedVariable("x", is_secret=False),
        },
        "staging": {
            "API_URL": ParsedVariable("https://staging.example.com", is_secret=False),
            "JWT_SECRET": ParsedVariable("token-1", is_secret=True),
            "ONLY_STAGING": ParsedVariable("y", is_secret=False),
        },
        "prod": {
            "API_URL": ParsedVariable("https://staging.example.com", is_secret=False),
            "JWT_SECRET": ParsedVariable("token-2", is_secret=True),
        },
    }

    report = detect_drift(environments)

    assert report.missing_by_environment["dev"] == ["ONLY_STAGING"]
    assert report.missing_by_environment["staging"] == ["ONLY_DEV"]
    assert report.missing_by_environment["prod"] == ["ONLY_DEV", "ONLY_STAGING"]

    assert report.extra_by_environment["dev"] == ["ONLY_DEV"]
    assert report.extra_by_environment["staging"] == ["ONLY_STAGING"]
    assert report.extra_by_environment["prod"] == []

    assert report.different_values == ["API_URL", "JWT_SECRET"]
    assert report.consistent_values == []
    assert report.secret_keys == ["JWT_SECRET"]


def test_detect_drift_marks_secret_consistent_when_values_match() -> None:
    """It marks a secret key as consistent when all secret values are equal."""
    environments = {
        "dev": {"JWT_SECRET": ParsedVariable("same", is_secret=True)},
        "staging": {"JWT_SECRET": ParsedVariable("same", is_secret=True)},
        "prod": {"JWT_SECRET": ParsedVariable("same", is_secret=True)},
    }

    report = detect_drift(environments)

    assert report.different_values == []
    assert report.consistent_values == ["JWT_SECRET"]
    assert report.secret_keys == ["JWT_SECRET"]
