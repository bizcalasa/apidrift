"""Tests for apidrift.config."""

import json
import pytest
from pathlib import Path

from apidrift.config import DriftConfig, load_config


def test_defaults():
    cfg = DriftConfig()
    assert cfg.output_format == "text"
    assert cfg.breaking_only is False
    assert cfg.ignore_paths == []
    assert cfg.ignore_methods == []


def test_should_ignore_path():
    cfg = DriftConfig(ignore_paths=["/health"])
    assert cfg.should_ignore("/health", "get") is True
    assert cfg.should_ignore("/users", "get") is False


def test_should_ignore_method():
    cfg = DriftConfig(ignore_methods=["OPTIONS"])
    assert cfg.should_ignore("/any", "options") is True
    assert cfg.should_ignore("/any", "get") is False


def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert isinstance(cfg, DriftConfig)


def test_load_config_from_json(tmp_path):
    data = {
        "output_format": "json",
        "breaking_only": True,
        "ignore_paths": ["/ping"],
        "ignore_methods": ["HEAD"],
    }
    cfg_file = tmp_path / "apidrift.json"
    cfg_file.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(cfg_file)
    assert cfg.output_format == "json"
    assert cfg.breaking_only is True
    assert "/ping" in cfg.ignore_paths
    assert "HEAD" in cfg.ignore_methods


def test_load_config_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.json")


def test_load_config_unsupported_extension_raises(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("output_format: json", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported config format"):
        load_config(cfg_file)


def test_load_config_partial_json(tmp_path):
    data = {"breaking_only": True}
    cfg_file = tmp_path / "apidrift.json"
    cfg_file.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(cfg_file)
    assert cfg.breaking_only is True
    assert cfg.output_format == "text"  # default
