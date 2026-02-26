"""
Effort level and sentiment (mood) scoring from run descriptions.

- **Effort level**: how hard the run felt (easy, moderate, hard, struggled).
- **Sentiment**: how the user is feeling — mood/emotion (positive, neutral, negative),
  e.g. happy, tired, sad, good, okay, frustrated.
"""

import re

_NEGATIONS: set[str] = {
    "not", "never", "no",
    "didn't", "didnt", "wasn't", "wasnt",
    "couldn't", "couldnt", "don't", "dont", "won't", "wont",
}

# ---------------------------------------------------------------------------
# Effort: perceived workout difficulty → easy / moderate / hard / struggled
# ---------------------------------------------------------------------------

_EFFORT_LEXICON: dict[str, float] = {
    "great": 2.0, "excellent": 2.0, "strong": 2.0, "fresh": 2.0,
    "easy": 2.0, "effortless": 2.0, "flew": 2.0, "flying": 2.0,
    "crushed": 2.0, "comfortable": 1.5, "solid": 1.5, "smooth": 1.5,
    "light": 1.5, "energized": 1.5, "recovered": 1.5,
    "cruised": 1.5, "cruising": 1.5, "floated": 1.5, "floating": 1.5,
    "relaxed": 1.5, "controlled": 1.5, "powerful": 1.5,
    "okay": 0.5, "fine": 0.5, "decent": 0.5, "alright": 0.5, "manageable": 0.5,
    "tired": -1.0, "slow": -1.0, "sluggish": -1.0, "heavy": -1.0,
    "sore": -1.0, "tight": -1.0, "stiff": -1.0, "labored": -1.0, "laboured": -1.0,
    "fatigued": -1.0, "drained": -1.0, "flat": -1.0,
    "exhausted": -2.0, "dead": -2.0, "awful": -2.0, "terrible": -2.0,
    "struggled": -2.0, "struggle": -2.0, "struggling": -2.0, "dying": -2.0,
    "hurt": -1.5, "pain": -2.0, "painful": -2.0, "hard": -1.5,
    "tough": -1.5, "difficult": -1.5, "barely": -2.0, "couldnt": -1.5,
    "failed": -2.0, "bonked": -2.0, "bonk": -2.0, "wall": -1.5,
    "crawled": -2.0, "crawling": -2.0, "wrecked": -2.0, "destroyed": -2.0,
    "brutal": -2.0, "suffered": -2.0, "suffering": -2.0,
}

_EFFORT_THRESHOLDS: dict[str, float] = {
    "easy": 1.5,
    "moderate": 0.0,
    "hard": -1.5,
}

# ---------------------------------------------------------------------------
# Sentiment: mood / how the user feels → positive / neutral / negative
# ---------------------------------------------------------------------------

_SENTIMENT_LEXICON: dict[str, float] = {
    # Positive mood
    "happy": 2.0, "great": 1.5, "good": 1.5, "proud": 2.0, "loved": 2.0,
    "satisfied": 1.5, "grateful": 1.5, "excited": 1.5, "amazing": 2.0,
    "fantastic": 2.0, "wonderful": 1.5, "strong": 1.0, "fresh": 1.0,
    # Neutral
    "okay": 0.0, "fine": 0.0, "alright": 0.0, "decent": 0.0,
    # Negative mood
    "tired": -1.0, "sad": -2.0, "bad": -1.5, "awful": -2.0, "terrible": -2.0,
    "frustrated": -1.5, "weak": -1.5, "down": -1.5, "miserable": -2.0,
    "disappointed": -1.5, "angry": -1.5, "exhausted": -1.0, "drained": -1.0,
    "heavy": -0.5, "sore": -0.5, "hurt": -1.0, "pain": -1.5,
    "struggled": -1.0, "barely": -1.5,
}

_SENTIMENT_THRESHOLDS: dict[str, float] = {
    "positive": 0.5,
    "neutral": -0.5,
}


def _score_with_lexicon(
    text: str,
    lexicon: dict[str, float],
    negations: set[str],
) -> float:
    """Sum weighted scores from lexicon with negation handling."""
    tokens = re.findall(r"[a-z']+", text.lower())
    total = 0.0
    negate_next = False
    for token in tokens:
        if token in negations:
            negate_next = True
            continue
        if token in lexicon:
            score = lexicon[token]
            if negate_next:
                score = -score
            total += score
            negate_next = False
    return total


class SentimentScorer:
    """Scores both effort level (workout difficulty) and sentiment (mood) from run text."""

    def score_effort(self, text: str) -> str:
        """Classify perceived effort level (how hard the run felt).

        Returns:
            One of: "easy", "moderate", "hard", "struggled".
        """
        total = _score_with_lexicon(text, _EFFORT_LEXICON, _NEGATIONS)
        if total >= _EFFORT_THRESHOLDS["easy"]:
            return "easy"
        if total >= _EFFORT_THRESHOLDS["moderate"]:
            return "moderate"
        if total >= _EFFORT_THRESHOLDS["hard"]:
            return "hard"
        return "struggled"

    def score_sentiment(self, text: str) -> str:
        """Classify mood / how the user is feeling (not workout difficulty).

        Returns:
            One of: "positive", "neutral", "negative".
        """
        total = _score_with_lexicon(text, _SENTIMENT_LEXICON, _NEGATIONS)
        if total >= _SENTIMENT_THRESHOLDS["positive"]:
            return "positive"
        if total >= _SENTIMENT_THRESHOLDS["neutral"]:
            return "neutral"
        return "negative"

    def score(self, text: str) -> str:
        """Return effort level only. Kept for backward compatibility.

        Prefer score_effort() and score_sentiment() for new code.
        """
        return self.score_effort(text)
