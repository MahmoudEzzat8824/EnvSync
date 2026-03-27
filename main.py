"""EnvSync CLI entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from envsync.cli.app import app
from envsync.cli.discover import discover_command


def _is_script_discover_args(args: list[str]) -> bool:
    """Return True when argv payload should run direct discover script mode."""
    if not args:
        return False
    if any(arg.startswith("-") for arg in args):
        return False

    known_commands = {"compare", "discover", "interactive"}
    if any(arg in known_commands for arg in args):
        return False

    return all(Path(arg).expanduser().exists() for arg in args)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if len(sys.argv) == 1:
        app()
    elif _is_script_discover_args(argv):
        try:
            discover_command(
                target_paths=[Path(arg).expanduser() for arg in argv],
                generate_template=False,
            )
        except typer.BadParameter as exc:
            typer.secho(f"Error: {exc}", fg=typer.colors.RED)
            raise typer.Exit(code=2)
    else:
        app()
