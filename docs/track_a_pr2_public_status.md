# Track A PR 2 Public Status

Updated: 2026-08-24

Public-safe progress for Track A PR 2 and the diagnostic-track acceptance
that unblocked PR 3. Machine-readable hashes and counts:
[track_a_pr2_public_status_v1.json](track_a_pr2_public_status_v1.json).
Allowlisted projection:
[track_a_pr2_public_projection_v1.json](track_a_pr2_public_projection_v1.json).
Safe decision fields:
[dataset_review_public_projection_v1.json](dataset_review_public_projection_v1.json).

## Completed

- Validator `pit_manifest_validator_v1` is on `main` with synthetic fixtures
  (PR #186).
- A private full manifest and freeze record exist locally. This repository
  binds them by hash only.
- Blinded dataset-review decision: `diagnostic_only`. CRITICAL review gate
  passed.
- Materiality proposal approved by exact SHA
  `d52b1441f6f66f650da082f01d2f2060c304cb12c3eefcc83ce540291d81e6e5`.
- Campaign dataset acceptance under the diagnostic ceiling:
  `DIAGNOSTIC_READY`. Bound acceptance-record identity SHA
  `1f0c92f0fc8001f08e95d2004c571751a5ceb3696f077cbb5df10895c78e0039`.
  Evidence ceiling remains `DIAGNOSTIC_ONLY`.
- Terminal-event policy: owner explicit defer. Contract default remains:
  unresolved return-relevant terminals block affected rows and are counted.
- Identity: 189 adjudicated, 0 accepted, D7 terminal fail-closed.
- Track A PR 3 bounded runner code later landed on `main` through PR #187.
  That does not complete detached binding or the 14-trial run.

## Not in this repository

Raw vendor rows, ticker lists, private filesystem paths, provider responses,
the full private manifest, the freeze-record body, the evidence pack, the full
decision record, and the full acceptance-record body stay off GitHub.

## Closed owner gates (diagnostic track)

1. Materiality thresholds: exact-SHA approved.
2. `diagnostic_only` plus `DIAGNOSTIC_READY` acceptance: accepted for the
   diagnostic track under `DIAGNOSTIC_ONLY`.
3. Public-safe PR 2 publication set: on `main`.

## Still closed

- Formal interpretation / promotion acceptance
- D8 materialization
- Result or performance access
- Fourteen-trial run (needs detached pre-run binding first)
- A2 exchange retrieval
- Identity reopen
- Raw private upload

## Next

Detached pre-run binding, then Track A PR 4 evidence only after binding
verifies. Another machine can read this public status from GitHub; private
control-tree bodies still require a private-channel transfer.
