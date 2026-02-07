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
| 2 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |
| 4 |  |  |  |  |  |
| 5 |  |  |  |  |  |
| 6 (optional) |  |  |  |  |  |

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

List dependencies, setup steps, and any environment variables required to run the system.

## Running

**Module 1 (safety validator):**
```python
from src.module1_safety_validator import validate_workout
profile = {"weekly_mileage": 20, "experience_level": "intermediate", "hydrated": True, "proper_footwear": True, "weather": "normal", "rest_days_this_week": 2, "days_trained_this_week": 3, "fully_recovered": True, "sleep_quality": "good", "available_terrain": ["road", "track"]}
workout = {"type": "long run", "distance": 10, "terrain": "road"}
result = validate_workout(profile, workout)  # {"safe": bool, "reason": str, "alternative": ...}
```

## Testing

**Unit Tests** (`unit_tests/`): Mirror the structure of `src/`. Each module should have corresponding unit tests.

**Integration Tests** (`integration_tests/`): Create a new subfolder for each module beyond the first, demonstrating how modules work together.

Provide commands to run tests and describe any test data needed.

## Checkpoint Log

| Checkpoint | Date | Modules Included | Status | Evidence |
| ---------- | ---- | ---------------- | ------ | -------- |
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
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

List libraries, APIs, datasets, and other references used by the system.
