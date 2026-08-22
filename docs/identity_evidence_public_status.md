# Identity Evidence Public Status

Updated: 2026-08-22

This note is a public aggregate of the completed identity-evidence evaluation.

## What was evaluated

Private Phase B retrieval collected public SEC index pages, then 1,194 primary
filed-document bodies discovered from those pages. An EDGAR-referential
readjudication then applied the frozen identity-acceptance policy to 189
identities over the requested interval `[2014-01-31, 2026-07-01)`.

Machine-readable counts and hashes:
[identity_evidence_public_aggregate_v1.json](identity_evidence_public_aggregate_v1.json).

## Result

- Identities adjudicated: 189
- Accepted identities: 0
- Coverage constraints evaluated: 450 at threshold 100
- First blocking claim for every identity: C01
- Constructed filed-text records: 6,024
- Interval-covering records in this corpus: 0

The first detector lineage failed review because it invented a private
annotation grammar. The replacement lineage reads real EDGAR profiles and
fail-closes: most iXBRL contexts are same-day durations, so the requested
multi-year window stays uncovered under the current policy.
