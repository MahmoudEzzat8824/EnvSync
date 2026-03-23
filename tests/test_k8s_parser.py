"""Unit tests for Kubernetes YAML parsing."""

from __future__ import annotations

import pytest

from envsync.parsers.k8s_parser import K8sParseError, parse_k8s_yaml_content


def test_parse_k8s_yaml_content_extracts_configmap_and_secret() -> None:
    """It extracts ConfigMap and Secret keys with proper secret flags."""
    content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  API_URL: https://api.example.com
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
stringData:
  JWT_SECRET: my-secret
data:
  TOKEN: dG9rZW4=
"""

    result = parse_k8s_yaml_content(content, source="k8s.yaml")

    assert result["API_URL"].value == "https://api.example.com"
    assert result["API_URL"].is_secret is False

    assert result["JWT_SECRET"].value == "my-secret"
    assert result["JWT_SECRET"].is_secret is True

    assert result["TOKEN"].value == "token"
    assert result["TOKEN"].is_secret is True


def test_parse_k8s_yaml_content_invalid_yaml_raises() -> None:
    """It raises on malformed YAML content."""
    content = "kind: ConfigMap\nmetadata: ["

    with pytest.raises(K8sParseError, match="invalid YAML"):
        parse_k8s_yaml_content(content, source="broken.yaml")


def test_parse_k8s_yaml_content_duplicate_key_raises() -> None:
    """It raises when the same key appears across manifests."""
    content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: cm1
data:
  API_URL: https://dev.example.com
---
apiVersion: v1
kind: Secret
metadata:
  name: sec1
stringData:
  API_URL: should-conflict
"""

    with pytest.raises(K8sParseError, match="duplicate key"):
        parse_k8s_yaml_content(content, source="dupe.yaml")
