#!/usr/bin/env python3
"""
Module 3 demo: one runner, three runs with different moods and workout types.

Run from project root:  PYTHONPATH=. python3 demo_module3.py
"""

from src.module3_run_logger import parse_run, log_run, get_run_history

DEMO_LOG = "data/run_log.json"

# One runner, three different inputs: varied workout types and moods
RUNS = [
    "easy 5 miles on the road, felt great",
    "long run 10 miles on trail at 9:30 pace, felt tired by mile 8",
    "track intervals today, exhausted after but proud I finished",
]


def main():
    print("Module 3: Natural Language Run Logger")
    print("One runner — 3 runs (different workout types & moods)\n")

    # 1. Parse all three
    print("--- Parse ---")
    for text in RUNS:
        out = parse_run(text)
        dist = out["distance"] if out.get("distance") is not None else "—"
        print(f"  \"{text}\"")
        print(f"  -> type={out['type']}, distance={dist}, terrain={out['terrain']}")
        print(f"     mood={out['sentiment']}, effort={out['effort']}\n")

    # 2. Log all three as the same runner
    print("--- Log (same runner) ---")
    for text in RUNS:
        rid = log_run(text, store_path=DEMO_LOG)
        print(f"  {rid}: {text}")

    # 3. Show this runner's history (all 3)
    print("\n--- Runner history (last 3) ---")
    for run in get_run_history(n=3, store_path=DEMO_LOG):
        p = run["parsed"]
        dist = p["distance"] if p.get("distance") is not None else "—"
        print(f"  {run['id']}: {p['type']}, {dist} mi, {p['terrain']} | mood={p['sentiment']}, effort={p['effort']}")

    print(f"\nLog file: {DEMO_LOG}")


if __name__ == "__main__":
    main()
