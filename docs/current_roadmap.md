# Current Roadmap

Updated: 2026-08-01 after live verification of the CCA1 roadmap-correction baseline.

Canonical responsibility: program stage sequence, dependency order, gate and
completion criteria, and coarse stage status.

This is the canonical roadmap.

Repository authority is [AGENTS.md](../AGENTS.md), workflow behavior is owned by
the [controller](codex_long_running_controller.md), and the timestamped
operational checkpoint is in the [current handoff](current_handoff.md).

## Program Position

- The verified start baseline for this correction is
  `c178d16d84a455774bcde73f21a9e3ff39ea7b2c`.
- PR #180 and PR #181 are merged. No pull request was open at the verified
  start of this work.
- Track A PR 1 is complete through PR #177: the EODHD diagnostic scope,
  three-factor protocol, and exact 14-semantic-trial inventory are frozen.
- Governance source convergence and the subsequent handoff and lifecycle work
  are complete through PR #181. They changed no campaign protocol, research
  runtime, private data, or empirical conclusion.
- The current research gate is private entitlement, retention, and publication
  evidence. That gate is not yet satisfied.
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

## Active Dependency Chain

| Order | Stage | Status | Dependency or completion criterion |
| --- | --- | --- | --- |
| 1 | Private entitlement, retention, and publication gate | Current; pending private evidence | Complete only with an accepted private record under the campaign contract. |
| 2 | Track A PR 2: dataset manifest and validation | Blocked by stage 1 | Complete only with an accepted provider-bound manifest, validator, safe projection, and blinded dataset-review decision. Generic preparation cannot satisfy or start this stage. |
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

This lane is neither Track A PR 2 nor Track A PR 3. It does not start, satisfy,
or unblock either stage, does not satisfy the owner-side gate, and does not
reopen the frozen protocol, preregistration, or 14-trial inventory.
The following remain explicitly blocked:

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

Stage 1 completes only when the owner supplies an accepted private record of the
exact existing capability and written permitted-use, retention, publication,
and deletion terms required by the campaign contract. Until then, stage 2 and
all dataset-bound work remain blocked. Qualifying dataset-independent
protocol-core work may proceed only within the parallel lane above; it neither
completes this gate nor authorizes any blocked work. The handoff owns the
timestamped list of currently missing owner evidence.

This section defines dependency and completion state only. It grants no authority
and adds no vendor, data, publication, or interpretation rule beyond the linked
canonical sources.

## Deferred And Out Of Scope

Broad factor-zoo expansion, formal statistics, strategy promotion, independent
cross-provider replication, LEAN parity, and completion of the remaining 26
optional ledger event schemas are outside the active queue.

This roadmap grants no authority. Use [AGENTS.md](../AGENTS.md) for authority,
the [controller](codex_long_running_controller.md) for execution and external
gates, and the [handoff](current_handoff.md) for the latest recorded checkpoint.
