"""
Semantic matching using Word2Vec word embeddings and cosine similarity.

Maps informal runner vocabulary to canonical labels by comparing word
vectors. This implements the distributional semantics idea from the
course slides: words appearing in similar contexts will have similar
vectors, so "trail" and "dirt path" will both be close to the
canonical terrain label "trail".

Requires gensim and a downloaded Word2Vec model. Falls back to a
keyword lookup if the model is unavailable.

Example:
    >>> from module3_run_logger.matcher import EmbeddingMatcher
    >>> matcher = EmbeddingMatcher()
    >>> matcher.match_terrain("ran on the dirt path today")
    'trail'
    >>> matcher.match_workout_type("did my long run this morning")
    'long run'
"""

import re
from typing import Optional

# Canonical labels the system understands.
CANONICAL_TERRAIN: list[str] = ["road", "trail", "track", "treadmill", "grass"]

CANONICAL_WORKOUT_TYPES: list[str] = [
    "easy run",
    "long run",
    "tempo run",
    "interval",
    "recovery run",
    "race",
]

# Keyword fallback: maps surface words to canonical terrain.
_TERRAIN_KEYWORDS: dict[str, str] = {
    "trail": "trail",
    "trails": "trail",
    "dirt": "trail",
    "gravel": "trail",
    "cinder": "trail",
    "crushed gravel": "trail",
    "path": "trail",
    "forest": "trail",
    "woods": "trail",
    "single track": "trail",
    "singletrack": "trail",
    "track": "track",
    "oval": "track",
    "400m": "track",
    "treadmill": "treadmill",
    "dreadmill": "treadmill",
    "mill": "treadmill",
    "indoor": "treadmill",
    "belt": "treadmill",
    "grass": "grass",
    "field": "grass",
    "park": "grass",
    "turf": "grass",
    "road": "road",
    "pavement": "road",
    "street": "road",
    "sidewalk": "road",
    "asphalt": "road",
    "concrete": "road",
    "tarmac": "road",
    "paved": "road",
}

# Keyword fallback: maps workout words to canonical workout type.
_WORKOUT_KEYWORDS: dict[str, str] = {
    "long run": "long run",
    "long slow": "long run",
    "lsd": "long run",
    "long": "long run",
    "easy run": "easy run",
    "easy": "easy run",
    "base run": "easy run",
    "aerobic": "easy run",
    "jog": "easy run",
    "shakeout": "easy run",
    "recovery run": "recovery run",
    "recovery": "recovery run",
    "recover": "recovery run",
    "regeneration": "recovery run",
    "tempo run": "tempo run",
    "tempo": "tempo run",
    "threshold": "tempo run",
    "comfortably hard": "tempo run",
    "lactate": "tempo run",
    "cruise": "tempo run",
    "interval": "interval",
    "intervals": "interval",
    "repeat": "interval",
    "repeats": "interval",
    "speed": "interval",
    "fartlek": "interval",
    "strides": "interval",
    "vo2": "interval",
    "yasso": "interval",
    "race": "race",
    "marathon": "race",
    "half marathon": "race",
    "5k": "race",
    "10k": "race",
    "parkrun": "race",
}


class EmbeddingMatcher:
    """Matches informal running text to canonical labels using Word2Vec.

    Attempts to load a gensim Word2Vec model on first use. If the model
    is unavailable or a word has no vector, falls back to keyword matching.

    Args:
        model_path: Optional path to a local Word2Vec .bin or .gz file.
                    If None, attempts to load a small pre-trained model
                    via gensim's downloader.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model = None
        self._model_path = model_path
        self._model_loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match_terrain(self, text: str) -> str:
        """Identify the terrain type from a run description.

        Args:
            text: Free-text run description.

        Returns:
            Canonical terrain label. Defaults to "road" if nothing matches.
        """
        return self._match(text, CANONICAL_TERRAIN, _TERRAIN_KEYWORDS, "road")

    def match_workout_type(self, text: str) -> str:
        """Identify the workout type from a run description.

        Args:
            text: Free-text run description.

        Returns:
            Canonical workout type. Defaults to "easy run" if nothing matches.
        """
        return self._match(
            text, CANONICAL_WORKOUT_TYPES, _WORKOUT_KEYWORDS, "easy run"
        )

    # ------------------------------------------------------------------
    # Internal matching logic
    # ------------------------------------------------------------------

    def _match(
        self,
        text: str,
        canonical: list[str],
        keyword_map: dict[str, str],
        default: str,
    ) -> str:
        """Try embedding similarity first, fall back to keywords.

        Args:
            text: Input text to classify.
            canonical: List of canonical label strings.
            keyword_map: Fallback keyword-to-label mapping.
            default: Label to return if nothing matches.

        Returns:
            Best matching canonical label.
        """
        # Try embedding-based matching first.
        embedding_result = self._embedding_match(text, canonical)
        if embedding_result is not None:
            return embedding_result

        # Fall back to keyword matching.
        return self._keyword_match(text, keyword_map, default)

    def _embedding_match(
        self, text: str, canonical: list[str]
    ) -> Optional[str]:
        """Find the canonical label most similar to words in text via cosine similarity.

        Loads the Word2Vec model lazily on first call. For each word in the
        text that has a vector, computes cosine similarity against each
        canonical label's vector. Returns the canonical label with the
        highest average similarity score.

        Args:
            text: Input text.
            canonical: List of canonical labels to compare against.

        Returns:
            Best matching label, or None if the model is unavailable or
            no words in text have vectors.
        """
        model = self._load_model()
        if model is None:
            return None

        tokens = re.findall(r"[a-z]+", text.lower())
        best_label = None
        best_score = -1.0

        for label in canonical:
            # For multi-word labels, use the last word as the anchor
            # (e.g. "long run" → "run", "easy run" → "run").
            label_word = label.split()[-1]
            if label_word not in model:
                continue

            scores = []
            for token in tokens:
                if token in model:
                    try:
                        sim = model.similarity(token, label_word)
                        scores.append(sim)
                    except Exception:
                        pass

            if scores:
                avg = sum(scores) / len(scores)
                if avg > best_score:
                    best_score = avg
                    best_label = label

        # Only return if similarity is meaningfully above zero.
        if best_label is not None and best_score > 0.05:
            return best_label
        return None

    def _keyword_match(
        self, text: str, keyword_map: dict[str, str], default: str
    ) -> str:
        """Match text against keyword map, longest match first.

        Args:
            text: Input text.
            keyword_map: Mapping from keyword phrase to canonical label.
            default: Return value if no keyword matches.

        Returns:
            Canonical label or default.
        """
        lower = text.lower()
        # Sort by length descending so longer phrases match before subwords.
        for keyword in sorted(keyword_map, key=len, reverse=True):
            if keyword in lower:
                return keyword_map[keyword]
        return default

    def _load_model(self):
        """Lazily load the Word2Vec model.

        Tries the provided model path first, then falls back to gensim's
        built-in downloader for the lightweight glove-wiki-gigaword-50 model.

        Returns:
            Loaded KeyedVectors object, or None if loading fails.
        """
        if self._model_loaded:
            return self._model

        self._model_loaded = True  # Don't retry on failure.

        try:
            import gensim.downloader as api
            from gensim.models import KeyedVectors

            if self._model_path:
                self._model = KeyedVectors.load_word2vec_format(
                    self._model_path, binary=True
                )
            else:
                # Lightweight model suitable for a course project (~66MB).
                self._model = api.load("glove-wiki-gigaword-50")

        except ImportError:
            # gensim not installed; keyword fallback will be used.
            self._model = None
        except OSError:
            # Model file not found, unreadable, or download failed.
            self._model = None
        except Exception:
            # Robustness: e.g. gensim API or data error during load.
            # Keyword fallback so the app keeps working.
            self._model = None

        return self._model