# Decision and evidence semantics

## Control evaluation

Each control declares a required state, owner, severity, blocking flag, evidence identifiers and maximum evidence age. The evaluator uses the scenario assessment date, not the machine clock, so repeated runs of a scenario are deterministic.

- `PASS`: required state matches and linked evidence is present, current and verified.
- `PARTIAL`: evidence is incomplete for a non-critical control or explicitly marked partial.
- `FAIL`: available state or failed evidence demonstrates that the requirement is not met.
- `ABSTAIN`: critical evidence is absent or stale, or the scenario declares material disagreement between state sources.

Evidence fixtures recognize `VERIFIED`, `ASSERTED`, `PARTIAL`, `FAILED`, `STALE` and `MISSING`. Assertions and partial evidence produce a partial result; failed evidence produces a control failure; stale or missing evidence follows the freshness/uncertainty rule.

Evidence age is measured in whole calendar days from `observed_at` to assessment `as_of`. An item older than the control's `freshness_days` is stale. Evaluated reports relabel the evidence status `STALE` and include its age and freshness limit. A missing or stale critical item yields `ABSTAIN`; the engine never turns missing evidence into a pass.

## Decision precedence

1. A blocking `FAIL` produces `NO-GO`.
2. Otherwise, any `ABSTAIN` produces `ABSTAIN`.
3. Otherwise, any `PARTIAL` or non-blocking `FAIL` produces `CONDITIONAL GO` and an owner-linked condition.
4. Otherwise, the result is `GO`.

An explicit state conflict is provided by `state_conflicts` in a scenario. A state that simply fails the declared requirement is a control failure; conflicting observations are uncertainty and cause abstention.

## Qualitative risk

Every control declares `inherent_risk`, `risk_treatment` and a `go_live_impact`. The report applies a categorical mapping to the control result: `PASS` moves one ordinal category down, `PARTIAL` leaves it unchanged, `FAIL` moves one category up, and `ABSTAIN` leaves it unchanged with effectiveness `UNDETERMINED`. The ordered labels are `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. The mapping is deterministic and explainable; it is not a score, probability, loss estimate or calibrated risk model. Risk categories and treatments require local governance approval.

## Third-party and governance records

Each synthetic product profile includes provider category, criticality, declared assurance status, evidence date and freshness threshold, dependency concentration, materiality, remediation and any exception. Evidence freshness is evaluated at the scenario's `as_of` date. An expired record is reported `STALE`; the register does not independently validate the provider or evidence.

Controls map to illustrative governance objectives. Reports expose objective-to-control IDs, linked evidence IDs and observed control statuses for traceability. The mapping supports preparation and review; it does not assert legal or regulatory compliance, audit completion or certification.

## Product profiles and lifecycle

`go` and `crypto_etp` use the same shared control registry and evaluator. The Crypto ETP scenario changes the product label, dependencies and lifecycle while retaining synthetic states and evidence. Lifecycle steps are descriptive presentation metadata and do not alter control outcomes.

## Coverage

Evidence coverage is the percentage of in-scope controls with at least one linked evidence record and no missing or stale linked item. Coverage does not measure evidence quality or prove control effectiveness. Control outcomes remain separately visible.

## Evidence boundary

The sample evidence sources and references are synthetic strings. No cryptographic signature verification, external source authentication, chain query or custody-system integration is performed. A `VERIFIED` label means only that the scenario fixture represents the item as verified for demonstration purposes.
