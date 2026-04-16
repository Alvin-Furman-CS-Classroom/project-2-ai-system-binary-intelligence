import re
from typing import Any, Optional

from .extractor import TokenExtractor
from .matcher import EmbeddingMatcher
from .sentiment import SentimentScorer


class RunLogParser:

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._extractor = TokenExtractor()
        self._matcher = EmbeddingMatcher(model_path=model_path)
        self._scorer = SentimentScorer()

    def parse(self, text: str) -> dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        normalized = self._normalize(text)

        return {
            "type": self._matcher.match_workout_type(normalized),
            "distance": self._extractor.extract_distance(normalized),
            "pace_minutes": self._extractor.extract_pace(normalized),
            "terrain": self._matcher.match_terrain(normalized),
            "sentiment": self._scorer.score(normalized),
            "notes": self._extractor.extract_notes(text),  # preserve original
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize(self, text: str) -> str:

        # Normalize unicode apostrophes to straight apostrophe
        normalized = text.replace("\u2019", "'").replace("\u2018", "'")
        # Lowercase so downstream matching is case-insensitive
        normalized = normalized.lower()
        # Insert space between digit and alpha letter only ("10mi" → "10 mi")
        # Excludes colon so pace patterns like "9:30" are preserved
        normalized = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", normalized)
        normalized = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", normalized)
        # Collapse multiple spaces
        normalized = re.sub(r"  +", " ", normalized).strip()
        return normalized