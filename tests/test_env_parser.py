"""Unit tests for .env parsing."""

from __future__ import annotations

import pytest

from envsync.parsers.env_parser import EnvParseError, parse_env_content


def test_parse_env_content_success() -> None:
    """It parses comments, export syntax, quotes, and empty values."""
    content = """
# comment
API_URL=https://example.com
export JWT_SECRET="top-secret"
EMPTY=

"""

    result = parse_env_content(content, source="dev.env")

    assert result == {
        "API_URL": "https://example.com",
        "JWT_SECRET": "top-secret",
        "EMPTY": "",
    }


def test_parse_env_content_invalid_line_raises() -> None:
    """It raises when a non-empty line does not contain '='."""
    content = """
VALID=1
BROKEN_LINE
"""

    with pytest.raises(EnvParseError, match="invalid line"):
        parse_env_content(content, source="broken.env")


def test_parse_env_content_duplicate_key_raises() -> None:
    """It raises when duplicate keys are present in the same file."""
    content = """
A=1
A=2
"""

    with pytest.raises(EnvParseError, match="duplicate key"):
        parse_env_content(content, source="dup.env")
