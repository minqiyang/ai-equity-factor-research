# Current Roadmap

Updated: 2026-09-05 after owner-accepted Astra R1 terminal disposition and roadmap alignment.

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
  `027e8ae`.
- PR #180 and PR #181 are merged. No pull request was open at the verified
  start of this work.
- Track A PR 1 is complete through PR #177: the EODHD diagnostic scope,
  three-factor protocol, and exact 14-semantic-trial inventory are frozen.
- Governance source convergence and the subsequent handoff and lifecycle work
  are complete through PR #181. They changed no campaign protocol, research
  runtime, private data, or empirical conclusion.
- Stage 1 (private entitlement, retention, and publication) is accepted.
  The public-safe record is `docs/stage1_accepted_public_record_v1.json`.
- The evidence ceiling remains `DIAGNOSTIC_ONLY`. A blinded dataset-review
  decision of `diagnostic_only` exists and campaign acceptance is
  `DIAGNOSTIC_READY`, bound by hash. Formal interpretation is not accepted.
- Track A PR 2 public validator and status are on protected main through
  PR #186. Track A PR 3 runner code is on protected main through PR #187.
- Stage 4 G-2 binding is accepted by hash. Stage 4 is not fully complete.
  14-trial remains REFUSED, reason ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL.
  Terminal refusal is disposition, not PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY.
- Synthetic Track B is separately eligible and not blocked by success-only Track A close.
- D8, A2, identity reopen, result/performance access stay closed.
- No private paths, tickers, prices, or performance values.
- Do not claim v6 accepted or runtime delivered.
- Optional 37-event completion and factor-zoo stay off the critical path.
- First future empirical slice is later/planning; do not authorize data access here.
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
  and [Track A PR 2 public status](track_a_pr2_public_status_v1.json):
  hashes and counts only.

## Active Dependency Chain

| Order | Stage | Status | Dependency or completion criterion |
| --- | --- | --- | --- |
| 1 | Private entitlement, retention, and publication gate | Accepted 2026-08-22 | Accepted private capability and written-term record exists; public-safe hashes are in `docs/stage1_accepted_public_record_v1.json`. |
| 2 | Track A PR 2: dataset manifest and validation | Public validator on main; campaign `DIAGNOSTIC_READY`; formal interpretation not granted | Complete for the diagnostic track with validator, safe projection, freeze hashes, blinded `diagnostic_only` review, and `DIAGNOSTIC_READY` hashes. |
| 3 | Track A PR 3: bounded diagnostic runner | Code on main via PR #187 | Complete when shippable runner code and synthetic golden fixtures satisfy the binding PR 3 acceptance criteria. Does not include a 14-trial run. |
| 4 | Detached pre-run binding | G-2 accepted; 14-trial remains REFUSED | Complete only when exact code, configuration, environment, protocol, inventory, and accepted dataset identities are bound outside the repository. G-2 is accepted by hash; 14-trial remains REFUSED, reason ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL. Terminal refusal is disposition, not PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY. |
| 5 | Track A PR 4: frozen diagnostic evidence | Terminal disposition; 14-trial remains REFUSED | Terminal refusal is disposition, not PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY. The 14-trial run remains REFUSED and did not execute. |
| 6 | Track B minimal formal evidence runtime | Separately eligible | Synthetic Track B is separately eligible and not blocked by success-only Track A close. Do not claim v6 accepted or runtime delivered; Path A is first runtime checkpoint only after accepted plan and design candidate. |

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

Stage 1 is accepted. Track A PR 2 public surfaces and campaign
`DIAGNOSTIC_READY` hashes are recorded under `DIAGNOSTIC_ONLY`. Track A PR 3
runner code is on protected main. Stage 4 G-2 binding is accepted by hash.
14-trial remains REFUSED, reason ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL.
Terminal refusal is disposition, not PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY.
Synthetic Track B is separately eligible and not blocked by success-only Track A close.
D8, A2, identity reopen, result/performance access stay closed.
No private paths, tickers, prices, or performance values.
Do not claim v6 accepted or runtime delivered.
Optional 37-event completion and factor-zoo stay off the critical path.
First future empirical slice is later/planning; do not authorize data access here.
The handoff owns the timestamped operational checkpoint.

This section defines dependency and completion state only. It grants no
authority and adds no vendor, data, publication, or interpretation rule beyond
the linked canonical sources.

## Deferred And Out Of Scope

Optional 37-event completion and factor-zoo stay off the critical path.
Broad factor-zoo expansion, formal statistics, strategy promotion, independent
cross-provider replication, LEAN parity, and completion of the remaining 26
optional ledger event schemas are outside the active queue. First future
empirical slice is later/planning; do not authorize data access here.

Authority and execution remain in [AGENTS.md](../AGENTS.md) and the
[controller](codex_long_running_controller.md). The latest checkpoint is in
the [handoff](current_handoff.md).
