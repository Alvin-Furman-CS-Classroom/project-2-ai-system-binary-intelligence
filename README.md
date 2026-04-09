# Long Run: AI Marathon Training System for Beginners

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

Your system must include 5-6 modules. Fill in the table below as you plan each module.

| Module | Topic(s) | Inputs | Outputs | Depends On | Checkpoint |
| ------ | -------- | ------ | ------- | ---------- | ---------- |
| 1 | Propositional Logic (Knowledge Bases, Inference, Chaining) | Runner profile dict with injuries, symptoms, training load, recovery status, experience level, environment, available terrain, and proposed workout | Safety assessment dict with safe (bool), reason (str), alternative workout (dict or None), and recommendation (str) if no alternative exists | None | Checkpoint 1 (Feb 11) |
| 2 | Search (A*, Heuristics, State-Space Search) | Config dict: goal, race_date, days_per_week, current_weekly_miles, experience, available_terrain; optional validate_fn and runner_profile for safety checks | Plan result dict with success (bool), plan (list of week dicts: week, total_miles, long_run, workouts), total_weeks, total_penalty, search_stats, rationale, errors | Module 1 (optional) | Checkpoint 1 (Feb 11) |
| 3 | NLP (regex/n-grams, distributional semantics, sentiment) | Free-text run description (str); optional store_path for log_run / get_run_history | parse_run: dict (type, distance, pace_minutes, terrain, sentiment, effort, notes). log_run: run ID (str). get_run_history: list of run entry dicts | None (integrates with M1/M2 for validation and plan alignment) | Checkpoint 2 (Feb 26) |
| 4 | Game Theory (Sequential Games, Nash-like strategy selection) | Context dict: current_streak, recent_sentiments, terrain_last_week, adherence_percent, days_to_race | Strategy dict with strategy (str), message_tone (str), reasoning (str); detailed variant also returns per-strategy scores and inferred runner state | Module 3 (uses sentiment / history) | Checkpoint 3 (Mar 19) |
| 5 | Reinforcement Learning (MDP, Q-learning, value updates) | Context dict: workout_type, terrain, fatigue_score, history (runs with distance, pace, terrain, sentiment); optional motivation (Module 4: streak, sentiments, terrain_last_week, adherence_percent, days_to_race); optional q_table_path | adapt_progression: next_distance, target_pace, suggested_terrain, confidence, reasoning; detailed adds Q snapshot; train_on_run for online Q-updates | Modules 3 & 4 | Checkpoint 4 (Apr 2) |
| 6 (optional) | Supervised Learning (linear / logistic regression, metrics) | Runner snapshot: ``history`` (Module 3–style runs), ``age``, ``goal_race`` (distance, target_time, terrain); optional ``experience_level``, ``days_to_race``, ``adherence_percent`` — or use ``pipeline_predict_race_readiness(profile)`` | ``predicted_finish``, ``confidence_interval``, ``readiness_score``, ``recommendations`` | Modules 3 & 5 (history); pipeline ties profile + log | Checkpoint 5 (Apr 16) |

## Repository Layout

```
your-repo/
├── src/                              # main system source code
├── unit_tests/                       # unit tests (parallel structure to src/)
├── integration_tests/                # integration tests (new folder for each module)
├── .claude/skills/code-review/SKILL.md  # rubric-based agent review
├── AGENTS.md                         # instructions for your LLM agent
└── README.md                         # system overview and checkpoints
```

## Setup

```bash
pip install -r requirements.txt
```

Use the **same** Python for installs and tests (e.g. `python -m pip install -r requirements.txt` then `python -m pytest`). Module 6 needs **NumPy** and **scikit-learn**. No environment variables required. Core modules 1–2 use the standard library plus pytest; later modules add the packages above.

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

**Pipeline (race prediction from profile + run log):**
```python
from src.pipeline import load_runner_profile, pipeline_predict_race_readiness

profile = load_runner_profile("data/runner_profile.json")
profile["age"] = 32
profile["race_goal"] = {"target_time": "4:30:00", "terrain": "road"}
result = pipeline_predict_race_readiness(profile, module6_dir="data/module6")
```

## Testing

**Unit Tests** (`unit_tests/`): Mirror the structure of `src/`. Each module has corresponding unit tests.

**Integration Tests** (`integration_tests/`): Subfolder per module beyond the first (e.g. `integration_tests/module2_integration/`, `integration_tests/module3_integration/`), demonstrating how modules work together.

**Run tests** (from repo root):

```bash
# Unit tests only
PYTHONPATH=. pytest unit_tests/ -v

# Integration tests only (Module 1 + Module 2 pipeline)
PYTHONPATH=. pytest integration_tests/ -v

# All tests (unit + integration)
PYTHONPATH=. pytest unit_tests/ integration_tests/ -v
```

No external test data required; tests use in-memory configs and profiles. Module 6 can auto-generate synthetic training CSV and fit models under ``data/module6/`` on first use (ignored by git).

## Checkpoint Log

| Checkpoint | Date | Modules Included | Status | Evidence |
| ---------- | ---- | ---------------- | ------ | -------- |
| 1 | Feb 14, 2025 | Module 1 & 2 | Completed |  |
| 2 |  |  |  |  |
| 3 | Mar 19, 2026 | Module 4 | Completed | `checkpoints/checkpoint_3_elegance_report.md`, `checkpoints/checkpoint_3_module_report.md`; `PYTHONPATH=. pytest unit_tests/ integration_tests/ -v` (688 passed) |
| 4 |  |  |  |  |

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

Hospital for Special Surgery. "Injury Prevention for Marathon Runners." *HSS*, https://www.hss.edu/article_injury-prevention-marathon-runners.asp.

Marathon Handbook. "The 12 Rules of Marathon Training." *Marathon Handbook*, https://marathonhandbook.com/the-12-rules-of-marathon-training/.

Mayo Clinic Health System. "Speaking of Health." *Mayo Clinic Health System*, https://www.mayoclinichealthsystem.org/hometown-health/speaking-of-health/.

Physical Therapy & Sports Medicine Center. "Ready to Run: Key Strategies to Get Started Running Safely." *PTSMC*, https://www.ptsmc.com/ready-to-run-key-strategies-to-get-started-running-safely/.

Running Lifestyle Media. "9 Guidelines on Writing a Running Training Plan." *Running Lifestyle*, https://running-lifestyle.com/9-guidelines-on-writing-a-running-training-plan/.

Therapeutic Associates Physical Therapy. "10 Laws of Preventing Running Injuries." *Therapeutic Associates*, https://www.therapeuticassociates.com/10-laws-of-preventing-running-injuries/.

VCU Health. "How Runners Can Prevent Injury." *VCU Health*, https://www.vcuhealth.org/news/how-runners-can-prevent-injury.
