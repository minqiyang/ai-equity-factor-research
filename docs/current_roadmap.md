# Current Roadmap

Updated: 2026-08-01 after the protected merge of PR #177.

Canonical responsibility: active stage status, dependencies, and completion
evidence. Repository authority is owned by [AGENTS.md](../AGENTS.md), and staged
workflow behavior is owned by the
[Codex long-running controller](codex_long_running_controller.md). This is the canonical roadmap.

## Current State

- Protected `main`: `f50b6e77b0c3a0226e246459e2a394d1489210ac`, the
  merge commit for PR #177.
- PR #177 final branch head:
  `c04133315911c74c96e77984b5968792434aee8f`.
- Completed delivery: Track A PR 1, the EODHD diagnostic scope and protocol
  freeze.
- Current research gate: private entitlement, retention, and publication
  evidence. This gate is not yet satisfied.
- Current evidence ceiling: `DIAGNOSTIC_ONLY`. No dataset, formal
  interpretation, profitability claim, deployment, brokerage, paper, live, or
  real-money activity is accepted or authorized.
- The 2025-05-01 through 2026-05-31 interval remains permanently
  `historical_evaluation`, never a pristine holdout.

The [current handoff](current_handoff.md) remains a detailed branch snapshot
pending refresh; its pre-merge PR #177 status does not supersede this evidence.

## Authoritative Research Sources

- [Research program charter](research_program_charter.md): long-term evidence
  policy and evidence-state boundaries.
- [docs/eodhd_sp500_diagnostic_campaign_contract.md](eodhd_sp500_diagnostic_campaign_contract.md):
  Track A/Track B scope, private-data gate, freeze sequence, and stop conditions.
- [Canonical preregistration](preregistrations/eodhd_sp500_three_factor_diagnostic_v1.yaml):
  frozen three-factor diagnostic protocol.
- [Canonical trial inventory](preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json):
  exactly 14 semantic trials.
- [docs/point_in_time_data_methodology_contract.md](point_in_time_data_methodology_contract.md):
  dataset review and formal-interpretation requirements.
- [Decision log](decision_log.md), [engineering log](engineering_log.md), and
  [troubleshooting log](troubleshooting_log.md): retained historical evidence,
  not active task queues.

Accepted ledger/schema contracts remain indexed, without duplicating semantics:
[design](experiment_trial_ledger_contract.md) (`docs/experiment_trial_ledger_contract.md`) and [R0](experiment_trial_ledger_schema_registry_contract.md) (`docs/experiment_trial_ledger_schema_registry_contract.md`);
[R1A/R1B](experiment_trial_ledger_allocation_registration_schema_contract.md) (`docs/experiment_trial_ledger_allocation_registration_schema_contract.md`) and [R1C](experiment_trial_ledger_trial_family_registration_schema_contract.md) (`docs/experiment_trial_ledger_trial_family_registration_schema_contract.md`);
[R1D](experiment_trial_ledger_sample_registration_schema_contract.md) (`docs/experiment_trial_ledger_sample_registration_schema_contract.md`) and [R1E](experiment_trial_ledger_binding_schema_contract.md) (`docs/experiment_trial_ledger_binding_schema_contract.md`);
[R1F](experiment_trial_ledger_trial_allocation_schema_contract.md) (`docs/experiment_trial_ledger_trial_allocation_schema_contract.md`) and [R1G](experiment_trial_ledger_campaign_inventory_seal_schema_contract.md) (`docs/experiment_trial_ledger_campaign_inventory_seal_schema_contract.md`);
[R1H](experiment_trial_ledger_attempt_allocation_schema_contract.md) (`docs/experiment_trial_ledger_attempt_allocation_schema_contract.md`) and [R1I](experiment_trial_ledger_attempt_start_schema_contract.md) (`docs/experiment_trial_ledger_attempt_start_schema_contract.md`).
Timing and split contracts remain discoverable through the [repository map](repo_map.md).

## Completed Foundations

| Foundation | Status | Evidence boundary |
| --- | --- | --- |
| Research charter and split isolation | Complete | Research policy and purged, bounded split behavior are accepted on protected `main`. |
| Signal and execution timing | Complete | The after-close/next-observed-close contract and implementation are accepted on protected `main`. |
| Point-in-time methodology | Contract complete | No provider, license, dataset, universe, field, benchmark, or historical claim is accepted by the methodology alone. |
| 4b-R1E. Campaign-entity and Stage 3 sample-reference binding schemas | Complete on protected main via PR #171 | Contract/schema evidence only. |
| 4b-R1F. Semantic trial-allocation schema | Complete on protected main via PR #172 | Contract/schema evidence only. |
| 4b-R1G. Initial campaign-inventory-seal schema | Complete on protected main via PR #173 | Contract/schema evidence only. |
| 4b-R1H. Attempt-allocation schema | Complete on protected main via PR #174 | Contract/schema evidence only. |
| 4b-R1I. Attempt-start schema | Complete on protected main via PR #176 | The accepted R0-R1I releases remain optional `full_ledger_profile_v1`; they do not provide a stateful evidence runtime. |
| Track A PR 1 protocol freeze | Complete via PR #177 | The provider-bounded three-factor protocol and unique 14-trial inventory are frozen; no research runtime ran and no performance was calculated. |

## Active Dependency Chain

| Order | Stage | Status | Dependency or completion evidence |
| --- | --- | --- | --- |
| 1 | Track A private entitlement, retention, and publication gate | Current; pending private evidence | Record the exact existing capability and written permitted-use, retention, publication, and deletion terms. A purchase is not authorized. |
| 2 | Track A PR 2: dataset manifest and validation | Dataset-bound work blocked by stage 1 | The manifest, provider-bound validator, safe projection, and non-self-issued blinded dataset decision begin only after the private gate. Generic provider-agnostic schema or validator preparation is separate and cannot satisfy or start PR 2. |
| 3 | Track A PR 3: bounded diagnostic runner | Blocked by an accepted PR 2 dataset review | Implement only the frozen protocol and its deterministic validation surface; do not add trials or interpret results. |
| 4 | Detached pre-run binding | Blocked by protected PR 3 merge | Before any result-bearing job, bind exact code, configuration, environment, protocol, inventory, and accepted dataset identities outside the repository. |
| 5 | Track A PR 4: frozen diagnostic evidence | Blocked by stages 3 and 4 | Run and reconcile all 14 trials once, retain every outcome externally, and publish only an approved safe aggregate projection. |
| 6 | Track B minimal formal evidence runtime | Deferred until Track A closes | Required before prospective performance access or formal evidence promotion; not a Track A prerequisite. |

Broad factor-zoo expansion, formal statistics, strategy promotion, independent
cross-provider replication, and LEAN parity remain outside the active queue.
Completing all 37 registry event schemas is optional hardening, not a Track A
dependency.

## Current Gate Evidence And Blockers

The next gate determines whether existing access supports historical membership evidence and whether written terms permit retention and safe public outputs; the campaign contract owns the exact required record and allowed content.

Current blockers are:

- historical-index-membership capability has not been privately established;
- frozen-snapshot retention and deletion duties have not been recorded;
- public noncommercial derived-output permission has not been recorded; and
- no dataset manifest or blinded dataset-review decision has been accepted.

Do not purchase or expand vendor access, expose credentials or provider
responses, commit licensed/private rows or paths, publish derived counts or
hashes, or inspect performance under this roadmap. Until the private gate is
satisfied, any separately authorized public preparation must remain generic and
provider-agnostic within the campaign contract; do not create or bind PR 2's
dataset manifest, provider validator, safe projection, or review decision.
Missing entitlement or unresolved permission requires owner input; it is not
permission to broaden scope.

## PR #177 Completion Evidence

- Merge commit `f50b6e77b0c3a0226e246459e2a394d1489210ac` has parents
  `6386c59c53b407765c5dba7fcfe7879fa0433356` and the final PR head
  `c04133315911c74c96e77984b5968792434aee8f`.
- The merged campaign contract points to the canonical preregistration and
  trial inventory; structure tests enforce a semantic-trial count of 14, 14
  entries, and 14 unique trial IDs.
- The final-head engineering record reports 71 focused structure tests and
  3,098 full-suite tests passed with two platform-conditional skips, together
  with Ruff, compile, Skill, artifact-build, repo-map, diff, privacy, and
  Unicode/control checks.
- The merged scope records no vendor access, private row, performance value,
  purchase, research runtime execution, brokerage, paper, or live action.

This roadmap grants no authority. Use [AGENTS.md](../AGENTS.md) for authority
and the [Codex long-running controller](codex_long_running_controller.md) for
stage execution, review, waiting, external gates, and stop behavior.
