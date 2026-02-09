"""
Demo script showing how to interact with the Profiles and Safety Validator.
"""

from src.profiles import UserProfile
from src.module1_safety_validator.validator import validate_workout

def run_demo():
    print("--- 1. Creating a User Profile ---")
    # multiple ways to intialize
    user = UserProfile(
        name="Mengsrun",
        experience_level="beginner",
        weekly_mileage=10.0,
        available_terrain=["road", "track", "treadmill"],
        injuries=["Cancer"],  # Add an injury
        pain_level="mild"
    )

    print(f"Created user: {user.name}")
    print(f"Injuries: {user.injuries}")
    print("-" * 30)

    print("\n--- 2. Proposing a Risky Workout ---")
    # A long run on a hard surface with shin splints is risky
    risky_workout = {
        "type": "long run", 
        "distance": 8.0, 
        "terrain": "track"
    }
    
    # Attach workout to user (optional, but good practice)
    user.proposed_workout = risky_workout
    
    print(f"Proposed: {risky_workout['distance']} mile {risky_workout['type']} on {risky_workout['terrain']}")
    print("-" * 30)

    print("\n--- 3. Validating Safety ---")
    # Convert profile to dictionary and validate
    profile_dict = user.to_dict()
    
    result = validate_workout(profile_dict)
    
    print(f"Is Safe: {result['safe']}")
    print(f"Reason: {result['reason']}")
    
    if 'alternative' in result and result['alternative']:
        print(f"\nSuggestion: Try {result['alternative']['type']} on {result['alternative']['terrain']} instead.")
    elif 'recommendation' in result:
        print(f"\nRecommendation: {result['recommendation']}")

if __name__ == "__main__":
    run_demo()
