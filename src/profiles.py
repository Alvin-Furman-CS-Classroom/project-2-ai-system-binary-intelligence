"""
User Profile module for the Long Run AI Marathon Training System.

This module defines the UserProfile structure which acts as the central data model
shared across all modules (Safety Validator, Plan Generator, etc.).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class UserProfile:
    """
    Represents a runner's profile containing their physical status, 
    training history, goals, and constraints.
    """
    
    # 1. Identity & Experience
    name: str = "Anonymous Runner"
    experience_level: str = "beginner"  # beginner, intermediate, advanced
    
    # 2. Goals
    goal: str = "complete marathon"
    race_date: Optional[str] = None  # ISO format "YYYY-MM-DD"
    
    # 3. Physical status & Health
    weekly_mileage: float = 0.0
    injuries: List[str] = field(default_factory=list)  # e.g., ["shin splints", "knee"]
    symptoms: List[str] = field(default_factory=list)  # e.g., ["chest pain", "dizziness"]
    pain_level: str = "none"  # none, mild, moderate, severe
    cleared_by_doctor: bool = False  # Required if injuries is not empty
    
    # 4. Recovery & Daily Status
    fully_recovered: bool = True
    sleep_quality: str = "good"  # good, fair, poor
    hydrated: bool = True
    
    # 5. Training History (Current Week/Recent)
    rest_days_this_week: int = 0
    days_trained_this_week: int = 0
    hard_workout_yesterday: bool = False
    rest_day_yesterday: bool = False
    
    # 6. Environment & Constraints
    available_terrain: List[str] = field(default_factory=list) # road, track, trail, treadmill
    weather: str = "normal"  # normal, extreme_heat, extreme_cold
    proper_footwear: bool = True
    
    # 7. Current Context (The "proposed" action usually comes from outside, 
    # but having a slot for the workout currently being validated is useful)
    proposed_workout: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert profile to dictionary format required by the Safety Validator module.
        """
        return {
            "experience_level": self.experience_level,
            "weekly_mileage": self.weekly_mileage,
            "injuries": self.injuries,
            "symptoms": self.symptoms,
            "pain_level": self.pain_level,
            "cleared_by_doctor": self.cleared_by_doctor,
            "fully_recovered": self.fully_recovered,
            "sleep_quality": self.sleep_quality,
            "hydrated": self.hydrated,
            "rest_days_this_week": self.rest_days_this_week,
            "days_trained_this_week": self.days_trained_this_week,
            "hard_workout_yesterday": self.hard_workout_yesterday,
            "rest_day_yesterday": self.rest_day_yesterday,
            "available_terrain": self.available_terrain,
            "weather": self.weather,
            "proper_footwear": self.proper_footwear,
            "race_date": self.race_date,
            "proposed_workout": self.proposed_workout or {}
        }

    @classmethod
    def create_new_user(cls, name: str, experience: str = "beginner") -> 'UserProfile':
        """Factory method to create a basic new user."""
        return cls(
            name=name,
            experience_level=experience,
            available_terrain=["road"],  # Default assumption
            weekly_mileage=0.0
        )
