Great addition. Terrain affects pacing, injury r
# Long Run: AI Marathon Training System for Beginners

## System Overview

Novice runners often struggle with pacing, training volume, and progression without professional guidance. Many beginners either follow generic plans that ignore their fitness level, push too hard and risk injury, or lose motivation when they don't see improvement. Long Run addresses these challenges by providing personalized coaching that adapts to each runner's constraints, goals, and progress.

The system validates workout safety based on user limitations and available terrain, generates training plans tailored to race goals and running environment, logs run performance through natural language input, adapts training loads based on results, and predicts race readiness timelines. This creates a complete coaching experience from a runner's first easy jog through race day preparation.

Implementing a marathon training system requires multiple AI techniques because coaching involves diverse intelligent behaviors. Safety validation requires logical reasoning about injury risk, recovery needs, and terrain suitability. Plan generation requires searching through possible workout combinations across different surfaces. Run logging requires understanding informal user descriptions. Motivation management requires strategic decision-making about when to push and when to rest. Progression requires learning each runner's response patterns. Race prediction requires modeling trends from historical data.

The system comprises six modules that share a central user profile and training history database. Early modules establish safety constraints and baseline plans, while later modules learn from accumulated training data to adapt and predict outcomes.

## Modules

### Module 1: Workout Safety Validator

**Topics:** Propositional Logic (Knowledge Bases, Inference, Chaining)

**Input:** Runner profile dictionary containing injury history, physical limitations, recent training load, available terrain, and a proposed workout.
```python
{"injuries": ["shin splints"], "weekly_mileage": 15, "rest_days_this_week": 1, "available_terrain": ["treadmill", "track"], "proposed_workout": {"type": "long run", "distance": 12, "terrain": "track"}}
```

**Output:** Safety assessment dictionary with recommendation and reasoning.
```python
{"safe": False, "reason": "Track running aggravates shin splints due to repetitive turns; long run exceeds safe mileage", "alternative": {"type": "long run", "distance": 8, "terrain": "treadmill"}}
```

**Integration:** Validates all workouts before the Plan Generator includes them in training schedules. Also checks user-logged runs in real-time to prevent unsafe training choices.

**Prerequisites:** Propositional Logic content from Weeks 1-2. No prior modules required.

The module constructs a knowledge base of training contraindications (e.g., "track running AND shin splints implies high injury risk") and uses forward chaining to infer whether a given workout is safe for the runner's current state and available terrain.

---

### Module 2: Training Plan Generator

**Topics:** Uninformed Search (BFS, DFS, Uniform Cost), Informed Search (Heuristics, A*)

**Input:** Race goal, available training days, current fitness level, weeks until race, and available terrain options.
```python
{"goal": "complete marathon", "race_date": "2025-06-15", "days_per_week": 5, "current_weekly_miles": 20, "experience": "beginner", "available_terrain": ["road", "treadmill", "trail"]}
```

**Output:** Complete training plan with workout types, distances, terrain assignments, and weekly structure.
```python
{"plan": [{"week": 1, "workouts": [{"day": "Monday", "type": "easy run", "distance": 4, "terrain": "road"}, {"day": "Wednesday", "type": "tempo", "distance": 5, "terrain": "treadmill"}, {"day": "Saturday", "type": "long run", "distance": 10, "terrain": "trail"}]}, ...], "rationale": "16-week buildup mixing terrain for injury prevention"}
```

**Integration:** Uses Module 1 to verify all planned workouts are safe for the runner and appropriate for the assigned terrain. Provides the baseline plan that Module 5 will adapt over time based on performance.

**Prerequisites:** Search algorithms content from Weeks 3-4. Requires Module 1.

The module uses A* search to explore possible workout combinations, with a heuristic function balancing mileage progression, workout variety, terrain rotation, and recovery time.

---

### Module 3: Natural Language Run Logger

**Topics:** NLP Before LLMs (n-grams, Word Embeddings)

**Input:** Free-text description of completed run.
```python
"did my long run on the trail today, 10 miles at 9:30 pace. felt pretty tired by mile 8 but the soft surface helped my shins"
```

**Output:** Structured run data with parsed distance, pace, terrain, workout type, and effort sentiment.
```python
{"type": "long run", "distance": 10, "pace_minutes": 9.5, "terrain": "trail", "sentiment": "struggled", "notes": "fatigue at mile 8, shins felt good on soft surface"}
```

**Integration:** Converts runner descriptions into structured data that feeds Module 5 (progression decisions) and Module 6 (predictions). Builds the historical dataset the system needs for learning.

**Prerequisites:** NLP content from Weeks 7-8. Requires Module 2 to define expected workout vocabulary.

The module uses word embeddings to match informal workout and terrain descriptions to canonical types, n-gram models to extract distance/pace patterns, and sentiment analysis to gauge perceived effort.

---

### Module 4: Motivation Strategy Selector

**Topics:** Game Theory (Nash Equilibrium, Sequential Move Games)

**Input:** Runner's current training streak, recent workout sentiment scores, terrain variety, and plan adherence.
```python
{"current_streak": 18, "recent_sentiments": ["good", "good", "struggled"], "terrain_last_week": ["treadmill", "treadmill", "treadmill"], "adherence_percent": 85, "days_to_race": 45}
```

**Output:** Recommended coaching strategy with intensity level and terrain suggestion.
```python
{"strategy": "encourage_variety", "message_tone": "motivating", "reasoning": "Monotonous treadmill running may cause mental fatigue; suggest outdoor run for engagement"}
```

**Integration:** Uses sentiment data from Module 3 to inform coaching decisions. Influences whether Module 5 should increase or decrease training intensity or vary terrain, creating a feedback loop where runner responses shape future programming.

**Prerequisites:** Game Theory content from Weeks 8-9. Requires Module 3 for sentiment input.

The module models the coach-runner interaction as a sequential game where the system chooses between pushing harder, maintaining volume, encouraging rest, or suggesting terrain changes. The runner "responds" through adherence and sentiment in subsequent workouts. Finding Nash equilibrium between maximizing fitness gains and preventing burnout keeps runners consistent. The payoff matrix weighs short-term mileage against long-term injury risk and mental freshness, recognizing that overtraining leads to missed weeks while monotonous training kills motivation.

---

### Module 5: Adaptive Progression System

**Topics:** Reinforcement Learning (Q-Learning, MDPs, Value Functions)

**Input:** Workout type, terrain, historical performance data, and runner fatigue indicators.
```python
{"workout_type": "tempo run", "terrain": "track", "history": [{"date": "2025-01-10", "distance": 5, "pace": 8.5, "terrain": "track", "sentiment": "good"}, ...], "fatigue_score": 0.3}
```

**Output:** Next session's recommended distance, target pace, and terrain.
```python
{"next_distance": 6, "target_pace": 8.25, "suggested_terrain": "road", "confidence": 0.80, "reasoning": "Consistent tempo performance supports increase; switching to road for variety"}
```

**Integration:** Receives logged runs from Module 3 and motivation context from Module 4. Adjusts Module 2's baseline plan week-to-week, creating a dynamic training program that learns optimal progression rates and terrain rotation for each runner.

**Prerequisites:** Reinforcement Learning content from Weeks 10-11. Requires Modules 3 and 4.

The module models progression as an MDP where states are current fitness levels and terrain history, actions are volume/intensity/terrain adjustments, and rewards balance improvement against injury/burnout risk, using Q-learning to find the optimal policy for each runner's response pattern.

---

### Module 6: Race Readiness Predictor

**Topics:** Supervised Learning (Linear Regression, Logistic Regression, Evaluation Metrics)

**Input:** Complete training history including terrain data, runner demographics, and race goal.
```python
{"history": [...all logged runs with terrain...], "age": 28, "goal_race": {"distance": "marathon", "target_time": "4:30:00", "terrain": "road"}}
```

**Output:** Race readiness assessment, predicted finish time, and terrain-specific recommendations.
```python
{"predicted_finish": "4:25:00", "confidence_interval": ["4:15:00", "4:35:00"], "readiness_score": 0.85, "recommendations": ["increase road running to match race surface", "add one more 20-mile long run on roads"]}
```

**Integration:** Analyzes all data from Modules 3 and 5 to provide race day projections. Recommends training adjustments (validated by Module 1) to address gaps, feeding back into Module 2 for plan updates.

**Prerequisites:** Supervised Learning content from Weeks 12+. Requires all prior modules.

The module uses linear regression to model fitness progression curves and predict finish times, factoring in terrain-specific performance. It employs logistic regression to classify whether the runner is adequately prepared based on training characteristics, terrain distribution, and historical patterns.

---

## Feasibility Study

| Module | Required Topic(s) | Topic Covered By | Checkpoint Due |
| ------ | ----------------- | ---------------- | -------------- |
| 1: Safety Validator | Propositional Logic | Weeks 1-2 | Checkpoint 1 (Feb 11) |
| 2: Plan Generator | Search Algorithms | Weeks 3-4 | Checkpoint 1 (Feb 11) |
| 3: Run Logger | NLP | Weeks 7-8 | Checkpoint 2 (Feb 26) |
| 4: Motivation Selector | Game Theory | Weeks 8-9 | Checkpoint 3 (Mar 19) |
| 5: Adaptive Progression | Reinforcement Learning | Weeks 10-11 | Checkpoint 4 (Apr 2) |
| 6: Race Predictor | Supervised Learning | Weeks 12+ | Checkpoint 5 (Apr 16) |

Each module is scheduled with at least one week of buffer between when the required content is taught and when the checkpoint is due, allowing time for implementation and testing.

## Coverage Rationale

The system covers six topics: Propositional Logic, Search, NLP, Game Theory, Reinforcement Learning, and Supervised Learning. These topics were selected because they address distinct aspects of running coaching that require different types of intelligence.

Propositional Logic fits safety validation because training contraindications follow clear conditional rules (if shin splints and track surface, then avoid repetitive turn stress). Search works well for plan generation because building a training schedule requires exploring combinations of workout types, distances, terrain options, and rest days to optimize for race readiness. NLP suits run logging because runners describe workouts informally and the system must extract structured data including terrain. Game Theory applies to motivation because coaching involves strategic interaction where both parties respond to each other's choices. Reinforcement Learning aligns with progression because optimal mileage increases depend on learned patterns of how each runner responds to training stress across different surfaces. Supervised Learning handles prediction because race times can be modeled from historical training data and terrain-specific performance.

This selection demonstrates progressive complexity throughout the semester. Early modules use deterministic methods with clear rules and search strategies, while later modules incorporate learning techniques that improve with accumulated data. Each module's output feeds naturally into subsequent modules, creating meaningful integration rather than isolated components.

First-Order Logic was excluded because propositional logic suffices for representing training contraindications without requiring quantifiers or complex predicates. Advanced Search techniques beyond A* were omitted since the plan optimization problem doesn't require hierarchical planning or adversarial search. Constraint Satisfaction was considered for plan generation but A* with appropriate heuristics provides more flexibility for the optimization criteria involved.

---
