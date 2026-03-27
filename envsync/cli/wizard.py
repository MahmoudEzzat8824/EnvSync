"""Interactive wizard for guided EnvSync usage."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import questionary
import typer
from rich.console import Console
from rich.panel import Panel


CompareRunner = Callable[..., None]
DiscoverRunner = Callable[..., None]


def run_interactive_wizard(
	compare_runner: CompareRunner,
	discover_runner: DiscoverRunner,
) -> None:
	"""Run a guided workflow for compare/discover commands."""
	console = Console()
	_show_welcome(console)

	while True:
		action = questionary.select(
			"What would you like to do?",
			choices=[
				"Compare Environments",
				"Discover Variables in Code",
				"Exit",
			],
		).ask()

		if action is None or action == "Exit":
			console.print("[bold cyan]Thanks for using EnvSync.[/bold cyan]")
			return

		if action == "Compare Environments":
			_run_compare_flow(console=console, compare_runner=compare_runner)
			continue

		if action == "Discover Variables in Code":
			_run_discover_flow(console=console, discover_runner=discover_runner)


def _show_welcome(console: Console) -> None:
	"""Render a rich welcome panel for the wizard."""
	banner = (
		"[bold cyan]========================================[/bold cyan]\n"
		"[bold cyan]                ENVSYNC                 [/bold cyan]\n"
		"[bold cyan]========================================[/bold cyan]\n"
		"\n"
		"[bold white]Find config drift before production does.[/bold white]"
	)
	panel = Panel.fit(
		banner,
		title="[bold green]EnvSync Interactive Wizard[/bold green]",
		border_style="green",
	)
	console.print(panel)


def _run_compare_flow(console: Console, compare_runner: CompareRunner) -> None:
	"""Collect environment file paths and execute compare flow."""
	paths = _collect_compare_paths(console)
	if not paths:
		console.print("[yellow]Compare cancelled.[/yellow]")
		return

	try:
		compare_runner(env_files=paths, json_output=False, fail_on_drift=False)
	except typer.BadParameter as exc:
		console.print(f"[red]Compare failed:[/red] {exc}")


def _collect_compare_paths(console: Console) -> list[Path]:
	"""Prompt for compare file inputs until user stops adding files."""
	paths: list[Path] = []

	while True:
		file_input = questionary.text(
			"Enter environment file path (.env/.yaml/.yml):",
			default="./",
		).ask()
		if file_input is None:
			return []

		paths.append(_normalize_user_path(file_input))

		add_another = questionary.confirm(
			"Add another environment file?",
			default=True,
		).ask()
		if add_another is None:
			return []
		if not add_another:
			if len(paths) < 2:
				console.print("[yellow]Please provide at least two files for comparison.[/yellow]")
				continue
			break

	return paths


def _run_discover_flow(console: Console, discover_runner: DiscoverRunner) -> None:
	"""Collect discover options and execute discover flow."""
	target_paths = _collect_discover_paths()
	if not target_paths:
		console.print("[yellow]Discover cancelled.[/yellow]")
		return

	generate_template = questionary.confirm(
		"Generate a .env.template file based on discoveries?",
		default=False,
	).ask()
	if generate_template is None:
		console.print("[yellow]Discover cancelled.[/yellow]")
		return

	try:
		discover_runner(
			target_paths=target_paths,
			generate_template=generate_template,
		)
	except typer.BadParameter as exc:
		console.print(f"[red]Discover failed:[/red] {exc}")


def _collect_discover_paths() -> list[Path]:
	"""Prompt for one or more discover scan paths."""
	paths: list[Path] = []

	while True:
		target = questionary.text(
			"Enter a path to scan:",
		).ask()
		if target is None:
			return []

		paths.append(_normalize_user_path(target))

		add_another = questionary.confirm(
			"Add another path to scan?",
			default=False,
		).ask()
		if add_another is None:
			return []
		if not add_another:
			break

	return paths


def _normalize_user_path(raw_value: str) -> Path:
	"""Normalize wizard path input while preserving absolute intent.

	Some prompt toolkits may return values without a leading slash even when
	users intend absolute paths (for example: `media/...`). In that case, if
	`/<value>` exists, prefer it.
	"""
	value = raw_value.strip()
	if not value:
		return Path(".")

	path = Path(value).expanduser()
	if path.is_absolute():
		return path

	abs_candidate = Path("/") / value
	if abs_candidate.exists():
		return abs_candidate

	return path