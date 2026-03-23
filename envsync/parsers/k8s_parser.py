"""Parser for Kubernetes ConfigMap and Secret manifests."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any

import yaml

from envsync.models.types import ParsedVariable, ParsedVariables


class K8sParseError(ValueError):
	"""Raised when a Kubernetes manifest cannot be parsed safely."""


def parse_k8s_yaml_file(file_path: str | Path) -> ParsedVariables:
	"""Parse a Kubernetes YAML file and extract ConfigMap/Secret entries.

	Args:
		file_path: Path to a YAML manifest file.

	Returns:
		Mapping of configuration keys to normalized parsed values.

	Raises:
		FileNotFoundError: If the provided file does not exist.
		IsADirectoryError: If the path points to a directory.
		K8sParseError: If YAML is invalid or manifests are malformed.
	"""
	path = Path(file_path)
	if not path.exists():
		raise FileNotFoundError(f"YAML file not found: {path}")
	if path.is_dir():
		raise IsADirectoryError(f"Expected file but got directory: {path}")

	content = path.read_text(encoding="utf-8")
	return parse_k8s_yaml_content(content=content, source=str(path))


def parse_k8s_yaml_content(content: str, source: str = "<memory>") -> ParsedVariables:
	"""Parse Kubernetes YAML content and extract relevant key-value pairs.

	Supported resources:
	- ConfigMap: extracts keys from .data and .binaryData
	- Secret: extracts keys from .stringData and .data

	Args:
		content: Raw YAML content, potentially multi-document.
		source: Human-readable source label included in parse errors.

	Returns:
		Mapping of keys to normalized parsed values.

	Raises:
		K8sParseError: If YAML is invalid, malformed, or contains duplicate keys.
	"""
	extracted: ParsedVariables = {}

	try:
		documents = list(yaml.safe_load_all(content))
	except yaml.YAMLError as exc:
		raise K8sParseError(f"{source}: invalid YAML content") from exc

	for index, document in enumerate(documents, start=1):
		if document is None:
			continue
		if not isinstance(document, dict):
			raise K8sParseError(
				f"{source}: document #{index} must be a mapping object"
			)

		kind = document.get("kind")
		if kind == "ConfigMap":
			_extract_configmap(
				extracted=extracted,
				doc=document,
				source=source,
				doc_index=index,
			)
		elif kind == "Secret":
			_extract_secret(
				extracted=extracted,
				doc=document,
				source=source,
				doc_index=index,
			)

	return extracted


def _extract_configmap(
	extracted: ParsedVariables,
	doc: dict[str, Any],
	source: str,
	doc_index: int,
) -> None:
	"""Extract ConfigMap data entries as non-secret values."""
	data = doc.get("data") or {}
	binary_data = doc.get("binaryData") or {}

	_validate_mapping(data, f"{source}: document #{doc_index}: ConfigMap.data")
	_validate_mapping(
		binary_data, f"{source}: document #{doc_index}: ConfigMap.binaryData"
	)

	for key, value in data.items():
		_insert_unique(
			extracted=extracted,
			key=_validate_key(key, source, doc_index),
			value=ParsedVariable(value=str(value), is_secret=False),
			source=source,
			doc_index=doc_index,
		)

	for key, value in binary_data.items():
		_insert_unique(
			extracted=extracted,
			key=_validate_key(key, source, doc_index),
			value=ParsedVariable(value=str(value), is_secret=False),
			source=source,
			doc_index=doc_index,
		)


def _extract_secret(
	extracted: ParsedVariables,
	doc: dict[str, Any],
	source: str,
	doc_index: int,
) -> None:
	"""Extract Secret entries, decoding .data and preserving .stringData."""
	string_data = doc.get("stringData") or {}
	data = doc.get("data") or {}

	_validate_mapping(string_data, f"{source}: document #{doc_index}: Secret.stringData")
	_validate_mapping(data, f"{source}: document #{doc_index}: Secret.data")

	for key, value in string_data.items():
		_insert_unique(
			extracted=extracted,
			key=_validate_key(key, source, doc_index),
			value=ParsedVariable(value=str(value), is_secret=True),
			source=source,
			doc_index=doc_index,
		)

	for key, value in data.items():
		normalized = _decode_secret_value(
			encoded_value=str(value),
			source=source,
			doc_index=doc_index,
			key=str(key),
		)
		_insert_unique(
			extracted=extracted,
			key=_validate_key(key, source, doc_index),
			value=ParsedVariable(value=normalized, is_secret=True),
			source=source,
			doc_index=doc_index,
		)


def _decode_secret_value(
	encoded_value: str,
	source: str,
	doc_index: int,
	key: str,
) -> str:
	"""Decode a base64 Secret.data value into a stable comparison string."""
	try:
		raw_bytes = base64.b64decode(encoded_value, validate=True)
	except (binascii.Error, ValueError) as exc:
		raise K8sParseError(
			f"{source}: document #{doc_index}: Secret.data[{key}] is not valid base64"
		) from exc

	try:
		return raw_bytes.decode("utf-8")
	except UnicodeDecodeError:
		# Preserve binary data in a deterministic text-safe representation.
		return raw_bytes.hex()


def _insert_unique(
	extracted: ParsedVariables,
	key: str,
	value: ParsedVariable,
	source: str,
	doc_index: int,
) -> None:
	"""Insert a key once and fail fast on collisions across resources."""
	if key in extracted:
		raise K8sParseError(
			f"{source}: document #{doc_index}: duplicate key detected across manifests: {key}"
		)
	extracted[key] = value


def _validate_mapping(value: Any, label: str) -> None:
	"""Ensure the provided YAML field is a mapping."""
	if not isinstance(value, dict):
		raise K8sParseError(f"{label} must be a mapping")


def _validate_key(key: Any, source: str, doc_index: int) -> str:
	"""Validate and normalize configuration keys."""
	if not isinstance(key, str) or not key.strip():
		raise K8sParseError(
			f"{source}: document #{doc_index}: keys must be non-empty strings"
		)
	return key.strip()
