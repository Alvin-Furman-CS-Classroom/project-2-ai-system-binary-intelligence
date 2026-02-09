import pytest
from datetime import date, timedelta
from src.module2_training_plan_generator.search import astar_plan, _weeks_until

class TestSearchPlan:
    def test_weeks_until_calculation(self):
        """Test calculation of weeks until race."""
        today = date.today()
        # 10 weeks out
        race_date = (today + timedelta(weeks=10)).strftime("%Y-%m-%d")
        weeks = _weeks_until(race_date)
        assert weeks == 10

    def test_basic_plan_generation(self):
        """Test that a plan is generated for standard inputs."""
        race_date = (date.today() + timedelta(weeks=8)).strftime("%Y-%m-%d")
        inputs = {
            "goal": "half_marathon",
            "race_date": race_date,
            "days_per_week": 4,
            "current_weekly_miles": 15.0,
            "experience": "intermediate",
            "available_terrain": ["road"]
        }
        
        # Validates effectively correct syntax and basic heuristic flow
        result = astar_plan(inputs, max_expansions=1000)
        
        assert result.output is not None
        assert len(result.output["plan"]) == 8
        assert result.total_cost < float("inf")

    def test_plan_with_safety_validator(self):
        """Test integration with a mock safety validator."""
        race_date = (date.today() + timedelta(weeks=4)).strftime("%Y-%m-%d")
        inputs = {
            "goal": "5k",
            "race_date": race_date,
            "days_per_week": 3,
            "current_weekly_miles": 10.0,
            "experience": "beginner",
            "available_terrain": ["road"]
        }
        
        # Mock validator that rejects long runs > 8 miles
        def mock_validator(profile, workout):
            if workout.get("type") == "long run" and workout.get("distance", 0) > 8:
                return {
                    "safe": False, 
                    "alternative": {**workout, "distance": 8, "type": "long run (capped)"}
                }
            return {"safe": True}

        result = astar_plan(inputs, safety_validator=mock_validator, max_expansions=1000)
        
        # Check that we got a plan
        assert len(result.output["plan"]) == 4
        
        # Verify no long runs > 8 exist in the plan (they should have been capped)
        for week in result.output["plan"]:
            for day in week["workouts"]:
                if day["type"] == "long run":
                    assert day["distance"] <= 8
