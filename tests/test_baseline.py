"""Tests for apidrift.baseline module."""

from __future__ import annotations

import json
import pytest

from apidrift.baseline import (
    BaselineError,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)

SAMPLE_SPEC: dict = {
    "openapi": "3.0.0",
    "info": {"title": "Demo", "version": "1.0.0"},
    "paths": {"/ping": {"get": {"responses": {"200": {"description": "ok"}}}}},
}


def test_save_and_load_baseline(tmp_path):
    bdir = str(tmp_path / "bl")
    dest = save_baseline("v1", SAMPLE_SPEC, baseline_dir=bdir)
    assert dest.exists()
    loaded = load_baseline("v1", baseline_dir=bdir)
    assert loaded == SAMPLE_SPEC


def test_save_creates_index(tmp_path):
    bdir = str(tmp_path / "bl")
    save_baseline("v1", SAMPLE_SPEC, baseline_dir=bdir)
    index_file = tmp_path / "bl" / "baselines.json"
    assert index_file.exists()
    index = json.loads(index_file.read_text())
    assert "v1" in index


def test_list_baselines_empty(tmp_path):
    bdir = str(tmp_path / "bl")
    assert list_baselines(baseline_dir=bdir) == []


def test_list_baselines_multiple(tmp_path):
    bdir = str(tmp_path / "bl")
    save_baseline("v2", SAMPLE_SPEC, baseline_dir=bdir)
    save_baseline("v1", SAMPLE_SPEC, baseline_dir=bdir)
    assert list_baselines(baseline_dir=bdir) == ["v1", "v2"]


def test_load_missing_name_raises(tmp_path):
    bdir = str(tmp_path / "bl")
    with pytest.raises(BaselineError, match="not found"):
        load_baseline("nope", baseline_dir=bdir)


def test_load_missing_file_raises(tmp_path):
    bdir = str(tmp_path / "bl")
    save_baseline("v1", SAMPLE_SPEC, baseline_dir=bdir)
    (tmp_path / "bl" / "v1.json").unlink()
    with pytest.raises(BaselineError, match="missing"):
        load_baseline("v1", baseline_dir=bdir)


def test_delete_baseline(tmp_path):
    bdir = str(tmp_path / "bl")
    save_baseline("v1", SAMPLE_SPEC, baseline_dir=bdir)
    delete_baseline("v1", baseline_dir=bdir)
    assert list_baselines(baseline_dir=bdir) == []
    assert not (tmp_path / "bl" / "v1.json").exists()


def test_delete_missing_raises(tmp_path):
    bdir = str(tmp_path / "bl")
    with pytest.raises(BaselineError, match="not found"):
        delete_baseline("ghost", baseline_dir=bdir)


def test_overwrite_existing_baseline(tmp_path):
    bdir = str(tmp_path / "bl")
    save_baseline("v1", SAMPLE_SPEC, baseline_dir=bdir)
    updated = {**SAMPLE_SPEC, "info": {"title": "Demo", "version": "2.0.0"}}
    save_baseline("v1", updated, baseline_dir=bdir)
    loaded = load_baseline("v1", baseline_dir=bdir)
    assert loaded["info"]["version"] == "2.0.0"
    assert list_baselines(baseline_dir=bdir) == ["v1"]
