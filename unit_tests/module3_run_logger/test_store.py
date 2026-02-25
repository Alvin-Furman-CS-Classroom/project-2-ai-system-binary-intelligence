"""
Unit tests for RunLogStore.

Tests cover: saving runs, retrieving all runs, recent runs,
date range filtering, clearing, and error handling.
"""

import os
import tempfile
import pytest
from datetime import datetime

from src.module3_run_logger.store import RunLogStore


@pytest.fixture
def store(tmp_path):
    """RunLogStore backed by a temp file."""
    return RunLogStore(str(tmp_path / "test_log.json"))


@pytest.fixture
def sample_parsed():
    return {
        "type": "easy run",
        "distance": 5.0,
        "pace_minutes": 9.5,
        "terrain": "road",
        "sentiment": "easy",
        "notes": "felt great",
    }


class TestSaveRun:
    def test_returns_run_id(self, store, sample_parsed):
        run_id = store.save_run("felt great", sample_parsed)
        assert run_id == "run_001"

    def test_sequential_ids(self, store, sample_parsed):
        id1 = store.save_run("run 1", sample_parsed)
        id2 = store.save_run("run 2", sample_parsed)
        assert id1 == "run_001"
        assert id2 == "run_002"

    def test_entry_contains_raw_input(self, store, sample_parsed):
        store.save_run("my raw text here", sample_parsed)
        runs = store.get_runs()
        assert runs[0]["raw_input"] == "my raw text here"

    def test_entry_contains_parsed_data(self, store, sample_parsed):
        store.save_run("text", sample_parsed)
        runs = store.get_runs()
        assert runs[0]["parsed"]["distance"] == 5.0

    def test_entry_contains_timestamp(self, store, sample_parsed):
        store.save_run("text", sample_parsed)
        runs = store.get_runs()
        assert "logged_at" in runs[0]
        datetime.fromisoformat(runs[0]["logged_at"])  # must be valid ISO


class TestGetRuns:
    def test_empty_store_returns_empty_list(self, store):
        assert store.get_runs() == []

    def test_returns_all_runs_in_order(self, store, sample_parsed):
        store.save_run("run 1", sample_parsed)
        store.save_run("run 2", sample_parsed)
        runs = store.get_runs()
        assert len(runs) == 2
        assert runs[0]["id"] == "run_001"
        assert runs[1]["id"] == "run_002"


class TestGetRecentRuns:
    def test_returns_n_most_recent(self, store, sample_parsed):
        for i in range(5):
            store.save_run(f"run {i}", sample_parsed)
        recent = store.get_recent_runs(3)
        assert len(recent) == 3
        assert recent[-1]["id"] == "run_005"

    def test_returns_all_if_fewer_than_n(self, store, sample_parsed):
        store.save_run("only run", sample_parsed)
        recent = store.get_recent_runs(10)
        assert len(recent) == 1

    def test_n_less_than_1_raises(self, store):
        with pytest.raises(ValueError):
            store.get_recent_runs(0)

    def test_n_equals_1_returns_last(self, store, sample_parsed):
        store.save_run("run 1", sample_parsed)
        store.save_run("run 2", sample_parsed)
        recent = store.get_recent_runs(1)
        assert recent[0]["id"] == "run_002"


class TestGetRunsByDateRange:
    def test_invalid_start_raises(self, store):
        with pytest.raises(ValueError):
            store.get_runs_by_date_range("not-a-date", "2026-01-01")

    def test_invalid_end_raises(self, store):
        with pytest.raises(ValueError):
            store.get_runs_by_date_range("2026-01-01", "bad")

    def test_returns_runs_in_range(self, store, sample_parsed):
        store.save_run("run", sample_parsed)
        runs = store.get_runs()
        logged_at = runs[0]["logged_at"][:10]  # YYYY-MM-DD
        result = store.get_runs_by_date_range(logged_at, logged_at)
        assert len(result) == 1

    def test_returns_empty_for_future_range(self, store, sample_parsed):
        store.save_run("run", sample_parsed)
        result = store.get_runs_by_date_range("2099-01-01", "2099-12-31")
        assert result == []


class TestClear:
    def test_clear_removes_all_runs(self, store, sample_parsed):
        store.save_run("run", sample_parsed)
        store.clear()
        assert store.get_runs() == []

    def test_can_save_after_clear(self, store, sample_parsed):
        store.save_run("run", sample_parsed)
        store.clear()
        run_id = store.save_run("new run", sample_parsed)
        # IDs are monotonic; after clear the next ID is run_002 (never reuse).
        assert run_id == "run_002"


class TestPersistence:
    def test_data_persists_across_instances(self, tmp_path, sample_parsed):
        path = str(tmp_path / "log.json")
        store1 = RunLogStore(path)
        store1.save_run("persisted run", sample_parsed)

        store2 = RunLogStore(path)
        runs = store2.get_runs()
        assert len(runs) == 1
        assert runs[0]["raw_input"] == "persisted run"

    def test_creates_parent_directories(self, tmp_path):
        deep_path = str(tmp_path / "a" / "b" / "c" / "log.json")
        store = RunLogStore(deep_path)
        assert os.path.exists(deep_path)
