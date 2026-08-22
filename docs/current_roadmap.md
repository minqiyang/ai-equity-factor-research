# Current Roadmap

Updated: 2026-08-22 after owner acceptance of the Stage 1 entitlement, retention, and publication record.

Canonical responsibility: program stage sequence, dependency order, gate and
completion criteria, and coarse stage status.

This is the canonical roadmap.

Repository authority is [AGENTS.md](../AGENTS.md), workflow behavior is owned by
the [controller](codex_long_running_controller.md), and the timestamped
operational checkpoint is in the [current handoff](current_handoff.md).

## Program Position

- Historical CCA1 start baseline:
  `c178d16d84a455774bcde73f21a9e3ff39ea7b2c`.
- Last live-verified protected main:
  `aacfa58cc6e0e9d7e50a50ef7bd99b3a73bbcf57`.
- PR #180 and PR #181 are merged. No pull request was open at the verified
  start of this work.
- Track A PR 1 is complete through PR #177: the EODHD diagnostic scope,
  three-factor protocol, and exact 14-semantic-trial inventory are frozen.
- Governance source convergence and the subsequent handoff and lifecycle work
  are complete through PR #181. They changed no campaign protocol, research
  runtime, private data, or empirical conclusion.
- Stage 1 (private entitlement, retention, and publication) is accepted.
  The public-safe record is `docs/stage1_accepted_public_record_v1.json`.
- The evidence ceiling remains `DIAGNOSTIC_ONLY`. No dataset or formal
  interpretation has been accepted.
- The 2025-05-01 through 2026-05-31 interval remains permanently
  `historical_evaluation`, never a pristine holdout.

## Canonical Research Sources

- [Research program charter](research_program_charter.md): long-term evidence
  policy and evidence-state boundaries.
- [Track A/Track B campaign contract](eodhd_sp500_diagnostic_campaign_contract.md):
  scope, private-data gate, freeze sequence, and stop conditions.
- [Canonical preregistration](preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml)
  and [trial inventory](preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json):
  frozen protocol and exactly 14 semantic trials.
- [Point-in-time methodology contract](point_in_time_data_methodology_contract.md):
  dataset review and formal-interpretation requirements.
- [Repository map](repo_map.md): accepted timing, split, ledger, and schema
  contracts without duplicating their semantics here.
- [Decision log](decision_log.md), [engineering log](engineering_log.md), and
  [troubleshooting log](troubleshooting_log.md): historical evidence, not queues.
- [Stage 1 public-safe record](stage1_accepted_public_record_v1.json) and
  [identity-evidence aggregates](identity_evidence_public_aggregate_v1.json):
  hashes and counts only.

## Active Dependency Chain

| Order | Stage | Status | Dependency or completion criterion |
| --- | --- | --- | --- |
| 1 | Private entitlement, retention, and publication gate | Accepted 2026-08-22 | Accepted private capability and written-term record exists; public-safe hashes are in `docs/stage1_accepted_public_record_v1.json`. |
| 2 | Track A PR 2: dataset manifest and validation | Eligible | Complete with an accepted provider-bound manifest, validator, safe projection, and blinded dataset-review decision. |
| 3 | Track A PR 3: bounded diagnostic runner | Blocked by accepted PR 2 review | Complete only with an accepted bounded runner implementing the frozen protocol and deterministic validation surface. |
| 4 | Detached pre-run binding | Blocked by protected PR 3 merge | Complete only when exact code, configuration, environment, protocol, inventory, and accepted dataset identities are bound outside the repository. |
| 5 | Track A PR 4: frozen diagnostic evidence | Blocked by stages 3 and 4 | Complete only after all 14 trials run once, every outcome is retained externally, and an approved safe aggregate projection is produced. |
| 6 | Track B minimal formal evidence runtime | Deferred until Track A closes | Required before prospective performance access or formal promotion; not a Track A prerequisite. |

## Parallel Dataset-Independent Protocol-Core Lane

Frozen protocol-core modules may be implemented in parallel with the owner-side
EODHD gate only when all three conditions hold:

- The exact computation is already frozen in the accepted campaign artifacts.
- A committed golden fixture exists for that computation.
- The work requires no dataset-specific input or result access.

This lane is neither Track A PR 2 nor Track A PR 3. Track A PR 2 and PR 3
keep exclusive ownership of starting, satisfying, and unblocking those
stages. The frozen protocol, preregistration, and 14-trial inventory stay as
already accepted.
The lane implements frozen golden-backed protocol-core modules that already
have committed fixtures. Later stages own:

- ingestion;
- security-master construction;
- historical membership;
- alias lineage;
- terminal/delisting-return semantics;
- decision-time eligibility;
- benchmark-membership construction;
- runner orchestration;
- private-data access;
- result-bearing execution.

## Binding Track A PR 3 Acceptance Criteria

Track A PR 3 must satisfy all of the following:

- Committed golden fixtures execute against shippable runner code rather than
  test-local closures.
- Each frozen factor ID maps to exactly one explicit implementation validated
  by its golden and anchor-mutation fixtures.
- Generic helper defaults never define campaign semantics.
- The factor-matched equal-weight benchmark is canonical and strict: it uses no
  fill, interpolation, or survivor renormalization, and invalid comparisons are
  retained and routed under the frozen contract.

## Gate Completion Criteria

Stage 1 is accepted as of 2026-08-22. Stage 2 is eligible. Qualifying
dataset-independent protocol-core work proceeds in the parallel lane above.
The handoff owns the timestamped operational checkpoint.

## Deferred And Out Of Scope

Broad factor-zoo expansion, formal statistics, strategy promotion, independent
cross-provider replication, LEAN parity, and completion of the remaining 26
optional ledger event schemas are outside the active queue.

Authority and execution remain in [AGENTS.md](../AGENTS.md) and the
[controller](codex_long_running_controller.md). The latest checkpoint is in
the [handoff](current_handoff.md).
