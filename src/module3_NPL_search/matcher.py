# import re
# from typing import Optional


# CANONICAL_TERRAIN: list[str] = ["road", "trail", "track", "treadmill", "grass"]

# CANONICAL_WORKOUT_TYPES: list[str] = [
#     "easy run",
#     "long run",
#     "tempo run",
#     "interval",
#     "recovery run",
#     "race",
# ]

# _TERRAIN_KEYWORDS: dict[str, str] = {
#     "trail": "trail",
#     "trails": "trail",
#     "dirt": "trail",
#     "gravel": "trail",
#     "cinder": "trail",
#     "crushed gravel": "trail",
#     "path": "trail",
#     "forest": "trail",
#     "woods": "trail",
#     "single track": "trail",
#     "singletrack": "trail",
#     "track": "track",
#     "oval": "track",
#     "400m": "track",
#     "treadmill": "treadmill",
#     "dreadmill": "treadmill",
#     "mill": "treadmill",
#     "indoor": "treadmill",
#     "belt": "treadmill",
#     "grass": "grass",
#     "field": "grass",
#     "park": "grass",
#     "turf": "grass",
#     "road": "road",
#     "pavement": "road",
#     "street": "road",
#     "sidewalk": "road",
#     "asphalt": "road",
#     "concrete": "road",
#     "tarmac": "road",
#     "paved": "road",
# }

# _WORKOUT_KEYWORDS: dict[str, str] = {
#     "long run": "long run",
#     "long slow": "long run",
#     "lsd": "long run",
#     "long": "long run",
#     "easy run": "easy run",
#     "easy": "easy run",
#     "base run": "easy run",
#     "aerobic": "easy run",
#     "jog": "easy run",
#     "shakeout": "easy run",
#     "recovery run": "recovery run",
#     "recovery": "recovery run",
#     "recover": "recovery run",
#     "regeneration": "recovery run",
#     "tempo run": "tempo run",
#     "tempo": "tempo run",
#     "threshold": "tempo run",
#     "comfortably hard": "tempo run",
#     "lactate": "tempo run",
#     "cruise": "tempo run",
#     "interval": "interval",
#     "intervals": "interval",
#     "repeat": "interval",
#     "repeats": "interval",
#     "speed": "interval",
#     "fartlek": "interval",
#     "strides": "interval",
#     "vo2": "interval",
#     "yasso": "interval",
#     "race": "race",
#     "marathon": "race",
#     "half marathon": "race",
#     "5k": "race",
#     "10k": "race",
#     "parkrun": "race",
# }


# class EmbeddingMatcher:
#     def __init__(self, model_path: Optional[str] = None) -> None:
#         self._model = None
#         self._model_path = model_path
#         self._model_loaded = False

#     def match_terrain(self, text: str) -> str:
#         return self._match(text, CANONICAL_TERRAIN, _TERRAIN_KEYWORDS, "road")

#     def match_workout_type(self, text: str) -> str:
#         return self._match(
#             text, CANONICAL_WORKOUT_TYPES, _WORKOUT_KEYWORDS, "easy run")

#     # match function used by both terrain and workout type, tries embedding first then fall bac to keyword matching
#     def _match(self,text: str, canonical: list[str],keyword_map: dict[str, str],default: str,) -> str:
#         # Try embedding-based matching first.
#         embedding_result = self._embedding_match(text, canonical)
#         if embedding_result is not None:
#             return embedding_result

#         # Fall back to keyword matching.
#         return self._keyword_match(text, keyword_map, default)

#     def _embedding_match(
#         self, text: str, canonical: list[str]
#     ) -> Optional[str]:
        
#         model = self._load_model()
#         if model is None:
#             return None

#         tokens = re.findall(r"[a-z]+", text.lower())
#         best_label = None
#         best_score = -1.0

#         for label in canonical:
#             # For multi-word labels, use the last word as the anchor
#             # (e.g. "long run" → "run", "easy run" → "run").
#             label_word = label.split()[-1]
#             if label_word not in model:
#                 continue

#             scores = []
#             for token in tokens:
#                 if token in model:
#                     try:
#                         sim = model.similarity(token, label_word)
#                         scores.append(sim)
#                     except Exception:
#                         pass

#             if scores:
#                 avg = sum(scores) / len(scores)
#                 if avg > best_score:
#                     best_score = avg
#                     best_label = label

#         # Only return if similarity is meaningfully above zero.
#         if best_label is not None and best_score > 0.05:
#             return best_label
#         return None

#     def _keyword_match(
#         self, text: str, keyword_map: dict[str, str], default: str
#     ) -> str:
       
#         lower = text.lower()
#         # Sort by length descending so longer phrases match before subwords.
#         for keyword in sorted(keyword_map, key=len, reverse=True):
#             if keyword in lower:
#                 return keyword_map[keyword]
#         return default

#     def _load_model(self):
      
#         if self._model_loaded:
#             return self._model

#         self._model_loaded = True 

#         try:
#             import gensim.downloader as api
#             from gensim.models import KeyedVectors

#             if self._model_path:
#                 self._model = KeyedVectors.load_word2vec_format(
#                     self._model_path, binary=True
#                 )
#             else:
#                 # Lightweight model suitable for a course project (~66MB).
#                 self._model = api.load("glove-wiki-gigaword-50")

#         except ImportError:
#             self._model = None
#         except OSError:
#             self._model = None
#         except Exception:
#             self._model = None

#         return self._model

import re
from typing import Optional
import json
import os

#FIX: Added imports for gensim and json (used in embedding matcher and config loading) it is in data folder, so we need to load it here
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

        # Hard rule: short distances can't be long runs
        if miles is not None and miles < 6.0:
            lower = text.lower()
            if "recovery" in lower or "recover" in lower:
                return "recovery run"
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