"""
Module 3: Natural Language Run Logger.

Converts free-text run descriptions into structured data using:
- N-gram regex patterns for distance and pace extraction
- Word2Vec embeddings + cosine similarity for terrain and workout type
- Sentiment (mood) and effort (workout difficulty) classification
- JSON persistence for historical run storage

Public API:
    parse_run     - Parse a free-text description into a structured dict.
    log_run       - Parse and persist a run entry, returning the run ID.
    get_run_history - Retrieve stored run history.

Parsed dict includes:
    sentiment - how the user feels (positive, neutral, negative)
    effort    - how hard the run felt (easy, moderate, hard, struggled)
"""

from .parser import RunLogParser
from .store import RunLogStore

_DEFAULT_STORE = RunLogStore("data/run_log.json")
_DEFAULT_PARSER = RunLogParser()


def parse_run(text: str) -> dict:
    """Parse a free-text run description into structured data.

    Args:
        text: Free-text run description from the runner.

    Returns:
        Dict with type, distance, pace_minutes, terrain, sentiment (mood),
        effort (workout difficulty), and notes.
    """
    return _DEFAULT_PARSER.parse(text)


def log_run(text: str, store_path: str = "data/run_log.json") -> str:
    """Parse a run description and persist it to the run log.

    Args:
        text: Free-text run description.
        store_path: Path to the JSON log file.

    Returns:
        The generated run ID (e.g. "run_001").
    """
    store = RunLogStore(store_path)
    parsed = _DEFAULT_PARSER.parse(text)
    return store.save_run(text, parsed)


def get_run_history(n: int = 10, store_path: str = "data/run_log.json") -> list:
    """Retrieve recent run history from the log.

    Args:
        n: Number of recent runs to retrieve.
        store_path: Path to the JSON log file.

    Returns:
        List of run entry dicts, most recent last.
    """
    store = RunLogStore(store_path)
    return store.get_recent_runs(n)


__all__ = ["parse_run", "log_run", "get_run_history", "RunLogParser", "RunLogStore"]
