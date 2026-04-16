"""
Forward chaining inference engine for workout safety validation.

This module implements propositional logic inference using forward chaining
to derive safety conclusions from facts and rules.
"""

from typing import Set, List, Tuple
from .rules import SafetyRule, SAFETY_RULES, SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_NONE

# Safety limit to prevent infinite loops in forward chaining
MAX_FORWARD_CHAIN_ITERATIONS = 100


def forward_chain(
    facts: Set[str],
    rules: List[SafetyRule] = None
) -> Tuple[Set[str], List[SafetyRule]]:
    """
    Apply forward chaining to derive all possible conclusions from facts and rules.
    
    Forward chaining is a data-driven inference method that starts with known
    facts and applies rules repeatedly until no new facts can be derived.
    
    Algorithm:
        1. Start with initial facts
        2. For each rule, check if all conditions are satisfied
        3. If satisfied and conclusion not already derived, add conclusion to facts
        4. Repeat until no new facts can be added (fixed point reached)
        5. Track which rules fired for explanation
    
    Args:
        facts: Initial set of propositional facts
        rules: List of safety rules to apply (defaults to all SAFETY_RULES)
        
    Returns:
        Tuple of (all_derived_facts, fired_rules)
        - all_derived_facts: Set of all facts including initial and derived
        - fired_rules: List of rules that fired during inference
        
    Example:
        >>> facts = {"shin_splints", "track_terrain"}
        >>> all_facts, fired = forward_chain(facts)
        >>> "high_injury_risk" in all_facts
        True
        >>> len(fired) >= 1
        True
    """
    if rules is None:
        rules = SAFETY_RULES
    
    # Copy initial facts to avoid modifying input
    all_facts = set(facts)
    fired_rules = []
    
    # Iteratively apply rules until no new facts can be derived
    changed = True
    iteration = 0

    while changed and iteration < MAX_FORWARD_CHAIN_ITERATIONS:
        changed = False
        iteration += 1
        
        for rule in rules:
            # Check if this rule has already fired
            if rule in fired_rules:
                continue
            
            # Check if all conditions are satisfied
            if all(condition in all_facts for condition in rule.conditions):
                # Add conclusion if not already present
                if rule.conclusion not in all_facts:
                    all_facts.add(rule.conclusion)
                    fired_rules.append(rule)
                    changed = True
    
    return all_facts, fired_rules


def determine_safety(derived_facts: Set[str]) -> Tuple[bool, str]:
    """
    Determine if workout is safe based on derived facts.
    
    Checks for presence of unsafe conclusions in the derived facts.
    Safety levels are prioritized: critical > high > medium.
    
    Args:
        derived_facts: Set of all facts after inference
        
    Returns:
        Tuple of (is_safe, severity_level)
        - is_safe: True if workout is safe, False otherwise
        - severity_level: "none", "medium", "high", or "critical"
        
    Example:
        >>> facts = {"unsafe_critical", "chest_pain"}
        >>> is_safe, severity = determine_safety(facts)
        >>> is_safe
        False
        >>> severity
        'critical'
    """
    # Check for unsafe conclusions in priority order
    if "unsafe_critical" in derived_facts:
        return False, SEVERITY_CRITICAL
    
    if "high_injury_risk" in derived_facts or "unsafe_high" in derived_facts:
        return False, SEVERITY_HIGH
    
    if "unsafe_medium" in derived_facts or "overtraining_risk" in derived_facts or "medium_injury_risk" in derived_facts:
        return False, SEVERITY_MEDIUM
    
    # No unsafe conclusions found
    return True, SEVERITY_NONE


def explain_inference(
    initial_facts: Set[str],
    derived_facts: Set[str],
    fired_rules: List[SafetyRule]
) -> str:
    """
    Generate a human-readable explanation of the inference process.
    
    Shows which facts led to which conclusions through which rules.
    Useful for debugging and understanding why a workout was deemed unsafe.
    
    Args:
        initial_facts: Facts present before inference
        derived_facts: All facts after inference
        fired_rules: Rules that fired during inference
        
    Returns:
        Multi-line string explaining the inference process
        
    Example:
        >>> explanation = explain_inference(initial, derived, fired)
        >>> print(explanation)
        Initial facts: shin_splints, track_terrain
        
        Rules fired:
        1. shin_splints_track: Track running aggravates shin splints...
           Derived: high_injury_risk
        
        Final conclusion: unsafe (high severity)
    """
    lines = []
    
    # Show initial facts
    lines.append("Initial facts:")
    for fact in sorted(initial_facts):
        lines.append(f"  - {fact}")
    lines.append("")
    
    # Show inference chain
    if fired_rules:
        lines.append("Rules fired:")
        for i, rule in enumerate(fired_rules, 1):
            lines.append(f"{i}. {rule.name}: {rule.explanation}")
            lines.append(f"   Conditions: {', '.join(rule.conditions)}")
            lines.append(f"   Derived: {rule.conclusion}")
            lines.append("")
    else:
        lines.append("No rules fired (all conditions safe)")
        lines.append("")
    
    # Show final conclusion
    is_safe, severity = determine_safety(derived_facts)
    if is_safe:
        lines.append("Final conclusion: SAFE")
    else:
        lines.append(f"Final conclusion: UNSAFE ({severity} severity)")
    
    return "\n".join(lines)


def get_critical_rules(fired_rules: List[SafetyRule]) -> List[SafetyRule]:
    """
    Filter fired rules to only those with critical severity.
    
    Args:
        fired_rules: List of rules that fired
        
    Returns:
        List of only critical severity rules
    """
    return [rule for rule in fired_rules if rule.severity == SEVERITY_CRITICAL]


def get_alternative_blocking_rules(fired_rules: List[SafetyRule]) -> List[SafetyRule]:
    """
    Get rules that prevent suggesting alternatives.
    
    Rules with can_suggest_alternative=False (like critical safety rules)
    prevent the system from suggesting any workout alternative.
    
    Args:
        fired_rules: List of rules that fired
        
    Returns:
        List of rules that block alternative suggestions
    """
    return [rule for rule in fired_rules if not rule.can_suggest_alternative]


def validate_rule_consistency(rules: List[SafetyRule]) -> List[str]:
    """
    Check for potential inconsistencies in the rule base.
    
    Looks for:
    - Rules with duplicate names
    - Rules with no conditions
    - Rules with empty conclusions
    
    Args:
        rules: List of safety rules to validate
        
    Returns:
        List of warning messages (empty if no issues)
        
    Example:
        >>> warnings = validate_rule_consistency(SAFETY_RULES)
        >>> len(warnings)
        0
    """
    warnings = []
    
    # Check for duplicate names
    names = [rule.name for rule in rules]
    duplicates = [name for name in names if names.count(name) > 1]
    if duplicates:
        warnings.append(f"Duplicate rule names found: {set(duplicates)}")
    
    # Check for rules with no conditions
    no_conditions = [rule.name for rule in rules if not rule.conditions]
    if no_conditions:
        warnings.append(f"Rules with no conditions: {no_conditions}")
    
    # Check for rules with empty conclusions
    no_conclusion = [rule.name for rule in rules if not rule.conclusion]
    if no_conclusion:
        warnings.append(f"Rules with no conclusion: {no_conclusion}")
    
    return warnings


def check_facts_coverage(facts: Set[str], rules: List[SafetyRule]) -> Tuple[bool, List[str]]:
    """
    Check if the given facts can potentially fire any rules.
    
    Useful for debugging when no rules fire and you want to know why.
    
    Args:
        facts: Set of propositional facts
        rules: List of safety rules
        
    Returns:
        Tuple of (can_fire_rules, missing_conditions)
        - can_fire_rules: True if at least one rule can fire
        - missing_conditions: List of conditions needed to fire at least one rule
        
    Example:
        >>> facts = {"shin_splints"}
        >>> can_fire, missing = check_facts_coverage(facts, SAFETY_RULES)
        >>> "track_terrain" in missing or "road_terrain" in missing
        True
    """
    can_fire = False
    all_missing = []
    
    for rule in rules:
        missing = [cond for cond in rule.conditions if cond not in facts]
        if not missing:
            can_fire = True
        else:
            all_missing.extend(missing)
    
    # Get unique missing conditions
    unique_missing = list(set(all_missing))
    
    return can_fire, unique_missing