## Project Context

- System title: Long Run: AI Marathon Training System for Beginners
- Theme: Personalized marathon coaching that adapts to each runner's constraints, goals, terrain options, and progress
- Proposal link or summary: See PROPOSAL.md for full proposal

**Module plan:**

| Module | Required Topic(s) | Topic Covered By | Checkpoint Due |
| ------ | ----------------- | ---------------- | -------------- |
| 1: Safety Validator | Propositional Logic | Weeks 1-2 | Checkpoint 1 (Feb 11) |
| 2: Plan Generator | Search Algorithms | Weeks 3-4 | Checkpoint 2 |
| 3: Run Logger | NLP | Weeks 7-8 | Checkpoint 2 (Feb 26) |
| 4: Motivation Selector | Game Theory | Weeks 8-9 | Checkpoint 3 (Mar 19) |
| 5: Adaptive Progression | Reinforcement Learning | Weeks 10-11 | Checkpoint 4 (Apr 2) |
| 6: Race Predictor | Supervised Learning | Weeks 12+ | Checkpoint 5 (Apr 16) |

## Constraints

- 5-6 modules total, each tied to course topics.
- Each module must have clear inputs/outputs and tests.
- Align module timing with the course schedule.

## How the Agent Should Help

- Draft plans for each module before coding.
- Suggest clean architecture and module boundaries.
- Identify missing tests and edge cases.
- Review work against the rubric using the code-review skill.

## Agent Workflow

1. Ask for the current module spec from `README.md`.
2. Produce a plan (use "Plan" mode if available).
3. Wait for approval before writing or editing code.
4. After implementation, run the code-review skill and list gaps.
5. Ask me for confirmation before creating or deleting any files.

## Key References

- Project Instructions: https://csc-343.path.app/projects/project-2-ai-system/ai-system.project.md
- Code elegance rubric: https://csc-343.path.app/rubrics/code-elegance.rubric.md
- Course schedule: https://csc-343.path.app/resources/course.schedule.md
- Rubric: https://csc-343.path.app/projects/project-2-ai-system/ai-system.rubric.md