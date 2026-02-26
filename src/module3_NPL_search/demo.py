"""
Demo script for RunLogParser.

Usage:

    # Run predefined demo examples
    python demo.py

    # Interactive mode
    python demo.py --interactive

    # Optional: specify Word2Vec model path
    python demo.py --model path/to/word2vec.model
"""

import argparse
import json
import sys
import os
from pprint import pprint

# Add the 'src' directory to sys.path so that 'moduel3_NPL_search' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.module3_NPL_search.parser import RunLogParser


def run_examples(parser: RunLogParser) -> None:
    """Run predefined demo examples."""
    examples = [
        "Did my long run on the trail today, 10 miles at 9:30 pace. "
        "Felt pretty tired by mile 8 but the soft surface helped my shins",

        "Easy 4mi recovery jog on the road, about 8:45/mi. Felt great and relaxed.",

        "Track workout: 6x800m, averaged 6:10 pace. Legs were cooked by the end.",
    ]

    for i, text in enumerate(examples, start=1):
        print(f"\n--- Example {i} ---")
        print("Input:")
        print(text)
        print("\nParsed Output:")

        result = parser.parse(text)
        pprint(result)


def run_interactive(parser: RunLogParser) -> None:
    """Interactive CLI mode."""
    print("RunLogParser Interactive Mode")
    print("Type a run description (or 'quit' to exit)\n")

    while True:
        user_input = input("> ")

        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        try:
            result = parser.parse(user_input)
            print("\nStructured Output:")
            print(json.dumps(result, indent=4))
            print()
        except ValueError as e:
            print(f"Error: {e}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="RunLogParser Demo")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional path to Word2Vec model",
    )

    args = parser.parse_args()

    run_parser = RunLogParser(model_path=args.model)

    if args.interactive:
        run_interactive(run_parser)
    else:
        run_examples(run_parser)


if __name__ == "__main__":
    main()