"""Workspace discovery command for environment variable usage."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import typer
from rich.console import Console
from rich.table import Table

IGNORED_DIRECTORIES = {
	".git",
	".venv",
	"__pycache__",
	"build",
	"dist",
	"node_modules",
	"venv",
}

_VAR_NAME_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"

PATTERNS: tuple[re.Pattern[str], ...] = (
	re.compile(rf"os\.getenv\(\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\)"),
	re.compile(rf"os\.environ\.get\(\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\)"),
	re.compile(rf"os\.environ\[\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\]"),
	re.compile(rf"Config\(\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\)"),
	re.compile(rf"process\.env\.(?P<var>{_VAR_NAME_PATTERN})"),
	re.compile(rf"process\.env\[\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\]"),
	re.compile(rf"os\.Getenv\(\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\)"),
	re.compile(rf"getenv\(\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\)"),
	re.compile(rf"\$_ENV\[\s*['\"](?P<var>{_VAR_NAME_PATTERN})['\"]\s*\]"),
)


@dataclass
class DiscoveryRecord:
	"""Aggregated usage details for one environment variable."""

	reference_count: int = 0
	extensions: Counter[str] = field(default_factory=Counter)


def discover_command(
	target_path: Path = typer.Argument(
		Path("."),
		help="Directory to scan recursively for env var usage.",
	),
	generate_template: bool = typer.Option(
		False,
		"--generate-template",
		help="Write discovered variables to .env.template in the target directory.",
	),
) -> None:
	"""Discover environment variable usage across a workspace."""
	path = target_path.resolve()
	if not path.exists():
		raise typer.BadParameter(f"Path does not exist: {target_path}")

	discovery = discover_environment_variables(path)
	_render_discovery_table(discovery)

	if generate_template:
		template_dir = path if path.is_dir() else path.parent
		template_path = template_dir / ".env.template"
		write_template(template_path=template_path, variable_names=sorted(discovery.keys()))
		Console().print(f"[green]Generated template:[/green] {template_path}")


def discover_environment_variables(root_path: Path) -> dict[str, DiscoveryRecord]:
	"""Scan files under a path and aggregate env variable usage."""
	results: dict[str, DiscoveryRecord] = {}
	for file_path in _iter_candidate_files(root_path):
		extension = file_path.suffix.lower() or "(no-ext)"
		for variable_name in scan_text_for_variables(file_path):
			record = results.setdefault(variable_name, DiscoveryRecord())
			record.reference_count += 1
			record.extensions[extension] += 1
	return results


def _iter_candidate_files(root_path: Path) -> Iterable[Path]:
	"""Yield text-like files recursively while skipping noisy directories."""
	if root_path.is_file():
		if _is_text_file(root_path):
			yield root_path
		return

	for child in root_path.iterdir():
		if child.is_dir():
			if child.name in IGNORED_DIRECTORIES:
				continue
			yield from _iter_candidate_files(child)
		elif child.is_file() and _is_text_file(child):
			yield child


def _is_text_file(file_path: Path, sample_size: int = 4096) -> bool:
	"""Detect binary files using null-byte and UTF-8 decoding heuristics."""
	try:
		sample = file_path.read_bytes()[:sample_size]
	except OSError:
		return False

	if not sample:
		return True
	if b"\x00" in sample:
		return False

	try:
		sample.decode("utf-8")
	except UnicodeDecodeError:
		return False
	return True


def scan_text_for_variables(file_path: Path) -> list[str]:
	"""Extract variable names from one source file using regex patterns."""
	try:
		text = file_path.read_text(encoding="utf-8")
	except (OSError, UnicodeDecodeError):
		return []

	matches: list[str] = []
	for pattern in PATTERNS:
		for match in pattern.finditer(text):
			value = match.group("var")
			if value:
				matches.append(value)
	return matches


def write_template(template_path: Path, variable_names: list[str]) -> None:
	"""Write a .env.template file with one discovered variable per line."""
	content = "".join(f"{name}=\n" for name in variable_names)
	template_path.write_text(content, encoding="utf-8")


def _render_discovery_table(discovery: dict[str, DiscoveryRecord]) -> None:
	"""Print discovery summary in a rich table."""
	console = Console()
	if not discovery:
		console.print("[yellow]No environment variable references found.[/yellow]")
		return

	table = Table(title="EnvSync Discovery Summary")
	table.add_column("Variable", style="cyan", no_wrap=True)
	table.add_column("References", justify="right")
	table.add_column("Primary Extension", style="magenta")

	ordered = sorted(
		discovery.items(),
		key=lambda item: (-item[1].reference_count, item[0]),
	)
	for variable_name, record in ordered:
		primary_extension = record.extensions.most_common(1)[0][0]
		table.add_row(variable_name, str(record.reference_count), primary_extension)

	console.print(table)