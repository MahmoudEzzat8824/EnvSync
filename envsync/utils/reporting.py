"""Report formatting helpers for terminal and JSON output."""

from __future__ import annotations

import json

from envsync.core.drift_detector import DriftReport
from envsync.utils.constants import REPO_URL


def format_terminal_report(report: DriftReport) -> str:
	"""Render a human-readable multi-section drift report."""
	has_drift = _has_drift(report)
	lines: list[str] = []
	lines.append("EnvSync Drift Report")
	lines.append("=" * 20)
	lines.append(f"Environments: {', '.join(report.environment_names)}")
	lines.append(f"Total keys discovered: {len(report.all_keys)}")
	lines.append("")

	lines.append("Missing Keys")
	lines.append("-" * 12)
	for env_name in report.environment_names:
		keys = report.missing_by_environment.get(env_name, [])
		lines.append(f"{env_name}: {_format_key_list(keys)}")
	lines.append("")

	lines.append("Extra Keys")
	lines.append("-" * 10)
	for env_name in report.environment_names:
		keys = report.extra_by_environment.get(env_name, [])
		lines.append(f"{env_name}: {_format_key_list(keys)}")
	lines.append("")

	lines.append("Different Values")
	lines.append("-" * 16)
	if report.different_values:
		for key in report.different_values:
			suffix = " [secret]" if key in report.secret_keys else ""
			lines.append(f"- {key}{suffix}")
	else:
		lines.append("None")
	lines.append("")

	lines.append("Consistent Values")
	lines.append("-" * 17)
	if report.consistent_values:
		for key in report.consistent_values:
			suffix = " [secret]" if key in report.secret_keys else ""
			lines.append(f"- {key}{suffix}")
	else:
		lines.append("None")

	if has_drift:
		lines.append("")
		lines.append("WARNING: Drift detected")
		lines.append("")
		lines.append("EnvSync tip:")
		lines.append(
			"Share this report with your team or integrate EnvSync into CI to prevent this automatically."
		)
		lines.append(f"Star the repo: {REPO_URL}")

	return "\n".join(lines)


def format_json_report(report: DriftReport) -> str:
	"""Render a machine-readable JSON report."""
	payload = {
		"environments": report.environment_names,
		"summary": {
			"total_keys": len(report.all_keys),
			"different_count": len(report.different_values),
			"consistent_count": len(report.consistent_values),
			"drift_detected": _has_drift(report),
		},
		"all_keys": report.all_keys,
		"missing": report.missing_by_environment,
		"extra": report.extra_by_environment,
		"different_values": report.different_values,
		"consistent_values": report.consistent_values,
		"secret_keys": report.secret_keys,
	}
	return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)


def _format_key_list(keys: list[str]) -> str:
	"""Format key lists compactly for per-environment report sections."""
	if not keys:
		return "None"
	return ", ".join(keys)


def _has_drift(report: DriftReport) -> bool:
	"""Return True when any drift category is non-empty."""
	if report.different_values:
		return True
	if any(report.missing_by_environment.values()):
		return True
	if any(report.extra_by_environment.values()):
		return True
	return False
