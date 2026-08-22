# Identity Evidence Public Status

Updated: 2026-08-22

This note is a public aggregate. It is not a profitability claim and does not
accept a dataset.

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
- Coverage constraints: 450, each still 100 short of the threshold 100
- First blocking claim for every identity: C01
- Constructed filed-text records: 6,024
- Records covering the requested interval: 0
- Materialization: not entered

The first detector lineage failed review because it invented a private
annotation grammar. The replacement lineage reads real EDGAR profiles and still
fail-closes: most iXBRL contexts are same-day durations and cannot cover the
multi-year window. That is an evidence-class gap under the current policy, not
a license to infer identity from ticker continuity.

## What this does not do

- It does not start Track A PR 2.
- It does not publish raw filings, ticker lists, or performance values.
- It does not authorize exchange (A2) retrieval or result access.
