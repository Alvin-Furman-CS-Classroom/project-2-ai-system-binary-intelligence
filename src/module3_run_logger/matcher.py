import re
from typing import Optional
import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "../../data/matcher_config.json")

with open(config_path, "r") as f:
    config = json.load(f)

CANONICAL_TERRAIN = config["canonical_terrain"]
CANONICAL_WORKOUT_TYPES = config["canonical_workout_types"]
_TERRAIN_KEYWORDS = config["terrain_keywords"]
_WORKOUT_KEYWORDS = config["workout_keywords"]





class EmbeddingMatcher:
    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model = None
        self._model_path = model_path
        self._model_loaded = False

    def match_terrain(self, text: str) -> str:
        if not self._has_any_keyword(text, _TERRAIN_KEYWORDS):
            return "road"
        return self._match(text, CANONICAL_TERRAIN, _TERRAIN_KEYWORDS, "road")

    def match_workout_type(self, text: str) -> str:
        # Hard rule: NxDIST notation always means intervals (e.g., 2x800m, 5x1km)
        if re.search(r"\d+\s*x\s*\d+", text, re.IGNORECASE):
            return "interval"

        miles = self._extract_miles(text)

        # Hard rule: short distances can't be long runs — unless text says "long run"
        if miles is not None and miles < 6.0:
            lower = text.lower()
            if "long run" in lower:
                pass  # let _match decide so "long run" keyword wins
            elif "recovery" in lower or "recover" in lower:
                return "recovery run"
            else:
                return "easy run"

        return self._match(text, CANONICAL_WORKOUT_TYPES, _WORKOUT_KEYWORDS, "easy run")

    def _match(
        self,
        text: str,
        canonical: list[str],
        keyword_map: dict[str, str],
        default: str,
    ) -> str:
        emb = self._embedding_match(text, canonical)
        if emb is not None:
            return emb
        return self._keyword_match(text, keyword_map, default)

    def _embedding_match(
        self, text: str, canonical: list[str]
    ) -> Optional[str]:
        model = self._load_model()
        if model is None:
            return None

        tokens = re.findall(r"[a-z]+", text.lower())
        tokens = [t for t in tokens if t in model.key_to_index]

        if not tokens:
            return None

        token_vecs = [model[t] for t in tokens]

        best_label = None
        best_score = -1.0

        for label in canonical:
            label_words = re.findall(r"[a-z]+", label.lower())
            label_words = [w for w in label_words if w in model.key_to_index]
            if not label_words:
                continue

            # Phrase vector = mean of label word vectors
            label_vec = sum(model[w] for w in label_words) / len(label_words)

            # Compute cosine similarities between label vector and each token vector
            sims = [
                float(model.cosine_similarities(label_vec, [tv])[0])
                for tv in token_vecs
            ]

            # Use top-3 similarities to reduce noise
            sims.sort(reverse=True)
            topk = sims[:3]
            score = sum(topk) / len(topk)

            if score > best_score:
                best_score = score
                best_label = label

        # Raised threshold from 0.05 → 0.20 to reduce false positives
        if best_label is not None and best_score > 0.20:
            return best_label

        return None

    def _keyword_match(
        self, text: str, keyword_map: dict[str, str], default: str
    ) -> str:
        lower = text.lower()
        tokens = set(re.findall(r"[a-z0-9]+", lower))

        # 1. Match multi-word phrases first (longest first to avoid subword conflicts)
        for keyword in sorted(keyword_map, key=len, reverse=True):
            if " " in keyword and keyword in lower:
                return keyword_map[keyword]

        # 2. Match single-word tokens exactly (prevents substring false matches)
        for keyword in sorted(keyword_map, key=len, reverse=True):
            if " " not in keyword and keyword in tokens:
                return keyword_map[keyword]

        return default

    def _load_model(self):
        if self._model_loaded:
            return self._model

        self._model_loaded = True  # Don't retry on failure

        try:
            import gensim.downloader as api
            from gensim.models import KeyedVectors

            if self._model_path:
                self._model = KeyedVectors.load_word2vec_format(
                    self._model_path, binary=True
                )
            else:
                # Lightweight model suitable for a course project (~66MB)
                self._model = api.load("glove-wiki-gigaword-50")

        except ImportError:
            # gensim not installed; keyword fallback will be used
            self._model = None
        except OSError:
            # Model file not found or download failed
            self._model = None
        except Exception:
            # Any other gensim/data error; degrade gracefully
            self._model = None

        return self._model

    # FIX: Added `self` parameter (was missing, caused crash when called as instance method)
    def _extract_miles(self, text: str) -> Optional[float]:
        t = text.lower()

        # Handle interval notation: NxDISTunit (e.g., "2x800m", "3x1km")
        m = re.search(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(m|km|mi|mile|miles)\b", t)
        if m:
            reps = float(m.group(1))
            dist = float(m.group(2))
            unit = m.group(3)
            if unit == "m":
                return (reps * dist) / 1609.344
            if unit == "km":
                return (reps * dist) * 0.621371
            return reps * dist

        # Handle standard distances with named units
        m = re.search(r"(\d+(?:\.\d+)?)\s*(mi|mile|miles|km)\b", t)
        if m:
            dist = float(m.group(1))
            if m.group(2) == "km":
                dist *= 0.621371
            return dist

        # Handle bare meter distances (e.g., "800m")
        m = re.search(r"(\d+(?:\.\d+)?)\s*m\b", t)
        if m:
            return float(m.group(1)) / 1609.344

        return None

    # FIX: Added `self` parameter (was missing, caused crash when called as instance method)
    def _has_any_keyword(self, text: str, keyword_map: dict[str, str]) -> bool:
        lower = text.lower()
        tokens = set(re.findall(r"[a-z0-9]+", lower))
        for kw in keyword_map:
            if " " in kw:
                if kw in lower:
                    return True
            else:
                if kw in tokens:
                    return True
        return False