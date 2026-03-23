"""Typed models used across parsing and drift detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class ParsedVariable:
	"""A normalized configuration key-value entry.

	Attributes:
		value: Parsed value used for drift comparison.
		is_secret: Whether this key is sensitive and must not be printed raw.
	"""

	value: str
	is_secret: bool = False


ParsedVariables: TypeAlias = dict[str, ParsedVariable]
