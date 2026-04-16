# Checkpoint 2 — Module Rubric Report

**Module:** Module 3 (Run Logger)  
**Scope:** `src/module3_run_logger/`, `unit_tests/module3_run_logger/`, `integration_tests/module3_integration/`  
**Rubric:** AI System Module Rubric (Part 1: Source, Part 2: Testing)  
**Last updated:** 2026-04-16 (checkpoint preparation re-run).  
**Test run (Module 3–scoped):** 113 passed (unit: 99, integration: 14). **Full project:** **945** passed.

---

## Summary

Module 3 is complete and aligned with the README specification. Parsed output now includes both **sentiment** (mood: positive/neutral/negative) and **effort** (workout difficulty: easy/moderate/hard/struggled). Inputs and outputs are clearly defined. NLP is engaged via regex/n-gram extraction, config-driven keyword matching with optional Word2Vec fallback, and dual sentiment/effort lexicons with negation. All 113 tests pass. Documentation and I/O are clear; unit and integration tests are comprehensive.

---

## Part 1: Source Code Review (27 pts)

| Criterion | Score | Justification |
|-----------|-------|----------------|
| **1.1 Functionality (8)** | 8 | All features work: parse_run (type, distance, pace, terrain, sentiment, effort, notes), log_run, get_run_history. Edge cases (no distance, empty file, invalid dates, n&gt;runs) handled. No crashes. |
| **1.2 Code Elegance and Quality (7)** | 7 | Elegance average 4.0. Clear structure, naming, abstraction. |
| **1.3 Documentation (4)** | 4 | Module and class docstrings; public functions have Args/Returns (and Raises where relevant). Type hints consistent. Sentiment/effort distinction documented in `__init__.py` and `sentiment.py`. |
| **1.4 I/O Clarity (3)** | 3 | Inputs: free-text str, optional store_path. Outputs: parsed dict (all keys documented), run ID, list of run entries. Easy to verify. |
| **1.5 Topic Engagement (5)** | 5 | NLP: regex/n-gram patterns (distance, pace), config-driven keyword matching, optional Word2Vec similarity, sentiment lexicons with negation. Clear engagement with extraction and classification. |
| **Part 1 total** | **27** | **27** |

---

## Part 2: Testing Review (15 pts)

| Criterion | Score | Justification |
|-----------|-------|----------------|
| **2.1 Test Coverage and Design (6)** | 6 | 99 unit tests (parser, extractor, matcher, sentiment, store); 14 integration tests (plan→NL→parse, M1 validation, log/history, store isolation). Core behaviour, edge cases, and errors covered; clear unit vs integration split. |
| **2.2 Test Quality and Correctness (5)** | 5 | All 113 tests pass. Tests assert behaviour (parsed keys, effort/sentiment values, store IDs, history order). Isolation via tmp_path and explicit store_path. |
| **2.3 Test Documentation and Organization (4)** | 4 | Tests grouped by class (e.g. TestOutputStructure, TestSentimentMood); names descriptive; docstrings where purpose is non-obvious. |
| **Part 2 total** | **15** | **15** |

---

## Part 3: GitHub Practices (8 pts)

Not assessed in this report; depends on commit history and collaboration.

---

## Scores Summary

| Section | Points | Max |
|---------|--------|-----|
| Part 1: Source Code | 27 | 27 |
| Part 2: Testing | 15 | 15 |
| **Total (Parts 1 & 2)** | **42** | **42** |

Participation requirement and Part 3 (GitHub) are not scored here.
