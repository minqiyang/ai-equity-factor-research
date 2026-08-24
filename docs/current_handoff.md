# Current Handoff

Updated: 2026-08-24 after protected merges of Track A PR 3 (#187) and the
README program-status sync (#188).

Canonical responsibility: the latest recorded operational checkpoint, exact
last-verified repository and PR facts, immediate blockers or owner decisions,
and the next safe action.

Recorded remote facts are cached evidence and must be verified live before any
action. This file defines no authority, workflow policy, research methodology,
stage dependency, or historical review narrative.

## Resume Order

1. Read `AGENTS.md` for repository authority and research-safety boundaries.
2. Read `docs/current_handoff.md` for the latest recorded operational checkpoint.
3. Read `docs/codex_long_running_controller.md` for execution and external gates.
4. Read `docs/current_roadmap.md` for research-stage status and dependencies.

Use `docs/repo_map.md` only for targeted file orientation. Before acting, follow
the controller's live-remote, clean-tree, authorization, validation, and review
requirements.

## Latest Recorded Operational Checkpoint

- Last externally verified protected `main` when this handoff was authored:
  `cc90b34602ee54117ac5bca2445a73b7cac7b90a`.
- Historical CCA1 start baseline:
  `c178d16d84a455774bcde73f21a9e3ff39ea7b2c`.
- Stage 1 is accepted. Public-safe record:
  `docs/stage1_accepted_public_record_v1.json`.
- Track A PR 2 public validator and status are on `main` through PR #186.
  Public status: `docs/track_a_pr2_public_status.md` and
  `docs/track_a_pr2_public_status_v1.json`.
- Blinded dataset-review class remains `diagnostic_only`
  (`docs/dataset_review_public_projection_v1.json`).
- Campaign dataset acceptance under the diagnostic ceiling is
  `DIAGNOSTIC_READY`, bound by public hashes in the PR 2 status record.
  Formal interpretation acceptance is not granted. Evidence ceiling remains
  `DIAGNOSTIC_ONLY`.
- Track A PR 3 bounded diagnostic runner code is on `main` through PR #187
  merge `bcb169e80ccc1566321f08e201a808663366da15` (final PR head
  `4a67618a7571aaee8c49c1d100c6f12f36365b16`). Package surface:
  `src/campaign/` plus synthetic fixtures.
- README program status was refreshed through PR #188 merge
  `cc90b34602ee54117ac5bca2445a73b7cac7b90a`.
- The 14-trial diagnostic run has not executed. No performance values are
  published.
- Raw private data, ticker lists, provider responses, private filesystem
  paths, and full private control-tree bodies remain outside this repository.

## Recorded Delivery Scope

- Keep public GitHub current for another machine or reader: roadmap, handoff,
  decision log, engineering log, and public-safe status/hash records.
- Bind private manifests, freeze records, acceptance bodies, and evidence packs
  by hash only in public docs.
- Do not upload raw private data.

## Current Research Gate Summary

| Stage | Public status |
| --- | --- |
| Stage 1 entitlement/retention/publication | Accepted |
| Track A PR 2 validator + public-safe status | On `main` |
| Campaign dataset acceptance class | `DIAGNOSTIC_READY` under `DIAGNOSTIC_ONLY` |
| Formal interpretation / promotion acceptance | Not granted |
| Track A PR 3 bounded runner code | On `main` via #187 |
| Detached pre-run binding | Not complete |
| Track A PR 4 fourteen-trial evidence | Not started |
| D8 materialization, A2, result access | Closed |

## Immediate Blockers Or Owner Decisions

- Detached pre-run binding must freeze exact code, configuration, environment,
  protocol, trial inventory, and accepted-dataset identities outside the repo
  before any result-bearing run.
- Terminal-event policy remains explicitly deferred; contract default still
  blocks unresolved return-relevant terminals and counts them.
- D8 materialization, A2 exchange retrieval, identity reopen, purchases, and
  performance/result access remain closed.
- Another machine can resume **public** work from this clone. Continuing
  **private** cards still requires a private-channel copy of the local
  `private_data` control tree; GitHub alone is not sufficient.

## Next Safe Action

- Start Stage 4 detached pre-run binding under the frozen PR 3 plan and the
  `DIAGNOSTIC_ONLY` ceiling, or continue only documentation hygiene that does
  not claim run results.
- Do not run the 14 trials, access performance, or enter D8 until binding is
  complete and any required owner gates are recorded.

## Source Routing

- Authority and research-safety invariants: `AGENTS.md`.
- Workflow, review, waiting, and stop behavior:
  `docs/codex_long_running_controller.md`.
- Program stages, dependencies, gate criteria, and completion evidence:
  `docs/current_roadmap.md`.
- Long-term evidence policy: `docs/research_program_charter.md`.
- Track A protocol and gate semantics:
  `docs/eodhd_sp500_diagnostic_campaign_contract.md` and its preregistrations.
- Public-safe PR 2 / Stage 1 records:
  `docs/track_a_pr2_public_status.md`,
  `docs/stage1_accepted_public_record_v1.json`.
- Historical decisions, validation, and failures: `docs/decision_log.md`,
  `docs/engineering_log.md`, and `docs/troubleshooting_log.md`.
