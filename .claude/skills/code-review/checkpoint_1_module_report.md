# Checkpoint 1 — Module Rubric Report

**Module:** Module 1 (Safety Validator)  
**Scope:** `src/module1_safety_validator/`, `unit_tests/module1_safety_validator/`  
**Rubric:** AI System Module Rubric (Part 1: Source, Part 2: Testing)  
**Last updated:** After type validation, workout-type validation, severity constants, TypedDict, and README example.

---

## Summary

Module 1 is complete and aligned with the README specification. Inputs and outputs are clearly defined and implemented (runner profile + proposed workout → safety assessment with `safe`, `reason`, `alternative`, `recommendation`). Input validation (including type checks for profile and workout and workout-type allowlist) and experience-level checks run before inference. Return shape is documented via `ValidationResult` TypedDict; README includes a quick copy-paste example. Test suite is comprehensive (294 tests passing) with clear organization and documentation. Integration tests are not required for the first module.

---

## Findings (assessment per criterion)

### Specification Clarity  
**Score: Full marks (reflected in I/O and Documentation)**

- README module table specifies inputs (runner profile, proposed workout) and outputs (safety assessment dict).
- Validator and input_validation docstrings align with this spec. README “Running” section has a quick example for Module 1.

### Inputs / Outputs  
**Score: 3/3 (I/O Clarity)**

- **Inputs:** Runner profile (injuries, symptoms, weekly_mileage, experience_level, terrain, recovery, etc.) and proposed workout (type, distance, terrain). Validated by `validate_runner_profile` (including types and bounds) and `validate_workout_structure` (distance, terrain, workout type).
- **Outputs:** `safe` (bool), `reason` (str), `alternative` (dict or None), `recommendation` (str when no alternative). Documented via `ValidationResult` TypedDict; easy to verify programmatically and for grading.

### Dependencies  
**Score: N/A (Module 1 has no module dependencies)**

- Module 1 depends only on the standard library and internal packages. No external service or other project modules.

### Test Coverage  
**Score: 6/6 (Test Coverage and Design)**

- 294 unit tests across `test_validator`, `test_alternatives`, `test_inference`, `test_facts`, `test_rules`, `test_input_validation`, `test_experience_levels`.
- Covers core behavior, edge cases (invalid inputs, wrong types, multiple injuries, all terrains contraindicated), and error paths.
- Integration tests not required for first module; validator tests exercise the full pipeline.

### Documentation  
**Score: 4/4**

- Public functions have docstrings with Args, Returns, and often Examples.
- Type hints and `ValidationResult` TypedDict used consistently. Module-level docstrings and validator “Quick example” describe purpose and usage.
- Test modules and classes are named and documented clearly.

### Integration Readiness  
**Score: Addressed**

- Output format is stable and documented (`ValidationResult`); downstream modules can consume `safe`, `reason`, `alternative`, `recommendation`.
- Public API in `__init__.py` (`validate_workout`, `validate_workout_detailed`, `quick_validate`, `batch_validate`) supports integration.

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

## Overall Module 1 Mark (Source + Testing only)

| Section | Points | Max |
|---------|--------|-----|
| Part 1: Source Code | 27 | 27 |
| Part 2: Testing | 15 | 15 |
| **Total (Parts 1 & 2)** | **42** | **42** |

Participation requirement and Part 3 (GitHub) are not scored here.
