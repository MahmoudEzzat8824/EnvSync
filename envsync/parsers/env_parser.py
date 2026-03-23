"""Parser for .env files."""

from __future__ import annotations

from pathlib import Path


class EnvParseError(ValueError):
	"""Raised when a .env file contains invalid syntax."""


def parse_env_file(file_path: str | Path) -> dict[str, str]:
	"""Parse a .env file into a dictionary.

	Args:
		file_path: Path to the .env file.

	Returns:
		Mapping of environment variable keys to values.

	Raises:
		FileNotFoundError: If the input path does not exist.
		IsADirectoryError: If the input path points to a directory.
		EnvParseError: If the content contains invalid lines or duplicate keys.
	"""
	path = Path(file_path)
	if not path.exists():
		raise FileNotFoundError(f".env file not found: {path}")
	if path.is_dir():
		raise IsADirectoryError(f"Expected file but got directory: {path}")

	content = path.read_text(encoding="utf-8")
	return parse_env_content(content=content, source=str(path))


def parse_env_content(content: str, source: str = "<memory>") -> dict[str, str]:
	"""Parse .env content into a dictionary.

	Supported syntax:
	- Empty lines and comment lines starting with '#'
	- Optional leading `export` keyword
	- KEY=VALUE assignments (including empty values)

	Args:
		content: Raw text content of a .env file.
		source: Human-readable source name used in parse errors.

	Returns:
		Mapping of environment variable keys to values.

	Raises:
		EnvParseError: If a line is malformed or a key appears more than once.
	"""
	result: dict[str, str] = {}

	for line_number, raw_line in enumerate(content.splitlines(), start=1):
		line = raw_line.strip()
		if not line or line.startswith("#"):
			continue

		if line.startswith("export "):
			line = line[len("export ") :].strip()

		if "=" not in line:
			raise EnvParseError(
				f"{source}:{line_number}: invalid line; expected KEY=VALUE"
			)

		key_part, value_part = line.split("=", 1)
		key = key_part.strip()
		value = value_part.strip()

		if not key:
			raise EnvParseError(f"{source}:{line_number}: empty key is not allowed")

		if key in result:
			raise EnvParseError(
				f"{source}:{line_number}: duplicate key detected: {key}"
			)

		result[key] = _normalize_env_value(value)

	return result


def _normalize_env_value(value: str) -> str:
	"""Normalize a parsed env value.

	The parser removes surrounding matching single or double quotes if present.
	Other content is preserved as-is.
	"""
	if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
		return value[1:-1]
	return value
