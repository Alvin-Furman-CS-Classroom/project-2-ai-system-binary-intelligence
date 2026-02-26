"""
Token extraction using n-gram style regex patterns.

Extracts numeric entities (distance, pace) from free-text run descriptions
by scanning for known word-pair patterns — the same idea as bigram/trigram
context matching from the course slides.

Example:
    >>> from module3_run_logger.extractor import TokenExtractor
    >>> ex = TokenExtractor()
    >>> ex.extract_distance("ran 10 miles on the trail")
    10.0
    >>> ex.extract_pace("finished at 9:30 pace")
    9.5
"""

import re
from typing import Optional


class TokenExtractor:
    """Extracts distance and pace values from free-text run descriptions.

    Uses regex patterns that capture common runner phrasings. Each pattern
    is essentially a bigram or trigram: a number token paired with a unit
    token (or a pace token paired with a colon-separated time).

    Distance patterns cover miles, kilometres, and named race distances.
    Pace patterns cover MM:SS formats with optional /mile or /km suffixes.
    """

    # Named race distances in miles.
    _NAMED_DISTANCES: dict[str, float] = {
        "marathon": 26.2,
        "half marathon": 13.1,
        "half-marathon": 13.1,
        "10k": 6.2,
        "5k": 3.1,
        "10 k": 6.2,
        "5 k": 3.1,
    }

    # Ordered list of (pattern, handler) tuples tried in sequence.
    # First match wins.
    _DISTANCE_PATTERNS: list[tuple[str, str]] = [
    # NEW: "6x800m", "8x400m", "10x200m"
    (r"(\d+)\s*x\s*(\d+)\s*m\b", "reps_meters"),   # ← add this line
    (r"(\d+(?:\.\d+)?)\s*(?:miles?|mi\b)", "miles"),
    (r"(\d+(?:\.\d+)?)\s*(?:k(?:m|ilom(?:et(?:re|er)s?)?)?\b)", "km"),
    ]

    _PACE_PATTERNS: list[tuple[str, str]] = [
        # "9:30 pace", "9:30/mile", "9:30 per mile", "at 9:30", "9:30/km"
        (r"(\d{1,2}):(\d{2})\s*(?:/?(?:per\s+)?(?:mile|mi|km|k)\b|pace\b|$|\s)", "mm_ss"),
        # "sub-9 minute miles", "sub 9 min pace"
        (r"sub[-\s]?(\d+)\s*(?:minute|min)", "sub_min"),
    ]

    def extract_distance(self, text: str) -> Optional[float]:
        """Extract distance in miles from a run description.

        Checks named distances first, then numeric patterns.

        Args:
            text: Free-text run description.

        Returns:
            Distance in miles as a float, or None if not found.
        """
        lower = text.lower()

        # Check named distances first (longest match wins).
        for name, miles in sorted(
            self._NAMED_DISTANCES.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if name in lower:
                return miles

        # Numeric patterns.
        for pattern, unit in self._DISTANCE_PATTERNS:
            match = re.search(pattern, lower)
            if match:
                if unit == "reps_meters":
                    reps = int(match.group(1))
                    meters = int(match.group(2))
                    total_miles = round((reps * meters / 1000) * 0.621371, 2)
                    return total_miles
                value = float(match.group(1))
                if unit == "km":
                    value = round(value * 0.621371, 2)
                return value

        return None

    def extract_pace(self, text: str) -> Optional[float]:
        """Extract pace in decimal minutes per mile from a run description.

        Handles MM:SS formats and sub-N minute phrasings.

        Args:
            text: Free-text run description.

        Returns:
            Pace as decimal minutes per mile (e.g. 9:30 → 9.5), or None.
        """
        lower = text.lower()
        for pattern, kind in self._PACE_PATTERNS:
            match = re.search(pattern, lower)
            if match:
                if kind == "mm_ss":
                    minutes = int(match.group(1))
                    seconds = int(match.group(2))
                    if seconds >= 60:
                        return None
                    return round(minutes + seconds / 60, 4)
                elif kind == "sub_min":
                    # "sub-9 minute" → return 9.0 as the pace ceiling
                    return float(match.group(1))
        return None

    def extract_notes(self, text: str) -> str:
        """Return the raw text as notes after stripping leading/trailing space.

        Args:
            text: Free-text run description.

        Returns:
            Cleaned notes string.
        """
        return text.strip()