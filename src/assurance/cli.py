"""Command-line report generator for the synthetic assurance scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import SCENARIO_DIR, assess, load_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a synthetic digital-asset assurance scenario")
    scenarios = sorted(path.stem for path in SCENARIO_DIR.glob("*.yaml") if path.stem != "controls")
    parser.add_argument("scenario", nargs="?", choices=scenarios, default="go")
    parser.add_argument("--output", type=Path, help="Write JSON report to this path")
    args = parser.parse_args()
    report = assess(load_scenario(args.scenario))
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
