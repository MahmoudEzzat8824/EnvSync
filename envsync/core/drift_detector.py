"""Drift detection engine across multiple environments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from envsync.models.types import ParsedVariables
from envsync.utils.hashing import sha256_hexdigest


@dataclass(frozen=True)
class DriftReport:
	"""Result of comparing configuration keys across environments."""

	environment_names: list[str]
	all_keys: list[str]
	missing_by_environment: dict[str, list[str]]
	extra_by_environment: dict[str, list[str]]
	different_values: list[str]
	consistent_values: list[str]
	secret_keys: list[str]


def detect_drift(environments: Mapping[str, ParsedVariables]) -> DriftReport:
	"""Detect configuration drift across multiple environments.

	Args:
		environments: Mapping of environment names to parsed key-value records.

	Returns:
		A DriftReport grouped by issue type.

	Raises:
		ValueError: If fewer than two environments are provided.
	"""
	if len(environments) < 2:
		raise ValueError("At least two environments are required for comparison")

	environment_names = list(environments.keys())
	environment_key_sets = {
		env_name: set(values.keys()) for env_name, values in environments.items()
	}
	all_keys = sorted(set().union(*environment_key_sets.values()))

	key_occurrence_count = {key: 0 for key in all_keys}
	for key_set in environment_key_sets.values():
		for key in key_set:
			key_occurrence_count[key] += 1

	missing_by_environment: dict[str, list[str]] = {}
	extra_by_environment: dict[str, list[str]] = {}
	for env_name in environment_names:
		present_keys = environment_key_sets[env_name]
		missing_by_environment[env_name] = sorted(set(all_keys) - present_keys)
		extra_by_environment[env_name] = sorted(
			key for key in present_keys if key_occurrence_count[key] == 1
		)

	different_values: list[str] = []
	consistent_values: list[str] = []
	secret_keys: list[str] = []

	for key in all_keys:
		present_envs = [env_name for env_name in environment_names if key in environments[env_name]]
		if len(present_envs) != len(environment_names):
			continue

		variables = [environments[env_name][key] for env_name in environment_names]
		is_secret = any(variable.is_secret for variable in variables)
		if is_secret:
			secret_keys.append(key)

		comparison_values = [
			sha256_hexdigest(variable.value) if is_secret else variable.value
			for variable in variables
		]

		if len(set(comparison_values)) == 1:
			consistent_values.append(key)
		else:
			different_values.append(key)

	return DriftReport(
		environment_names=environment_names,
		all_keys=all_keys,
		missing_by_environment=missing_by_environment,
		extra_by_environment=extra_by_environment,
		different_values=sorted(different_values),
		consistent_values=sorted(consistent_values),
		secret_keys=sorted(secret_keys),
	)
