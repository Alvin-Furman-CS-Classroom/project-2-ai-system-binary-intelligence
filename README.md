# Long Run: AI Marathon Training System for Beginners

## Contents

- [Overview](#overview)
- [Team](#team)
- [Proposal](#proposal)
- [Module plan](#module-plan)
- [System architecture](#system-architecture-data-flow)
- [Repository layout](#repository-layout)
- [Setup](#setup)
- [Running](#running)
- [Testing](#testing)
- [Checkpoint log](#checkpoint-log)
- [Required workflow (agent-guided)](#required-workflow-agent-guided)
- [References](#references)

## Overview

Novice runners often struggle with pacing, training volume, and progression without professional guidance. Many beginners either follow generic plans that ignore their fitness level, push too hard and risk injury, or lose motivation when they don't see improvement. Long Run addresses these challenges by providing personalized coaching that adapts to each runner's constraints, goals, and progress.

The system validates workout safety based on user limitations and available terrain, generates training plans tailored to race goals and running environment, logs run performance through natural language input, adapts training loads based on results, and predicts race readiness timelines. This creates a complete coaching experience from a runner's first easy jog through race day preparation.

Implementing a marathon training system requires multiple AI techniques because coaching involves diverse intelligent behaviors. Safety validation requires logical reasoning about injury risk, recovery needs, and terrain suitability. Plan generation requires searching through possible workout combinations across different surfaces. Run logging requires understanding informal user descriptions. Motivation management requires strategic decision-making about when to push and when to rest. Progression requires learning each runner's response patterns. Race prediction requires modeling trends from historical data.

The system comprises six modules that share a central user profile and training history database. Early modules establish safety constraints and baseline plans, while later modules learn from accumulated training data to adapt and predict outcomes.

## Team

- Member 1: Tanya Masvimbo
- Member 2: Mengsrun Nit

## Proposal

See the approved project proposal in PROPOSAL.md for complete system design details.

## Module Plan

The implemented system includes **six modules** (see course schedule in the last column). Module 6 (race prediction) is the optional supervised-learning capstone. Summary:

| Module | Topic(s) | Inputs | Outputs | Depends On | Checkpoint |
| ------ | -------- | ------ | ------- | ---------- | ---------- |
| 1 | Propositional Logic (Knowledge Bases, Inference, Chaining) | Runner profile dict with injuries, symptoms, training load, recovery status, experience level, environment, available terrain, and proposed workout | Safety assessment dict with safe (bool), reason (str), alternative workout (dict or None), and recommendation (str) if no alternative exists | None | Checkpoint 1 (Feb 11) |
| 2 | Search (A*, Heuristics, State-Space Search) | Config dict: goal, race_date, days_per_week, current_weekly_miles, experience, available_terrain; optional validate_fn and runner_profile for safety checks | Plan result dict with success (bool), plan (list of week dicts: week, total_miles, long_run, workouts), total_weeks, total_penalty, search_stats, rationale, errors | Module 1 (optional) | Checkpoint 1 (Feb 11) |
| 3 | NLP (regex/n-grams, distributional semantics, sentiment) | Free-text run description (str); optional store_path for log_run / get_run_history | parse_run: dict (type, distance, pace_minutes, terrain, sentiment, effort, notes). log_run: run ID (str). get_run_history: list of run entry dicts | None (integrates with M1/M2 for validation and plan alignment) | Checkpoint 2 (Feb 26) |
| 4 | Game Theory (Sequential Games, Nash-like strategy selection) | Context dict: current_streak, recent_sentiments, terrain_last_week, adherence_percent, days_to_race | Strategy dict with strategy (str), message_tone (str), reasoning (str); detailed variant also returns per-strategy scores and inferred runner state | Module 3 (uses sentiment / history) | Checkpoint 3 (Mar 19) |
| 5 | Reinforcement Learning (MDP, Q-learning, value updates) | Context dict: workout_type, terrain, fatigue_score, history (runs with distance, pace, terrain, sentiment); optional motivation (Module 4: streak, sentiments, terrain_last_week, adherence_percent, days_to_race); optional q_table_path | adapt_progression: next_distance, target_pace, suggested_terrain, confidence, reasoning; detailed adds Q snapshot; train_on_run for online Q-updates | Modules 3 & 4 | Checkpoint 4 (Apr 2) |
| 6 (optional) | Supervised Learning (linear / logistic regression, metrics) | Runner snapshot: ``history`` (Module 3–style runs), ``age``, ``goal_race`` (distance, target_time, terrain); optional ``experience_level``, ``days_to_race``, ``adherence_percent`` — or use ``pipeline_predict_race_readiness(profile)`` | ``predicted_finish``, ``confidence_interval``, ``readiness_score``, ``recommendations`` | Modules 3 & 5 (history); pipeline ties profile + log | Checkpoint 5 (Apr 16) |

## System architecture (data flow)

Modules stay **independent packages** under ``src/``; the **pipeline** (``src/pipeline/``) is the glue layer. A typical flow:

1. **Profile** — ``data/runner_profile.json`` holds planner goals, Module 1 runner fields, and paths (run log, optional Q-table). Defaults and schema version live in ``src/pipeline/constants.py``.
2. **Plan** — Module 2 generates weeks of workouts; Module 1 can validate workouts when a ``validate_fn`` is wired in.
3. **Log** — Module 3 parses natural-language runs and stores structured entries; history feeds Module 4–6.
4. **Motivation** — Module 4 uses streaks, sentiment, and terrain context from the log.
5. **Progression** — Module 5 (Q-learning) suggests the next distance/pace/terrain; optional adherence vs plan is computed in ``src/pipeline/adherence.py``.
6. **Race prediction** — Module 6 builds a tabular snapshot from profile + history and outputs finish time and readiness.

Import orchestration helpers with ``from src.pipeline import ...`` (see examples below). For a full list, see ``src/pipeline/orchestrator.py``.

## Repository Layout

```
project-root/
├── src/                              # Modules 1–6 + src/pipeline/ (orchestration)
├── unit_tests/                       # Mirrors src/ (plus unit_tests/pipeline/)
├── integration_tests/                # Cross-module tests (e.g. module2_integration/)
├── checkpoints/                      # Rubric / checkpoint notes (e.g. project_module_report.md)
├── data/                             # Profile, configs, logs (some paths gitignored)
├── calibrate_from_real_data.py       # Module 6 calibration utility (repo root)
├── PROPOSAL.md                       # Approved system design
├── AGENTS.md                         # Agent / contributor instructions
├── requirements.txt
└── README.md
```

Rubric-based review skill: `.claude/skills/code-review/SKILL.md`.

## Setup

Create a virtual environment (recommended), then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Use the **same interpreter** for `pip` and `pytest`. Dependencies include **pytest**, **NumPy**, and **scikit-learn** (Module 6 and tests). Modules 1–2 rely primarily on the standard library at runtime. No environment variables are required for the defaults in `src/pipeline/constants.py`.

## Running

**Module 1 (safety validator):**
```python
from src.module1_safety_validator import validate_workout
profile = {"weekly_mileage": 20, "experience_level": "intermediate", "hydrated": True, "proper_footwear": True, "weather": "normal", "rest_days_this_week": 2, "days_trained_this_week": 3, "fully_recovered": True, "sleep_quality": "good", "available_terrain": ["road", "track"]}
workout = {"type": "long run", "distance": 10, "terrain": "road"}
result = validate_workout(profile, workout)  # {"safe": bool, "reason": str, "alternative": ...}
```

**Module 3 (run logger):**
```python
from src.module3_run_logger import parse_run, log_run, get_run_history
result = parse_run("easy 5 miles on the road, felt great")
# result: type, distance, pace_minutes, terrain, sentiment, effort, notes
run_id = log_run("long run 10 miles on track", store_path="data/run_log.json")
recent = get_run_history(n=5, store_path="data/run_log.json")
```

**Module 5 (adaptive progression):**
```python
from src.module5_adaptive_progression import adapt_progression

result = adapt_progression({
    "workout_type": "easy run",
    "terrain": "road",
    "fatigue_score": 0.3,
    "history": [{"distance": 5, "pace": 9.0, "terrain": "road", "sentiment": "positive"}],
    # Optional: Module 4 motivation context (validated by Module 4 rules)
    "motivation": {
        "current_streak": 8,
        "recent_sentiments": ["good", "neutral"],
        "terrain_last_week": ["road", "trail"],
        "adherence_percent": 82,
        "days_to_race": 40,
    },
})
# result: next_distance, target_pace, suggested_terrain, confidence, reasoning
```

**Module 6 (race readiness — requires `numpy`, `scikit-learn`):**
```python
from src.module6_race_predictor import predict_race_readiness

out = predict_race_readiness({
    "age": 34,
    "experience_level": "intermediate",
    "days_to_race": 40,
    "adherence_percent": 85,
    "history": [
        {"date": "2026-01-01", "distance": 6, "pace": 9.0, "terrain": "road", "sentiment": "positive"},
    ],
    "goal_race": {"distance": "marathon", "target_time": "4:15:00", "terrain": "road"},
})
# out: predicted_finish, confidence_interval, readiness_score, recommendations
```

Training uses **from-scratch** mini-batch gradient descent for linear and logistic regression; **scikit-learn** is only used for feature scaling (`StandardScaler`). The synthetic label weights were informed by real runners in `data/CalibrationData.csv` (see `calibrate_from_real_data.py` at repo root). Models use **average training pace** (from run history) as an explicit feature alongside volume and demographics. If you have an older local `data/module6/` synthetic CSV from before that column existed, delete the CSV and `module6_models.pkl` so training regenerates.

**Pipeline (race prediction from profile + run log):**
```python
from src.pipeline import load_runner_profile, pipeline_predict_race_readiness

profile = load_runner_profile("data/runner_profile.json")
profile["age"] = 32
profile["race_goal"] = {"target_time": "4:30:00", "terrain": "road"}
result = pipeline_predict_race_readiness(profile, module6_dir="data/module6")
```

## Testing

- **Unit tests** (`unit_tests/`): Parallel to `src/` (`module1_safety_validator/`, …, `module6_race_predictor/`, plus `pipeline/`). Short scope notes: `unit_tests/module6_race_predictor/README.md`, `unit_tests/pipeline/README.md`.
- **Integration tests** (`integration_tests/`): Cross-module flows (e.g. `module2_integration/`, `module3_integration/`, `module4_integration/`, `module5_integration/`, `module6_integration/`).

From the **repository root**, run the full suite (recommended):

```bash
PYTHONPATH=. pytest
```

Other useful invocations:

```bash
PYTHONPATH=. pytest unit_tests/ -q
PYTHONPATH=. pytest integration_tests/ -q
```

No external test datasets are required for CI; tests use in-memory configs and temporary paths. **Module 6** can auto-generate a synthetic CSV and train models under `data/module6/` on first use (that directory is gitignored). Latest full run: **945** tests passing (run locally to confirm).

**Project rubric notes** (self-assessment): see `checkpoints/project_module_report.md` and `checkpoints/project_elegance_report.md`.

## Checkpoint log

Indicative tracking (adjust dates and status to match your syllabus and submissions):

| Checkpoint | Modules / focus | Artifacts |
| ---------- | ----------------- | --------- |
| 1 | Safety + search (M1–M2) | `src/module1_safety_validator/`, `src/module2_plan_generator/` |
| 2 | NLP run logger (M3) | `src/module3_run_logger/`; `integration_tests/module3_integration/` |
| 3 | Motivation / game theory (M4) | `checkpoints/checkpoint_3_*_report.md` |
| 4 | Adaptive progression (M5) | `src/module5_adaptive_progression/`; `integration_tests/module5_integration/` |
| 5 | Race predictor (M6) | `checkpoints/checkpoint_5_*_report.md`; `integration_tests/module6_integration/` |

**Whole system:** run `PYTHONPATH=. pytest` from repo root (945 tests at last update). Optional self-assessment writeups: `checkpoints/project_module_report.md`, `checkpoints/project_elegance_report.md`.

## Required Workflow (Agent-Guided)

Before each module:

1. Write a short module spec in this README (inputs, outputs, dependencies, tests).
2. Ask the agent to propose a plan in "Plan" mode.
3. Review and edit the plan. You must understand and approve the approach.
4. Implement the module in `src/`.
5. Unit test the module, placing tests in `unit_tests/` (parallel structure to `src/`).
6. For modules beyond the first, add integration tests in `integration_tests/` (new subfolder per module).
7. Run a rubric review using the code-review skill at `.claude/skills/code-review/SKILL.md`.

Keep `AGENTS.md` updated with your module plan, constraints, and links to APIs/data sources.

## References

**Libraries**

- Python 3 (standard library only for Module 1: `dataclasses`, `typing`, `datetime`)
- pytest 9.x (testing; see `requirements.txt`)

**APIs / datasets**

- None for Module 1.

**References**

Girardi, M. (2017). Marathon time predictions [Dataset]. Kaggle. https://www.kaggle.com/datasets/girardi69/marathon-time-predictions

Hospital for Special Surgery. "Injury Prevention for Marathon Runners." *HSS*, https://www.hss.edu/article_injury-prevention-marathon-runners.asp.

Marathon Handbook. "The 12 Rules of Marathon Training." *Marathon Handbook*, https://marathonhandbook.com/the-12-rules-of-marathon-training/.

Mayo Clinic Health System. "Speaking of Health." *Mayo Clinic Health System*, https://www.mayoclinichealthsystem.org/hometown-health/speaking-of-health/.

Physical Therapy & Sports Medicine Center. "Ready to Run: Key Strategies to Get Started Running Safely." *PTSMC*, https://www.ptsmc.com/ready-to-run-key-strategies-to-get-started-running-safely/.

Running Lifestyle Media. "9 Guidelines on Writing a Running Training Plan." *Running Lifestyle*, https://running-lifestyle.com/9-guidelines-on-writing-a-running-training-plan/.

Therapeutic Associates Physical Therapy. "10 Laws of Preventing Running Injuries." *Therapeutic Associates*, https://www.therapeuticassociates.com/10-laws-of-preventing-running-injuries/.

VCU Health. "How Runners Can Prevent Injury." *VCU Health*, https://www.vcuhealth.org/news/how-runners-can-prevent-injury.
