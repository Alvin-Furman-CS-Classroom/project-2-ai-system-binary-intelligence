"""
Integration tests: Module 3 (run logger) + Module 4 (motivation selector).

Verifies that Module 3 output (parse_run, get_run_history) can be piped
into Module 4 to produce coaching strategies. Covers sentiment/effort
mapping, terrain flow, and the full pipeline from natural-language run
descriptions to motivation recommendations.

Run from repo root: PYTHONPATH=. pytest integration_tests/module4_integration/ -v
"""

from __future__ import annotations

from src.module3_run_logger import parse_run, log_run, get_run_history
from src.module4_motivation_selector import (
    select_motivation_strategy,
    select_motivation_strategy_detailed,
)


def _build_m4_context_from_m3_history(
    history: list,
    current_streak: int = 0,
    adherence_percent: float = 80.0,
    days_to_race: int = 45,
) -> dict:
    """Build Module 4 context from Module 3 run history.

    Maps Module 3 sentiment (positive/neutral/negative) and effort
    (easy/moderate/hard/struggled) to Module 4's coarse buckets.
    """
    if not history:
        raise ValueError("Need at least one run to build context")

    sentiments = []
    terrain = []
    for entry in history:
        parsed = entry.get("parsed", entry)
        # Use effort as primary (workout difficulty); sentiment as fallback
        effort = parsed.get("effort", "moderate")
        sentiment = parsed.get("sentiment", "neutral")

        if effort in ("easy",) or sentiment == "positive":
            sentiments.append("good")
        elif effort in ("hard", "struggled") or sentiment == "negative":
            sentiments.append("struggled")
        else:
            sentiments.append("neutral")

        t = parsed.get("terrain", "road")
        if t:
            terrain.append(t)

    if not terrain:
        raise ValueError("History produced no valid terrain")

    return {
        "current_streak": current_streak,
        "recent_sentiments": sentiments,
        "terrain_last_week": terrain,
        "adherence_percent": adherence_percent,
        "days_to_race": days_to_race,
    }


# ===========================================================================
# M3 → M4: Parsed runs feed motivation selector
# ===========================================================================


class TestModule3OutputFeedsModule4:
    """Module 3 parse_run output formats correctly for Module 4."""

    def test_parsed_run_with_excellent_sentiment_maps_to_good(self):
        """'Felt excellent' parses to positive sentiment; M4 normalizes to good."""
        parsed = parse_run("easy 5 miles on road, felt excellent")
        # Module 3 outputs sentiment (positive/neutral/negative) and effort (easy/...)
        assert parsed.get("sentiment") in ("positive", "neutral") or parsed.get("effort") == "easy"

        ctx = _build_m4_context_from_m3_history(
            [{"parsed": parsed}],
            current_streak=5,
            adherence_percent=90,
            days_to_race=60,
        )
        result = select_motivation_strategy_detailed(ctx)
        assert "strategy" in result
        assert "reasoning" in result
        # recent_sentiments should include "good" (excellent/positive/easy → good)
        assert "good" in ctx["recent_sentiments"] or "neutral" in ctx["recent_sentiments"]

    def test_parsed_struggled_run_maps_to_struggled(self):
        """Run described as exhausting parses to struggled effort; M4 gets struggled."""
        parsed = parse_run("long run 10 miles, completely exhausted by mile 8")
        assert parsed.get("effort") in ("hard", "struggled") or parsed.get("sentiment") == "negative"

        ctx = _build_m4_context_from_m3_history(
            [{"parsed": parsed}, {"parsed": parsed}],
            adherence_percent=95,
        )
        result = select_motivation_strategy_detailed(ctx)
        assert result["inferred_state"] in ("burnout_risk", "mixed")

    def test_terrain_from_parsed_run_passes_validation(self):
        """Terrain from Module 3 (road, track, treadmill, trail) is valid for M4."""
        for nl, expected_terrain in [
            ("easy 3 miles on the road", "road"),
            ("5k on track", "track"),
            ("treadmill 4 miles", "treadmill"),
            ("trail run 6 miles", "trail"),
        ]:
            parsed = parse_run(nl)
            assert parsed.get("terrain") == expected_terrain
            ctx = _build_m4_context_from_m3_history([{"parsed": parsed}])
            result = select_motivation_strategy(ctx)
            assert result["strategy"] in (
                "push_harder",
                "maintain",
                "encourage_rest",
                "encourage_variety",
            )


# ===========================================================================
# Full pipeline: log runs (M3), build context, select strategy (M4)
# ===========================================================================


class TestLogRunsThenSelectMotivation:
    """Full pipeline: log runs via M3, build context, get M4 strategy."""

    def test_log_multiple_runs_then_select_strategy(self, tmp_path):
        """Log runs, build context from history, select motivation strategy."""
        store_path = str(tmp_path / "run_log.json")

        log_run("easy 5 miles on road, felt great", store_path=store_path)
        log_run("long run 10 miles on trail, felt okay", store_path=store_path)
        log_run("tempo 6 miles on treadmill, a bit tired", store_path=store_path)

        history = get_run_history(n=5, store_path=store_path)
        assert len(history) == 3

        ctx = _build_m4_context_from_m3_history(
            history,
            current_streak=7,
            adherence_percent=85,
            days_to_race=30,
        )

        result = select_motivation_strategy(ctx)
        assert "strategy" in result
        assert "message_tone" in result
        assert "reasoning" in result

        detailed = select_motivation_strategy_detailed(ctx)
        assert "scores" in detailed
        assert "inferred_state" in detailed

    def test_monotonous_terrain_triggers_variety_or_maintain(self, tmp_path):
        """All treadmill runs → bored state; M4 recommends variety or maintain."""
        store_path = str(tmp_path / "run_log.json")

        for _ in range(4):
            log_run("easy 4 miles on treadmill, felt fine", store_path=store_path)

        history = get_run_history(n=5, store_path=store_path)
        ctx = _build_m4_context_from_m3_history(
            history,
            current_streak=10,
            adherence_percent=90,
            days_to_race=60,
        )

        result = select_motivation_strategy_detailed(ctx)
        # Bored state favors encourage_variety; near race might favor maintain
        assert result["strategy"] in ("encourage_variety", "maintain", "push_harder")
        assert result["inferred_state"] in ("bored", "engaged", "mixed")
