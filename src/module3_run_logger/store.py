"""
Run log storage using JSON persistence.

Stores parsed run entries with timestamps so Module 5 (progression)
and Module 6 (predictions) can access historical run data.

Example:
    >>> from module3_run_logger.store import RunLogStore
    >>> store = RunLogStore("data/run_log.json")
    >>> store.save_run("felt good today, 5 miles easy", {"type": "easy", "distance": 5.0})
    >>> runs = store.get_recent_runs(5)
"""

import json
import os
from datetime import datetime
from typing import Any, Optional


class RunLogStore:
    """Persists parsed run entries to a JSON file.

    Each entry stores the raw input text, the parsed structured data,
    and a timestamp. Keeping the raw input allows re-parsing if the
    parsing logic improves later.

    No file locking is used; concurrent writes from multiple processes
    could corrupt the file. Safe for single-process / single-user use.

    Args:
        filepath: Path to the JSON log file. Created if it does not exist.
    """

    def __init__(self, filepath: str = "data/run_log.json") -> None:
        self.filepath = filepath
        self._ensure_file()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_run(self, raw_input: str, parsed: dict[str, Any]) -> str:
        """Append a parsed run entry to the log.

        Run IDs are monotonic (run_001, run_002, ...) and never reuse,
        even after clear(), so each ID is unique for the lifetime of the file.

        Args:
            raw_input: The original free-text description from the runner.
            parsed: Structured run data produced by RunLogParser.

        Returns:
            The generated run ID (e.g. "run_001").
        """
        data = self._load()
        next_id = data.get("next_id", len(data["runs"]) + 1)
        run_id = f"run_{next_id:03d}"
        entry = {
            "id": run_id,
            "logged_at": datetime.now().isoformat(),
            "raw_input": raw_input,
            "parsed": parsed,
        }
        data["runs"].append(entry)
        data["next_id"] = next_id + 1
        self._save(data)
        return run_id

    def get_runs(self) -> list[dict[str, Any]]:
        """Return all stored run entries in chronological order.

        Returns:
            List of run entry dicts, oldest first.
        """
        return self._load()["runs"]

    def get_recent_runs(self, n: int) -> list[dict[str, Any]]:
        """Return the n most recent run entries.

        Args:
            n: Number of recent runs to retrieve. Must be >= 1.

        Returns:
            List of run entry dicts, most recent last.

        Raises:
            ValueError: If n < 1.
        """
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")
        runs = self._load()["runs"]
        return runs[-n:]

    def get_runs_by_date_range(
        self,
        start: str,
        end: str,
    ) -> list[dict[str, Any]]:
        """Return runs logged between start and end (inclusive).

        Args:
            start: ISO format date string, e.g. "2026-01-01".
            end: ISO format date string, e.g. "2026-02-01".

        Returns:
            List of matching run entry dicts.

        Raises:
            ValueError: If start or end are not valid ISO date strings.
        """
        try:
            # Accept both "YYYY-MM-DD" and full ISO datetime strings.
            start_dt = datetime.fromisoformat(
                start if "T" in start else start + "T00:00:00"
            )
            end_dt = datetime.fromisoformat(
                end if "T" in end else end + "T23:59:59"
            )
        except ValueError as exc:
            raise ValueError(
                f"start and end must be valid ISO date strings: {exc}"
            ) from exc

        runs = self._load()["runs"]
        result = []
        for run in runs:
            logged = datetime.fromisoformat(run["logged_at"])
            if start_dt <= logged <= end_dt:
                result.append(run)
        return result

    def clear(self) -> None:
        """Delete all stored runs. Useful for testing.

        The next_id counter is preserved, so the next save_run() continues
        from the previous ID (e.g. run_004); IDs never reuse.
        """
        data = self._load()
        next_id = data.get("next_id", 1)
        self._save({"runs": [], "next_id": next_id})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_file(self) -> None:
        """Create the JSON file and any parent directories if needed."""
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        if not os.path.exists(self.filepath):
            self._save({"runs": [], "next_id": 1})

    def _load(self) -> dict[str, Any]:
        """Load and return the full JSON structure."""
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict[str, Any]) -> None:
        """Write the full JSON structure to disk."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
