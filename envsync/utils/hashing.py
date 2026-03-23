"""Hashing helpers for safe secret comparison."""

from __future__ import annotations

import hashlib


def sha256_hexdigest(value: str) -> str:
	"""Return the SHA256 hex digest for a string value.

	Args:
		value: Plain text input value.

	Returns:
		Hex-encoded SHA256 digest.
	"""
	return hashlib.sha256(value.encode("utf-8")).hexdigest()
