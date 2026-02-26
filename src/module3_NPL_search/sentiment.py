import re

# Words that flip sentiment of the next positive/negative word.
_NEGATIONS: set[str] = {
    "not", "never", "no",
    "didn't", "didn't", "didnt",
    "wasn't", "wasn't", "wasnt",
    "couldn't", "couldn't", "couldnt",
    "don't", "don't", "dont",
    "won't", "won't", "wont",
}

# Scored lexicon: positive scores → easy/good, negative → hard/struggled.
_LEXICON: dict[str, float] = {
    # Strong positive
    "great": 2.0,
    "excellent": 2.0,
    "strong": 2.0,
    "fresh": 2.0,
    "easy": 2.0,
    "effortless": 2.0,
    "flew": 2.0,
    "flying": 2.0,
    "crushed": 2.0,
    "comfortable": 1.5,
    "good": 1.5,
    "solid": 1.5,
    "smooth": 1.5,
    "light": 1.5,
    "energized": 1.5,
    "recovered": 1.5,
    "cruised": 1.5,
    "cruising": 1.5,
    "floated": 1.5,
    "floating": 1.5,
    "relaxed": 1.5,
    "controlled": 1.5,
    "powerful": 1.5,
    # Mild positive
    "okay": 0.5,
    "fine": 0.5,
    "decent": 0.5,
    "alright": 0.5,
    "manageable": 0.5,
    # Mild negative
    "tired": -1.0,
    "slow": -1.0,
    "sluggish": -1.0,
    "heavy": -1.0,
    "sore": -1.0,
    "tight": -1.0,
    "stiff": -1.0,
    "labored": -1.0,
    "laboured": -1.0,
    "fatigued": -1.0,
    "drained": -1.0,
    "flat": -1.0,
    # Strong negative
    "exhausted": -2.0,
    "dead": -2.0,
    "awful": -2.0,
    "terrible": -2.0,
    "struggled": -2.0,
    "struggle": -2.0,
    "struggling": -2.0,
    "dying": -2.0,
    "hurt": -1.5,
    "pain": -2.0,
    "painful": -2.0,
    "hard": -1.5,
    "tough": -1.5,
    "difficult": -1.5,
    "barely": -2.0,
    "couldnt": -1.5,
    "failed": -2.0,
    "bonked": -2.0,
    "bonk": -2.0,
    "wall": -1.5,
    "crawled": -2.0,
    "crawling": -2.0,
    "wrecked": -2.0,
    "destroyed": -2.0,
    "brutal": -2.0,
    "suffered": -2.0,
    "suffering": -2.0,
}

# Score thresholds for final category assignment.
_THRESHOLDS: dict[str, float] = {
    "easy": 1.5,       # score >= 1.5
    "moderate": 0.0,   # score >= 0.0
    "hard": -1.5,      # score >= -1.5
    # below -1.5 → struggled
}


class SentimentScorer:
    """Classifies perceived effort from a run description.

    Tokenizes the input, detects negation windows, sums lexicon scores,
    and maps the total to a categorical effort label.
    """

    def score(self, text: str) -> str:
        """Classify effort level from free-text run description.

        Args:
            text: Free-text run description.

        Returns:
            One of: "easy", "moderate", "hard", "struggled".
        """
        tokens = re.findall(r"[a-z']+", text.lower())
        total = 0.0
        negate_next = False

        for token in tokens:
            if token in _NEGATIONS:
                negate_next = True
                continue

            if token in _LEXICON:
                score = _LEXICON[token]
                if negate_next:
                    score = -score
                total += score
                negate_next = False
            # Non-lexicon words do NOT clear the negation flag,
            # so "didn't feel good" correctly negates "good".

        return self._categorize(total)

    def _categorize(self, score: float) -> str:
        """Map a numeric score to a categorical effort label.

        Args:
            score: Summed lexicon score.

        Returns:
            Effort category string.
        """
        if score >= _THRESHOLDS["easy"]:
            return "easy"
        if score >= _THRESHOLDS["moderate"]:
            return "moderate"
        if score >= _THRESHOLDS["hard"]:
            return "hard"
        return "struggled"