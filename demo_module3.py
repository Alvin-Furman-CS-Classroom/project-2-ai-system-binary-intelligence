#!/usr/bin/env python3
"""
Module 3 demo: parse free-text runs, log to JSON, show history.

Run from project root:  PYTHONPATH=. python3 demo_module3.py
"""

from src.module3_run_logger import parse_run, log_run, get_run_history

DEMO_LOG = "data/demo_run_log.json"


def main():
    print("Module 3: Natural Language Run Logger\n")

    # 1. Parse a few examples
    print("--- Parse ---")
    for text in ["easy 5 miles on the road, felt great", "long run 10 miles on trail at 9:30 pace, felt tired"]:
        out = parse_run(text)
        print(f"  {text[:50]}...")
        print(f"  -> type={out['type']}, distance={out['distance']}, terrain={out['terrain']}, sentiment={out['sentiment']}\n")

    # 2. Log two runs
    print("--- Log ---")
    for text in ["easy 5 miles on the road", "long run 12 miles on trail at 9:00 pace"]:
        rid = log_run(text, store_path=DEMO_LOG)
        print(f"  {rid}: {text}")

    # 3. Show recent history
    print("\n--- History (last 2) ---")
    for run in get_run_history(n=2, store_path=DEMO_LOG):
        p = run["parsed"]
        print(f"  {run['id']}: {p['type']}, {p['distance']} mi, {p['terrain']}")

    print(f"\nLog file: {DEMO_LOG}")


if __name__ == "__main__":
    main()
