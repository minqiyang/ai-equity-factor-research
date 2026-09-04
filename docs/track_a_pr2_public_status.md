# Track A PR 2 Public Status

Updated: 2026-09-04

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
- Stage 4 G-2 binding is accepted by hash. Acceptance-file SHA
  `84f1ce471af19b4473a2a3bfa9ffb65b08927cc0218c55bd6922a7ddc5c30de0`.
  Frozen plan markdown SHA
  `d847c6305469b050f3d2e0426ff589cf422a2fa1f54044b9dcf037963567f992`.
  EXEC-2 fileset SHA
  `29aeec97ebc8146fccac1f575c1c098cbc9db2b106831a1b53d12e7ad2995c92`.
  Protected main at G-2 acceptance
  `11a9cb8849b5239faa1081eda046d2254a12febc`. Stage 4 is not fully complete.
- The 14-trial run is REFUSED. Named reason:
  `ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`. Owner-stop SHA
  `163b8f31d3568e460c074592c00376cf86d4f09371a6bb6a40f8d6cdd4548f5a`.
  Freeze-record SHA
  `c160a3b21f359dc96eda7f1f018e3315bae79f505078ca5199ed87a8204f0ccd`.
  Protected main after PR #194:
  `24bc794d0a6cbd6502a8db088008fa74acbe8752`. Evidence ceiling remains
  `DIAGNOSTIC_ONLY`. No performance values are published. The 14-trial run
  did not execute.

## Not in this repository

Raw vendor rows, ticker lists, private filesystem paths, provider responses,
the full private manifest, the freeze-record body, the evidence pack, the full
decision record, the full acceptance-record body, the G-2 acceptance-file body,
the frozen plan markdown body, the EXEC-2 fileset body, and the owner-stop
body stay off GitHub.

## Closed owner gates (diagnostic track)

1. Materiality thresholds: exact-SHA approved.
2. `diagnostic_only` plus `DIAGNOSTIC_READY` acceptance: accepted for the
   diagnostic track under `DIAGNOSTIC_ONLY`.
3. Public-safe PR 2 publication set: on `main`.
4. Stage 4 G-2 binding: accepted by hash under `DIAGNOSTIC_ONLY`.

## Still closed

- Formal interpretation / promotion acceptance
- D8 materialization
- Result or performance access
- Remaining Stage 4 detached pre-run binding after G-2
- Fourteen-trial run (`REFUSED`,
  `ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`)
- A2 exchange retrieval
- Identity reopen
- Raw private upload

## Next

Owner-stop remains in force. D8, A2, and identity reopen stay closed. Do not
run the 14 trials. Another machine can read this public status from GitHub;
private control-tree bodies still require a private-channel transfer. No
performance values are published.
