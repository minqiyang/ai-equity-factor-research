# Current Roadmap

Updated: 2026-08-24 after protected merges of Track A PR 3 (#187) and the
README program-status sync (#188).

Canonical responsibility: program stage sequence, dependency order, gate and
completion criteria, and coarse stage status.

This is the canonical roadmap.

Repository authority is [AGENTS.md](../AGENTS.md), workflow behavior is owned by
the [controller](codex_long_running_controller.md), and the timestamped
operational checkpoint is in the [current handoff](current_handoff.md).

## Program Position

- Historical CCA1 start baseline:
  `c178d16d84a455774bcde73f21a9e3ff39ea7b2c`.
- Last live-verified protected main when this roadmap was authored:
  `cc90b34602ee54117ac5bca2445a73b7cac7b90a`.
- Track A PR 1 is complete through PR #177: the EODHD diagnostic scope,
  three-factor protocol, and exact 14-semantic-trial inventory are frozen.
- Stage 1 (private entitlement, retention, and publication) is accepted.
  The public-safe record is `docs/stage1_accepted_public_record_v1.json`.
- Track A PR 2 public validator, allowlisted projection, and safe
  dataset-review fields are on `main` through PR #186. See
  `docs/track_a_pr2_public_status_v1.json`.
- Blinded dataset-review class is `diagnostic_only`. Campaign dataset
  acceptance under the diagnostic ceiling is `DIAGNOSTIC_READY`, bound by
  hash in the public PR 2 status record. Formal interpretation acceptance is
  not granted. The evidence ceiling remains `DIAGNOSTIC_ONLY`.
- Track A PR 3 bounded diagnostic runner code is on `main` through PR #187.
  Shippable surface: `src/campaign/` with committed synthetic fixtures. The
  14-trial run has not executed.
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
- [Stage 1 public-safe record](stage1_accepted_public_record_v1.json),
  [identity-evidence aggregates](identity_evidence_public_aggregate_v1.json),
  [Track A PR 2 public status](track_a_pr2_public_status_v1.json), and
  [bounded diagnostic runner note](campaign_bounded_diagnostic_runner_v1.md):
  hashes, counts, and public package surfaces only.

## Active Dependency Chain

| Order | Stage | Status | Dependency or completion criterion |
| --- | --- | --- | --- |
| 1 | Private entitlement, retention, and publication gate | Accepted 2026-08-22 | Accepted private capability and written-term record exists; public-safe hashes are in `docs/stage1_accepted_public_record_v1.json`. |
| 2 | Track A PR 2: dataset manifest and validation | Public validator and status on `main`; campaign acceptance `DIAGNOSTIC_READY` under `DIAGNOSTIC_ONLY`; formal interpretation not granted | Complete for the diagnostic track when validator, safe projection, freeze binding hashes, blinded `diagnostic_only` review, and `DIAGNOSTIC_READY` acceptance hashes are recorded. Formal promotion remains a later gate. |
| 3 | Track A PR 3: bounded diagnostic runner | Code on `main` via PR #187 | Complete when shippable runner code and synthetic golden fixtures satisfy the binding PR 3 acceptance criteria below. Does not include a result-bearing 14-trial run. |
| 4 | Detached pre-run binding | Next; not complete | Complete only when exact code, configuration, environment, protocol, inventory, and accepted-dataset identities are bound outside the repository and the runner refuses result-bearing work until that binding verifies. |
| 5 | Track A PR 4: frozen diagnostic evidence | Blocked by stage 4 | Complete only after all 14 trials run once, every outcome is retained externally, and an approved safe aggregate projection is produced. |
| 6 | Track B minimal formal evidence runtime | Deferred until Track A closes | Required before prospective performance access or formal promotion; not a Track A prerequisite. |

## Parallel Dataset-Independent Protocol-Core Lane

Frozen protocol-core modules may proceed when the exact computation is already
frozen, a committed golden fixture exists, and no dataset-specific input or
result access is required. After PR #187, much of that surface now lives in
`src/campaign/` and related packages on `main`.

This lane does not replace Stage 4 binding or Stage 5 evidence. Later or
still-external concerns include:

- private-data access and provider panel assembly;
- detached run binding and environment lock;
- result-bearing fourteen-trial execution;
- D8 materialization;
- A2 exchange retrieval;
- formal interpretation and promotion.

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

Stage 1 is accepted. Track A PR 2 public surfaces and campaign
`DIAGNOSTIC_READY` acceptance hashes are recorded under `DIAGNOSTIC_ONLY`.
Track A PR 3 runner code is on `main`. The next completion gate is detached
pre-run binding. The handoff owns the timestamped operational checkpoint.

This section defines dependency and completion state only. It grants no
authority and adds no vendor, data, publication, or interpretation rule beyond
the linked canonical sources.

## Deferred And Out Of Scope

Broad factor-zoo expansion, formal statistics, strategy promotion, independent
cross-provider replication, LEAN parity, and completion of the remaining 26
optional ledger event schemas are outside the active queue.

Authority and execution remain in [AGENTS.md](../AGENTS.md) and the
[controller](codex_long_running_controller.md). The latest checkpoint is in
the [handoff](current_handoff.md).
