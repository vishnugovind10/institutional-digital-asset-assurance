from copy import deepcopy
from datetime import date

import pytest

from assurance.engine import assess, load_scenario


@pytest.mark.parametrize(
    ("name", "expected"),
    [("go", "GO"), ("conditional_go", "CONDITIONAL GO"), ("no_go", "NO-GO"), ("abstain", "ABSTAIN")],
)
def test_demonstration_scenarios(name: str, expected: str) -> None:
    report = assess(load_scenario(name))
    assert report["decision"] == expected
    assert report["synthetic"] is True


def test_blocking_contract_failure_has_remediation_and_evidence() -> None:
    report = assess(load_scenario("no_go"))
    control = next(item for item in report["controls"] if item["id"] == "SC-001")
    assert control["status"] == "FAIL"
    assert control["blocking"] is True
    assert control["evidence"][0]["reference"].startswith("sha256:")
    assert any(condition["control_id"] == "SC-001" for condition in report["conditions"])


def test_stale_critical_evidence_abstains_without_inference() -> None:
    report = assess(load_scenario("abstain"))
    control = next(item for item in report["controls"] if item["id"] == "CU-001")
    assert control["status"] == "ABSTAIN"
    assert control["stale_evidence"] == ["EV-CU-001"]
    assert report["evidence_coverage_percent"] < 100


def test_nonblocking_partial_generates_condition() -> None:
    report = assess(load_scenario("conditional_go"))
    assert report["decision"] == "CONDITIONAL GO"
    assert any(condition["control_id"] == "GV-001" for condition in report["conditions"])


def test_missing_critical_evidence_abstains() -> None:
    scenario = deepcopy(load_scenario("go"))
    scenario["evidence"] = [item for item in scenario["evidence"] if item["id"] != "EV-CU-001"]
    report = assess(scenario)
    assert report["decision"] == "ABSTAIN"
    assert "EV-CU-001" in next(item for item in report["controls"] if item["id"] == "CU-001")["missing_evidence"]


def test_conflicting_system_state_abstains() -> None:
    scenario = deepcopy(load_scenario("go"))
    scenario["state_conflicts"] = ["custody_authorization"]
    report = assess(scenario)
    assert report["decision"] == "ABSTAIN"
    assert "CU-001" in report["abstention_reasons"][0]


@pytest.mark.parametrize("status", ["PARTIAL", "ASSERTED"])
def test_non_verified_assertion_is_partial(status: str) -> None:
    scenario = deepcopy(load_scenario("go"))
    next(item for item in scenario["evidence"] if item["id"] == "EV-GV-001")["status"] = status
    report = assess(scenario)
    assert next(item for item in report["controls"] if item["id"] == "GV-001")["status"] == "PARTIAL"


def test_explicit_stale_and_missing_evidence_states_are_supported() -> None:
    scenario = deepcopy(load_scenario("go"))
    next(item for item in scenario["evidence"] if item["id"] == "EV-CU-001")["status"] = "STALE"
    report = assess(scenario)
    assert report["decision"] == "ABSTAIN"
    assert "EV-CU-001" in next(item for item in report["controls"] if item["id"] == "CU-001")["stale_evidence"]
    scenario = deepcopy(load_scenario("go"))
    next(item for item in scenario["evidence"] if item["id"] == "EV-CU-001")["status"] = "MISSING"
    report = assess(scenario)
    assert report["decision"] == "ABSTAIN"


def test_evidence_freshness_uses_assessment_date() -> None:
    report = assess(load_scenario("go"), today=date(2026, 11, 20))
    assert report["decision"] == "ABSTAIN"


def test_path_traversal_and_unknown_scenario_are_rejected() -> None:
    with pytest.raises(ValueError):
        load_scenario("../go")
    with pytest.raises(ValueError):
        load_scenario("unknown")
