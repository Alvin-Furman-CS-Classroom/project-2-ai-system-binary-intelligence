# Checkpoint 2 — Module Rubric Report

**Module:** Module 3 (Run Logger)  
**Scope:** `src/module3_run_logger/`, `unit_tests/module3_run_logger/`, `integration_tests/module3_integration/`  
**Rubric:** AI System Module Rubric (Part 1: Source, Part 2: Testing)  
**Last updated:** After Module 3 completion (parser, extractor, matcher, sentiment, store; unit and integration tests).  
**Test run:** 109 passed (unit: 95, integration: 14).

---

## Summary

Module 3 is complete and aligned with the README specification. Inputs and outputs are clearly defined (free-text run description → parsed dict; log_run → run ID; get_run_history → list of run entries). NLP is engaged via regex/n-gram extraction, distributional semantics (Word2Vec + keyword fallback), and weighted sentiment lexicon with negation. Documentation and I/O are clear; unit and integration tests are comprehensive and passing.

---

## Findings (assessment per criterion)

### Specification Clarity  
**Score: Full marks (reflected in I/O and Documentation)**

- README module table specifies inputs (free-text str, optional store_path) and outputs (parse_run dict, log_run ID, get_run_history list).
- Module and function docstrings align with this spec. README “Running” section has an example for Module 3.

### Inputs / Outputs  
**Score: 3/3 (I/O Clarity)**

- **Inputs:** Free-text run description (str); optional `store_path` for `log_run` and `get_run_history`. Parser validates (raises ValueError for empty/non-string).
- **Outputs:** `parse_run` → dict (type, distance, pace_minutes, terrain, sentiment, notes); `log_run` → run ID str (e.g. run_001); `get_run_history` → list of run entry dicts (most recent last). Easy to verify programmatically and for grading.

### Dependencies  
**Score: N/A (Module 3 has no required module dependencies)**

- Module 3 uses standard library plus optional gensim (keyword fallback when unavailable). Integrates with M1/M2 in integration tests; no hard dependency on other project modules for core behaviour.

### Test Coverage  
**Score: 6/6 (Test Coverage and Design)**

- 95 unit tests across `test_parser`, `test_extractor`, `test_matcher`, `test_sentiment`, `test_store` (structure, examples, edge cases, errors).
- 14 integration tests in `module3_integration`: plan→NL→parse (M1+M2+M3), parsed run→M1 validation, log_run/get_run_history, M3 when plan blocked, store isolation, history n > runs.
- Core behaviour, edge cases, and error conditions covered; clear distinction between unit and integration.

### Documentation  
**Score: 4/4**

- Module and class docstrings with purpose and examples. Public functions have Args, Returns, Raises where applicable.
- Type hints used consistently. Inline comments for non-obvious logic (negation flag, next_id preservation, concurrency, matcher fallback).
- Test classes and methods are named and documented clearly.

### Integration Readiness  
**Score: Addressed**

- Output format is stable and documented; Module 5/6 can consume run history. Parsed dict shape (type, distance, pace_minutes, terrain, sentiment, notes) is fixed.
- Public API in `__init__.py` (`parse_run`, `log_run`, `get_run_history`, `RunLogParser`, `RunLogStore`). Integration tests demonstrate M1+M2+M3 pipelines.

---

## Scores Summary (AI System Rubric)

### Part 1: Source Code (27 pts)

| Criterion | Points | Max |
|-----------|--------|-----|
| 1.1 Functionality | 8 | 8 |
| 1.2 Code Elegance and Quality | 7 | 7 |
| 1.3 Documentation | 4 | 4 |
| 1.4 I/O Clarity | 3 | 3 |
| 1.5 Topic Engagement | 5 | 5 |
| **Part 1 total** | **27** | **27** |

### Part 2: Testing (15 pts)

| Criterion | Points | Max |
|-----------|--------|-----|
| 2.1 Test Coverage and Design | 6 | 6 |
| 2.2 Test Quality and Correctness | 5 | 5 |
| 2.3 Test Documentation and Organization | 4 | 4 |
| **Part 2 total** | **15** | **15** |

### Part 3: GitHub Practices (8 pts)

Not assessed in this report; depends on commit history and collaboration.

---

## Overall Module 3 Mark (Source + Testing only)

| Section | Points | Max |
|---------|--------|-----|
| Part 1: Source Code | 27 | 27 |
| Part 2: Testing | 15 | 15 |
| **Total (Parts 1 & 2)** | **42** | **42** |

Participation requirement and Part 3 (GitHub) are not scored here.
