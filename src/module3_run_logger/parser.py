"""
Run log parser: converts free-text run descriptions into structured data.

Orchestrates TokenExtractor (distance/pace), EmbeddingMatcher (terrain/
workout type), and SentimentScorer (effort) to produce a structured dict
that Module 5 and Module 6 can consume.

Example:
    >>> from module3_run_logger.parser import RunLogParser
    >>> parser = RunLogParser()
    >>> result = parser.parse(
    ...     "did my long run on the trail today, 10 miles at 9:30 pace. "
    ...     "felt pretty tired by mile 8 but the soft surface helped my shins"
    ... )
    >>> result["type"]
    'long run'
    >>> result["distance"]
    10.0
    >>> result["terrain"]
    'trail'
"""

import re
from typing import Any, Optional

from .extractor import TokenExtractor
from .matcher import EmbeddingMatcher
from .sentiment import SentimentScorer


class RunLogParser:
    """Parses a free-text run description into a structured dict.

    Uses three components:
    - TokenExtractor: regex/n-gram patterns for distance and pace.
    - EmbeddingMatcher: Word2Vec cosine similarity for terrain and type.
    - SentimentScorer: weighted lexicon for effort classification.

    Args:
        model_path: Optional path to a local Word2Vec model file.
                    Passed through to EmbeddingMatcher.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._extractor = TokenExtractor()
        self._matcher = EmbeddingMatcher(model_path=model_path)
        self._scorer = SentimentScorer()

    def parse(self, text: str) -> dict[str, Any]:
        """Parse a free-text run description into structured data.

        Args:
            text: Free-text run description from the runner.

        Returns:
            Dict with keys:
                type (str): canonical workout type
                distance (float | None): distance in miles
                pace_minutes (float | None): pace in decimal minutes/mile
                terrain (str): canonical terrain label
                sentiment (str): effort level (easy/moderate/hard/struggled)
                notes (str): original text preserved as notes

        Raises:
            ValueError: If text is empty or not a string.
        """
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
        """Light normalization to improve pattern matching reliability.

        - Lowercases the text
        - Inserts a space between digits and letters ("10mi" → "10 mi")
        - Collapses multiple spaces
        - Converts unicode apostrophes to straight apostrophes

        Args:
            text: Raw input text.

        Returns:
            Normalized text string.
        """
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