"""CLI application definitions."""

from __future__ import annotations

from pathlib import Path

import typer

from envsync.cli.discover import discover_command
from envsync.core.drift_detector import DriftReport, detect_drift
from envsync.models.types import ParsedVariable, ParsedVariables
from envsync.parsers.env_parser import EnvParseError, parse_env_file
from envsync.parsers.k8s_parser import K8sParseError, parse_k8s_yaml_file
from envsync.utils.reporting import format_json_report, format_terminal_report

app = typer.Typer(help="Detect configuration drift across environments.")
app.command("discover")(discover_command)


@app.callback()
def app_callback() -> None:
	"""Top-level CLI callback for EnvSync."""


@app.command("compare")
def compare_command(
	env_files: list[Path] = typer.Option(
		..., "--env", help="Environment file path (.env, .yml, .yaml). Repeat for each env."
	),
	json_output: bool = typer.Option(
		False,
		"--json",
		help="Print machine-readable JSON report instead of terminal text.",
	),
	fail_on_drift: bool = typer.Option(
		False,
		"--fail-on-drift",
		help="Exit with code 2 when any drift is detected (CI-friendly).",
	),
) -> None:
	"""Compare multiple environment files and print drift findings."""
	if len(env_files) < 2:
		raise typer.BadParameter("Provide at least two --env inputs for comparison")

	parsed_inputs: list[tuple[str, ParsedVariables]] = []
	for index, env_file in enumerate(env_files, start=1):
		env_name = _derive_environment_name(env_file=env_file, index=index)
		parsed = _parse_environment_file(env_file)
		parsed_inputs.append((env_name, parsed))

	environments = _ensure_unique_environment_names(parsed_inputs)
	report = detect_drift(environments)
	has_drift = _has_drift(report)
	if json_output:
		typer.echo(format_json_report(report))
		if fail_on_drift and has_drift:
			raise typer.Exit(code=2)
		return

	typer.echo(format_terminal_report(report))
	if fail_on_drift and has_drift:
		raise typer.Exit(code=2)


def _parse_environment_file(file_path: Path) -> ParsedVariables:
	"""Parse one input file into normalized parsed variables."""
	extension = file_path.suffix.lower()
	try:
		if extension in {".yaml", ".yml"}:
			return parse_k8s_yaml_file(file_path)
		if extension == ".env":
			env_values = parse_env_file(file_path)
			return {
				key: ParsedVariable(value=value, is_secret=False)
				for key, value in env_values.items()
			}
		raise typer.BadParameter(
			f"Unsupported file type: {file_path}. Use .env, .yaml, or .yml"
		)
	except (FileNotFoundError, IsADirectoryError, EnvParseError, K8sParseError) as exc:
		raise typer.BadParameter(str(exc)) from exc


def _derive_environment_name(env_file: Path, index: int) -> str:
	"""Build a readable environment label from an input file path."""
	if env_file.suffix.lower() == ".env":
		candidate = env_file.stem
	else:
		candidate = env_file.name.rsplit(".", 1)[0]

	candidate = candidate.strip()
	return candidate if candidate else f"env{index}"


def _ensure_unique_environment_names(
	parsed_inputs: list[tuple[str, ParsedVariables]],
) -> dict[str, ParsedVariables]:
	"""Ensure environment names are unique by appending numeric suffixes."""
	result: dict[str, ParsedVariables] = {}
	seen_counts: dict[str, int] = {}

	for name, values in parsed_inputs:
		count = seen_counts.get(name, 0)
		seen_counts[name] = count + 1

		resolved_name = name if count == 0 else f"{name}_{count + 1}"
		result[resolved_name] = values

	return result


def _has_drift(report: DriftReport) -> bool:
	"""Return True when any drift category is non-empty."""
	missing = report.missing_by_environment
	extra = report.extra_by_environment
	different = report.different_values
	if different:
		return True
	if any(missing.values()):
		return True
	if any(extra.values()):
		return True
	return False
