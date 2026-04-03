"""Unit tests for CLI environment file acceptance rules."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from envsync.cli.app import _derive_environment_name, _parse_environment_file


@pytest.mark.parametrize(
    ("filename", "expected_name"),
    [
        ("prod.env", "prod"),
        (".env.local", "local"),
        ("service.env.backup", "service.env"),
        (".env", "env"),
    ],
)
def test_parse_environment_file_accepts_env_like_names(
    tmp_path: Path,
    filename: str,
    expected_name: str,
) -> None:
    """It accepts any file name containing '.env'."""
    file_path = tmp_path / filename
    file_path.write_text("API_URL=https://example.com\n", encoding="utf-8")

    parsed = _parse_environment_file(file_path)

    assert parsed["API_URL"].value == "https://example.com"
    assert parsed["API_URL"].is_secret is False
    assert _derive_environment_name(file_path, index=1) == expected_name


def test_parse_environment_file_rejects_unsupported_file_types(tmp_path: Path) -> None:
    """It rejects files that are neither env-like nor YAML."""
    file_path = tmp_path / "settings.toml"
    file_path.write_text("A=1\n", encoding="utf-8")

    with pytest.raises(typer.BadParameter, match="Unsupported file type"):
        _parse_environment_file(file_path)


def test_parse_environment_file_prefers_yaml_parser_when_extension_is_yaml(
    tmp_path: Path,
) -> None:
    """It treats .yaml/.yml as Kubernetes input even if '.env' appears in name."""
    file_path = tmp_path / "config.env.yaml"
    file_path.write_text(
        """
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  API_URL: https://api.example.com
""".strip()
        + "\n",
        encoding="utf-8",
    )

    parsed = _parse_environment_file(file_path)

    assert parsed["API_URL"].value == "https://api.example.com"
    assert parsed["API_URL"].is_secret is False
