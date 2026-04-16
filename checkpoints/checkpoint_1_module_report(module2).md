# Checkpoint 2 — Module Rubric Report

**Modules:** Module 1 (Safety Validator) + Module 2 (Training Plan Generator)  
**Scope:** `src/`, `unit_tests/`, `integration_tests/`  
**Rubric:** [AI System Module Rubric](https://csc-343.path.app/projects/project-2-ai-system/ai-system.rubric.md)  
**Last updated:** 2026-04-16 (checkpoint preparation re-run; full suite **945** tests green).

---

## Summary

Checkpoint 2 is complete and aligned with the README specification. Module 2 adds the plan generator (A* search, constraints, heuristics) with clear inputs (config: goal, race_date, days_per_week, current_weekly_miles, experience, available_terrain; optional validate_fn and runner_profile) and outputs (success, plan with weekly total_miles/long_run/workouts, total_weeks, total_penalty, search_stats, rationale, errors). Integration with Module 1 is implemented (validate_fn, critical-safety block). **Full project suite:** **945** tests pass (2026-04-16); historical note — previously reported **537** when fewer modules were present. Integration tests in `integration_tests/module2_integration/` cover the full Module 1 → Module 2 pipeline: plan structure, every-workout safety, critical-safety blocking, advisory notes, generate_plan_detailed, experience levels and terrain, and edge cases. The README module table is filled in for Module 2.

---

## Findings (assessment per criterion)

### Specification Clarity  
**Score: Full marks (reflected in I/O and Documentation)**

- README module table now specifies Module 2: topic (Search: A*, Heuristics, State-Space Search), inputs, outputs, and dependency on Module 1 (optional).
- Planner and module docstrings align with this spec; demo shows full plan with weekly_total and long_run.

### Inputs / Outputs  
**Score: 3/3 (I/O Clarity)**

- **Module 1:** Unchanged: runner profile + proposed workout → safety assessment (safe, reason, alternative, recommendation).
- **Module 2:** Config dict (goal, race_date, days_per_week, current_weekly_miles, experience, available_terrain); optional validate_fn and runner_profile. Output: success, plan (list of week dicts with week, total_miles, long_run, workouts), total_weeks, total_penalty, search_stats, rationale, errors. Easy to verify (e.g. via demo or unit tests).

### Dependencies  
**Score: Addressed**

- Module 2 optionally depends on Module 1: when validate_fn and runner_profile are provided, every candidate workout is safety-checked; critical severity blocks plan generation. No external services.

### Test Coverage  
**Score: 6/6 (Test Coverage and Design)**

- **Unit tests:** 518 across both modules (Module 1: validator, inference, facts, rules, alternatives, input validation, experience levels; Module 2: planner, search, states, actions, constraints, heuristics, input validation). Core behavior, edge cases, and error paths covered.
- **Integration tests:** 19 tests in `integration_tests/module2_integration/` using the real Module 1 `validate_workout`: full pipeline, plan structure, every-workout safety validation, critical-safety blocking (e.g. chest_pain), advisory notes, generate_plan_detailed, experience/terrain variants, and edge cases. Clear distinction between unit and integration tests.

### Documentation  
**Score: 4/4**

- Public functions have docstrings with Args, Returns, and Examples (planner, search, constraints, states, etc.). Type hints used consistently. Module-level docstrings and README Running section support usage.
- Test modules and classes are named and documented clearly.

### Integration Readiness  
**Score: Addressed**

- Module 2 output format is stable and documented. Downstream modules can consume plan, rationale, and search_stats.
- Module 1 integration: generate_plan(config, validate_fn=validate_workout, runner_profile=profile) is documented in Module 2 __init__.py and exercised in both unit tests and integration tests.

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

| Criterion | Points | Max |
|-----------|--------|-----|
| 3.1 Commit Quality and History | 3 | 4 |
| 3.2 Collaboration Practices | 3 | 4 |
| **Part 3 total** | **6** | **8** |

*Part 3 not verifiable from file snapshot alone; assumes meaningful commits and use of branches/PRs.*

---

## Overall Checkpoint 2 Score

| Section | Points | Max |
|---------|--------|-----|
| Part 1: Source Code | 27 | 27 |
| Part 2: Testing | 15 | 15 |
| Part 3: GitHub Practices | 6 | 8 |
| **Total** | **48** | **50** |

**Percentage: 96%.**

Participation requirement must be satisfied separately (commit history evidence).

---

## Action Items

- [x] Integration tests added in `integration_tests/module2_integration/` (19 tests, full Module 1 → Module 2 pipeline).
- [ ] Confirm commit history and PR usage meet participation and collaboration expectations.
