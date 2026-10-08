"""Deterministic control, evidence, and go-live assessment logic."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "scenarios"


def load_scenario(name: str) -> dict[str, Any]:
    """Load a named synthetic scenario, rejecting path traversal and bad shapes."""
    if not name or Path(name).name != name or name.endswith((".yaml", ".yml")):
        raise ValueError(f"Unknown scenario: {name!r}")
    path = SCENARIO_DIR / f"{name}.yaml"
    if not path.is_file():
        raise ValueError(f"Unknown scenario: {name!r}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    controls = yaml.safe_load((SCENARIO_DIR / "controls.yaml").read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(controls, list):
        raise TypeError(f"Invalid scenario file: {path.name}")
    return {**data, "controls": controls}


def _parse_date(value: str) -> date:
    try:
        return datetime.fromisoformat(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid ISO date: {value!r}") from exc


def assess(scenario: dict[str, Any], *, today: date | None = None) -> dict[str, Any]:
    """Evaluate each declared control and produce a transparent decision report."""
    as_of = today or date.fromisoformat(scenario["as_of"])
    evidence_by_id = {item["id"]: item for item in scenario.get("evidence", [])}
    results: list[dict[str, Any]] = []

    for control in scenario["controls"]:
        evidence = [evidence_by_id[eid] for eid in control.get("evidence_ids", []) if eid in evidence_by_id]
        missing = [eid for eid in control.get("evidence_ids", []) if eid not in evidence_by_id]
        missing.extend(item["id"] for item in evidence if item["status"] == "MISSING")
        stale = [item for item in evidence if item["status"] == "STALE" or (as_of - _parse_date(item["observed_at"])).days > control["freshness_days"]]
        stale_ids = {item["id"] for item in stale}
        evaluated_evidence = [
            {
                **item,
                "declared_status": item["status"],
                "status": "STALE" if item["id"] in stale_ids else item["status"],
                "age_days": (as_of - _parse_date(item["observed_at"])).days,
                "freshness_days": control["freshness_days"],
            }
            for item in evidence
        ]
        failed_evidence = [item for item in evidence if item["status"] == "FAILED"]
        actual = scenario.get("system_state", {}).get(control["state_key"])
        expected = control["expected_state"]
        conflict = control["state_key"] in scenario.get("state_conflicts", [])

        if conflict:
            status, finding = "ABSTAIN", f"System state is {actual!r}; expected {expected!r}."
        elif failed_evidence or actual != expected:
            status, finding = "FAIL", "Available state or evidence demonstrates the requirement is not met."
        elif stale or missing:
            status = "ABSTAIN" if control["severity"] == "CRITICAL" else "PARTIAL"
            if stale:
                oldest = max(stale, key=lambda item: as_of - _parse_date(item["observed_at"]))
                age = (as_of - _parse_date(oldest["observed_at"])).days
                finding = (
                    f"Evidence {oldest['id']} is {age} days old; the control freshness threshold is "
                    f"{control['freshness_days']} days. The assurance engine cannot infer control "
                    "effectiveness from stale evidence."
                )
            else:
                finding = "Required evidence is missing; the assurance engine cannot infer control effectiveness."
        elif any(item["status"] in {"PARTIAL", "ASSERTED"} for item in evidence):
            status, finding = "PARTIAL", "Evidence supports only part of the requirement."
        else:
            status, finding = "PASS", "Required state and current evidence are consistent."

        results.append({
            **control,
            "status": status,
            "finding": finding,
            "system_state": actual,
            "evidence": evaluated_evidence,
            "missing_evidence": missing,
            "stale_evidence": [item["id"] for item in stale],
            "stale_details": [
                {"id": item["id"], "age_days": (as_of - _parse_date(item["observed_at"])).days,
                 "freshness_days": control["freshness_days"]}
                for item in stale
            ],
            "state_conflict": conflict,
        })

    failed = [item for item in results if item["status"] == "FAIL"]
    partial = [item for item in results if item["status"] == "PARTIAL"]
    abstentions = [item for item in results if item["status"] == "ABSTAIN"]
    blocking_failures = [item for item in failed if item["blocking"]]
    critical_abstentions = [item for item in abstentions if item["severity"] == "CRITICAL"]

    if blocking_failures:
        decision = "NO-GO"
        rationale = "A blocking control failure prevents a defensible go-live recommendation."
    elif critical_abstentions or abstentions:
        decision = "ABSTAIN"
        rationale = "Material evidence or system-state uncertainty prevents an assurance conclusion."
    elif partial or failed:
        decision = "CONDITIONAL GO"
        rationale = "No blocking failure was identified; listed remediation conditions remain open."
    else:
        decision = "GO"
        rationale = "All in-scope controls pass with current evidence and consistent system state."

    linked = sum(bool(item["evidence"]) and not item["missing_evidence"] and not item["stale_evidence"] for item in results)
    coverage = round(100 * linked / len(results)) if results else 0
    conditions = [
        {"control_id": item["id"], "owner": item["owner"], "requirement": item["remediation"]}
        for item in results if item["status"] in {"PARTIAL", "FAIL"}
    ]
    abstention_reasons = [f"{item['id']}: {item['finding']}" for item in abstentions]
    return {
        "product": scenario["product"],
        "scenario": scenario["scenario"],
        "scenario_key": scenario["scenario_key"],
        "as_of": as_of.isoformat(),
        "decision": decision,
        "rationale": rationale,
        "summary": {state: sum(item["status"] == state for item in results) for state in ("PASS", "PARTIAL", "FAIL", "ABSTAIN")},
        "control_count": len(results),
        "evidence_coverage_percent": coverage,
        "critical_findings": [item["id"] for item in results if item["severity"] == "CRITICAL" and item["status"] != "PASS"],
        "failed_controls": [item["id"] for item in failed],
        "partial_controls": [item["id"] for item in partial],
        "abstention_reasons": abstention_reasons,
        "conditions": conditions,
        "controls": results,
        "dependencies": scenario.get("dependencies", []),
        "synthetic": True,
    }
