"""Build the static console's scenario reports from the Python decision engine."""

import json
from pathlib import Path

from assurance.engine import SCENARIO_DIR, assess, load_scenario

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site" / "reports"

OUTPUT.mkdir(parents=True, exist_ok=True)
for scenario_path in sorted(SCENARIO_DIR.glob("*.yaml")):
    if scenario_path.stem == "controls":
        continue
    report = assess(load_scenario(scenario_path.stem))
    (OUTPUT / f"{scenario_path.stem}.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
