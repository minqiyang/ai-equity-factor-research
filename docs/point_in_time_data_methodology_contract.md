# Point-in-Time Data Methodology Contract

Status: proposed Stage 3 methodology contract; acceptance pending protected
merge.

Contract ID: `point_in_time_data_methodology_contract_v1`.

Contract version: `1.0.0`.

This document is the normative Stage 3 data-methodology contract under
`docs/research_program_charter.md` and `docs/current_roadmap.md`. It defines the
provider-agnostic evidence required before a historical dataset may be treated
as point-in-time, tradable, survivorship-aware research input.

Contract acceptance is software-process evidence only. It does not select a
provider, inspect or verify a dataset, grant a license, establish historical
validity, authorize real-data interpretation, or satisfy later trial,
statistical, cost, portfolio, or reproduction gates.

## Scope and Non-Authorization

This stage defines:

- dataset identity, provenance, entitlement, version, and transformation
  lineage;
- bitemporal availability and revision semantics;
- permanent security/listing identity, identifier history, listing lifecycle,
  and historical universe membership;
- corporate actions, distributions, delistings, and terminal-value policy;
- raw/adjusted price, return, volume, fundamental, classification, benchmark,
  and risk-free field semantics;
- missing, stale, halted, suspended, invalid, and non-observation states;
- exchange calendar, session, timestamp, timezone, currency, and unit policy;
- private full manifests and tracked redacted projections; and
- sample classification plus the future holdout-exposure ledger schema.

No provider selection, download, credentials, or remote data access is
authorized. This stage does not read private files or performance values, add
provider adapters, change loaders, run factors or backtests, add a database or
dependency, implement the Stage 4 immutable all-trial ledger, or authorize
LEAN, paper, brokerage, order, or live behavior.

## Three Separate Gates

The program has three non-interchangeable gates:

1. `methodology_contract_accepted`: this provider-agnostic contract has passed
   documentation, review, and protected-merge gates.
2. `dataset_manifest_reviewed`: a specific immutable dataset version has a
   complete private manifest, safe public projection, evidence references, and
   an immutable accepted dataset-review decision for one declared use, bound to
   the exact manifest and projection versions.
3. `formal_interpretation_eligible`: every applicable data, sample, timing,
   trial, statistical, cost, privacy, and evidence-layer gate has passed for a
   frozen experiment.

In plain terms, methodology_contract_accepted does not imply
dataset_manifest_reviewed, and dataset_manifest_reviewed does not imply
formal_interpretation_eligible.

Contract acceptance does not verify any dataset and does not establish
`formal_ready`, point-in-time status, license entitlement, or historical
validity. A dataset-specific review can still be `blocked`,
`diagnostic_ready`, or `diagnostic_ready_with_low_caveats`; `formal_ready`
remains unavailable until every later applicable program gate is implemented
and satisfied.

After protected merge, the accepted contract identity is the tuple
`(contract_id, contract_version, contract_content_sha256,
contract_protected_merge_sha)`. `contract_content_sha256` is the SHA-256 of the
exact UTF-8 bytes of this file at that protected-main commit; the hash is stored
outside this self-referential file. A dataset-review decision must bind all four
values and becomes stale after any contract-content or version change.

## Evidence States and Missing Declarations

Every required section in a dataset-specific review has one state:

- `accepted`: evidence was reviewed and satisfies the declared use;
- `diagnostic_only`: enough is known for a narrowly described diagnostic but
  not formal interpretation; or
- `blocked`: required evidence is missing, unknown, incompatible, disputed, or
  not independently reviewable.

`UNKNOWN` is an explicit blocking value, never an acceptable caveat for formal
use. An empty value never means `NOT_APPLICABLE`. `NOT_APPLICABLE` is permitted
only with a typed reason, evidence reference, reviewer, review timestamp, and
an explanation of why the field cannot affect the declared calculation.

Static or survivor-selected cohorts remain `DIAGNOSTIC_ONLY` even when their
survivorship caveat is documented. This includes a static current list:
unverified historical membership blocks formal interpretation. A completed
checklist, loader success, matching dates, an actual hash, or a provider name
alone cannot change that classification.

## Dataset Identity and Manifest

Each immutable dataset version requires one `private_full_manifest`. Its
identity is a tuple, not a filename or free-text label.

### Top-level fields

| Field | Requirement |
| --- | --- |
| `schema_version` | Version of this manifest schema. |
| `manifest_id` | Immutable logical identifier; a correction creates a new ID. |
| `created_at_utc` | Time the manifest version was created. |
| `dataset_role` | Asset prices, benchmark, security master, membership, corporate actions, fundamentals, classifications, risk-free, or another reviewed role. |
| `provider_label` | Provider/source label without credentials or account metadata. |
| `provider_product_release` | Product, release, snapshot, or as-of identifier. |
| `retrieved_at_utc` | Actual retrieval or receipt time. |
| `as_of_cutoff` | Latest information the extraction was allowed to contain. |
| `extraction_identity` | Query/config identity, coverage, filters, and requested fields; sensitive details remain private. |
| `privacy_classification` | `public`, `private`, or `restricted`. |
| `code_sha` | Code used for a derived or normalized version. |
| `config_sha256` | Canonical hash of transformation configuration. |
| `environment_id` | Immutable interpreter, platform, library, calendar, locale, and timezone environment reference used for transformation or validation. |
| `environment_lock_sha256` | Hash of the reviewed lock, container, or equivalent complete environment manifest. |
| `canonicalization_id` | Versioned canonical-serialization and identity-projection specification. |
| `ordered_manifest_sha256` | Hash of the ordered component inventory. |
| `canonical_manifest_sha256` | Hash of canonical manifest serialization excluding this field itself. |

### Per-input fields

Every input records:

- stable `input_id` and role;
- schema name and version;
- actual `raw_byte_sha256`, byte size, row count, exact inclusive data range,
  and approved hash-publication classification;
- raw, vendor-cleaned, hand-cleaned, normalized, or derived status;
- parent input IDs and hashes, transformation ID, code SHA, and config hash;
- transformation `environment_id` and environment-lock digest;
- identifier namespace, currency, units, calendar, timezone, and timestamp
  semantics;
- adjustment, revision, missingness, and publication policies; and
- manual transformations plus quality exceptions with reviewer disposition.

“Hash later,” a `hash_plan`, a mutable timestamp, or a malformed/placeholder
digest is insufficient for `dataset_manifest_reviewed`. A byte hash identifies
bytes; it does not prove semantic equivalence, query coverage, license,
adjustment policy, revision history, or point-in-time correctness. The same
bytes under different extraction or transformation lineage remain distinct
evidence versions.

Derived lineage must be complete and acyclic. A correction or vendor revision
creates a new manifest ID and retains the prior version; it must never silently
overwrite the evidence used by an earlier run.

### Canonical serialization and environment identity

The manifest freezes `canonicalization_id` as `pit_canonical_json_v1`. It first
constructs a typed identity projection:

- a duplicate object property is rejected during parsing, before any mapping
  can discard it;
- invalid Unicode, including lone surrogates, is rejected; schema-declared
  textual values are normalized to Unicode NFC before the JCS input is
  constructed, and are preserved byte-for-byte thereafter;
- timestamps become UTC RFC 3339
  `YYYY-MM-DDTHH:MM:SS[.fraction]Z`; zero fractional seconds are omitted and
  nonzero fractions remove trailing zeroes;
- JSON integers are permitted only in the exact I-JSON interoperable range
  `[-(2^53)+1, (2^53)-1]`; larger integers and every exact non-integral
  quantity become schema-typed decimal strings matching
  `-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?`, with no plus sign, exponent, leading
  zero, trailing fractional zero, or negative zero;
- booleans remain JSON `true`/`false`, missing values are JSON `null`, and raw
  floating-point values, NaN, and infinity are prohibited;
- the identity projection includes schema/canonicalization versions and
  excludes only `canonical_manifest_sha256`, signatures, and explicitly
  non-identity presentation notes;
- set-like arrays are sorted by their declared stable IDs before
  canonicalization; semantically ordered arrays retain their schema-required
  stable ordinal; and
- the component inventory is sorted by `(input_id, component_ordinal)` before
  `ordered_manifest_sha256` is calculated.

The resulting I-JSON value is serialized exactly under
[RFC 8785 JCS](https://www.rfc-editor.org/rfc/rfc8785): no inter-token
whitespace, RFC-defined lowercase literal and string escaping, recursive
property sorting by raw UTF-16 code units independent of locale, unchanged
array order, and UTF-8 output without a byte-order mark. Any input outside that
profile fails instead of being coerced. These rules, including the referenced
RFC version, are part of `pit_canonical_json_v1`; a change requires a new
canonicalization ID.

`canonical_manifest_sha256` is SHA-256 over the UTF-8 bytes of that canonical
identity projection. Reordering object keys or non-semantic input inventory
rows must not change it; changing an identity-bearing semantic field must
change it.

`tests/fixtures/pit_canonical_json_v1_golden.json` freezes a tiny synthetic
semantic input, exact canonical UTF-8 text, and SHA-256. Its test proves compact
literal encoding, property order, byte identity, and digest consistency without
representing a private dataset or implementing a production manifest service.

Every validation or derived-data step records `environment_id`,
`environment_lock_sha256`, interpreter/platform, locale, process timezone, and
the versions of every parsing, calendar, and transformation library. An
unlocked or incomplete environment blocks independent reproduction. Raw-byte
identity remains valid without transforming the source, but the manifest
creation and verification environment is still recorded.

## License, Entitlement, and Permitted Use

Automated checks cannot determine legal entitlement. The private manifest
records a reviewable evidence status:

- `asserted`: a person or source says access is permitted, but no owner review
  is recorded;
- `owner_accepted`: the owner or authorized reviewer accepted the evidence for
  the declared use;
- `unknown`: evidence is absent or scope is unclear; or
- `blocked`: evidence indicates the use is not permitted.

Only `owner_accepted` can satisfy this data-methodology section, and it must
record the reviewer, review date, private evidence reference, effective and
expiry dates, territory if applicable, retention requirements, and separate
permissions for internal research, derived-output publication, redistribution,
and independent reproduction.

License documents, account IDs, contract numbers, entitlement tokens, access
keys, and credentials remain outside the repository. `asserted`, `unknown`, or
`blocked` status prohibits formal interpretation. This is an evidence gate,
not a legal opinion.

## Immutable Dataset-Review Decision

Neither a manifest author nor a checklist can self-certify
`dataset_manifest_reviewed`. An authorized reviewer who did not create or
modify the reviewed manifest/projection issues a new immutable decision record
containing:

- `review_decision_id`, schema version, `reviewed_at`, reviewer ID, and
  reviewer-authority reference;
- exact `contract_id`, `contract_version`, `contract_content_sha256`, and
  `contract_protected_merge_sha`;
- exact `manifest_id`, private `canonical_manifest_sha256`, and
  `canonicalization_id`;
- exact public-projection ID, schema version, and
  `public_projection_sha256`;
- declared dataset roles, use, date/universe scope, privacy/publication scope,
  and applicable contract version;
- decision: `accepted`, `diagnostic_only`, or `blocked`;
- every finding ID, severity, evidence reference, disposition, and unresolved
  limitation;
- predecessor or superseded decision ID without modifying the earlier record;
  and
- `decision_canonicalization_id` = `pit_canonical_json_v1`,
  `decision_record_sha256`, and safe public decision reference.

The decision identity projection includes every field above plus all finding
and disposition records, excludes only `decision_record_sha256`, signatures,
and explicitly non-identity presentation notes, and sorts findings by stable
finding ID and set-like evidence references by their stable IDs. It otherwise
uses the `pit_canonical_json_v1` encoding, timestamp, numeric, null, key, and
array rules. `decision_record_sha256` is SHA-256 over the resulting canonical
UTF-8 bytes.

The tracked projection carries only the safe decision ID, status, scope,
reviewer-authority reference, reviewed time, public-projection identity, and
redacted evidence references. A private manifest digest appears publicly only
when its publication is separately approved.

The decision is invalid when it is missing, self-issued by the
manifest/projection producer, bound to a different manifest, projection, or
contract identity, backdated, non-canonical, hash-mismatched, mutable, outside
reviewer authority, missing finding dispositions, or superseded. A form may
reference an accepted decision; it cannot grant the gate. Any contract,
manifest, projection, scope, or identity-bearing correction requires a new
review decision.

## Bitemporal Availability and Revision Contract

Every time-varying record distinguishes when it describes the world from when
the information was knowable. Required fields include:

- `effective_from` and `effective_to`;
- `known_at`;
- `source_published_at` and `public_available_at`;
- `provider_available_at` when provider delivery lag matters;
- `retrieved_at_utc`;
- `revision_id`, `revision_published_at`, and `supersedes`; and
- source timezone, calendar, cutoff rule, and evidence reference.

`known_at` is the frozen conservative earliest timestamp at which the record is
eligible for the declared research actor. It must be no earlier than every
applicable public, provider-delivery, revision, and parent availability time
and must never be backdated from later evidence.

For a decision at time `t`, a value is usable only when:

```text
effective_from <= t < effective_to
and known_at <= t
and public_available_at <= t
and provider_available_at <= t when provider delivery lag applies
and revision_published_at <= t for the selected vintage
and every parent of a derived value satisfies the same rule
and the observation status, calendar, and field role are accepted
```

Economic or fiscal period end is not an availability timestamp. A date-only
release defaults conservatively to the next eligible exchange session after
the source-local date unless a reviewed timestamp rule proves earlier
availability. Latest-only history and retrospectively reconstructed effective
dates without knowability evidence are diagnostic-only.

## Security Master, Listing, and Historical Membership

Ticker text is an alias, not a permanent join key.

### Security and listing identity

The instrument master records:

- `permanent_security_id`;
- `listing_id`;
- provider identifiers, security type, share class, domicile, currency, and
  exchange/MIC;
- each `ticker_alias` with effective interval, source, and change reason;
- listing start, first-trade date, last-trade date, listing end, trading
  status, and termination reason; and
- predecessor/successor mappings without silently stitching returns.

Alias, listing, and membership intervals must not overlap inconsistently.
Ticker reuse, relisting, share-class changes, venue moves, and mergers must not
join distinct permanent securities.

### Historical universe membership

Each base membership row records:

- universe ID, version, purpose, and rule;
- permanent security and listing IDs;
- membership `effective_from` and `effective_to`;
- decision/announcement `known_at` and source evidence;
- inclusion or exclusion reason; and
- revision/supersession identity.

Membership must be both effective and knowable before the signal decision. It
must fall inside a valid listing episode. A future membership record, later
alias, or retrospective constituent history must not change an earlier
universe mask.

Derived eligibility is separate from base membership. Formal eligibility is:

```text
listed_and_tradable
and point_in_time_member
and known_liquidity_eligible
and data_valid
```

Each component has independent provenance and availability. A symbol's
presence in a price file is not membership evidence.

## Corporate Actions, Delistings, and Terminal Value

The event ledger uses a stable event ID, permanent security/listing IDs,
provider/revision identity, source evidence, and explicit event type. It
supports, when applicable:

- split and reverse-split ratios;
- ordinary and special cash dividends with currency;
- stock dividends, rights, and spin-offs;
- merger/acquisition cash, stock, and mixed consideration;
- exchange, ticker, or identifier change;
- listing transfer, suspension, bankruptcy, and delisting; and
- final-trade, ex, record, effective, payment, announcement, and `known_at`
  timestamps.

Every declared return convention freezes:

- split-factor direction;
- dividend inclusion, withholding, and reinvestment treatment;
- total-return construction;
- merger consideration and successor handling;
- spin-off allocation;
- double-count prevention between adjusted prices and separate distributions;
  and
- `delisting_terminal_value_policy`, including missing terminal evidence.

Unresolved terms block affected formal windows. A delisted holding cannot
disappear, default to a zero return, or be replaced by a successor without a
registered policy and evidence.

## Field Dictionary and Adjustment Semantics

Every consumed field has a field-dictionary row containing:

- canonical field ID, source column, data type, units, currency, and precision;
- observation meaning and allowed roles: feature, label, execution, liquidity,
  benchmark, risk-free, or metadata;
- semantic class: raw, split-adjusted, dividend-adjusted,
  total-return-adjusted, vendor-adjusted, or `UNKNOWN`;
- `adjustment_set_id`, adjustment-factor source/version/direction, dividend
  treatment, and revision behavior;
- `volume_basis`: raw shares, split-adjusted shares, vendor-adjusted, or
  `UNKNOWN`;
- effective, publication, provider-availability, revision, and ingestion
  timestamp semantics;
- compatible parent/companion fields; and
- formal-use eligibility plus limitation reason.

OHLC fields used together require one compatible adjustment set. An adjusted
return series is not an execution price. A price-volume product requires a
reviewed compatible price field and `volume_basis`; a column named
`adjusted_close` does not establish that compatibility. Asset and benchmark
return conventions must be economically comparable.

## Fundamentals and Classifications

A formal fundamental value records fiscal period, units, currency, filing or
publication ID, `public_available_at`, provider availability, revision ID,
`revision_published_at`, and `supersedes`. As-of reconstruction returns only a
vintage available by the decision timestamp; a later restatement never
back-propagates.

A classification records scheme, scheme version, code, permanent security ID,
effective interval, publication/knowability interval, revision, and source.
Sector or industry analysis remains blocked when only a latest classification
is available.

## Missing, Stale, Suspension, and Observation Status

Numeric missingness does not identify economic state. Every absent or unusable
observation uses an evidence-backed reason code such as:

- `OBSERVED`;
- `NOT_SCHEDULED`;
- `NOT_YET_LISTED`;
- `NOT_MEMBER`;
- `HALTED`;
- `SUSPENDED`;
- `NO_TRADE`;
- `STALE`;
- `DELISTED`;
- `CORPORATE_ACTION_PENDING`;
- `PROVIDER_GAP`; or
- `INVALID`.

The methodology defines the allowed states for each field role, staleness
threshold in expected exchange sessions, last-valid-observation behavior,
quality issue, and exclusion reason. It never infers a halt, suspension, or
stale observation solely from zero volume or unchanged price.

Forward-fill, backward-fill, zero-fill, interpolation, implicit symbol
substitution, and corporate-action inference are prohibited by default. A
reviewed exception must be typed, versioned, reproducible, recorded as a
transformation, and excluded from formal use when it could alter availability
or tradability.

## Calendar, Session, Timezone, Currency, and Units

Date alignment alone is not a calendar contract. Each listing/data role records:

- `calendar_id`, `calendar_version`, and a version/hash evidence reference;
- exchange/MIC, `source_timezone`, and UTC conversion rule;
- `session_date`, session-label convention, expected open/close, early-close
  behavior, holidays, DST, and expected-session set;
- observation timestamp and `available_at`;
- currency, unit, lot/share convention, and any FX policy; and
- multi-exchange and benchmark alignment policy.

Naive dates may be retained as validated source labels, but they cannot by
themselves prove knowledge time or session validity. Missing/extra sessions,
half days, DST changes, cross-market holidays, and calendar version changes
must be reviewed without implicit intersection or filling.

## Benchmark and Risk-Free Policy

The benchmark contract records:

- `benchmark_purpose`, permanent identity, universe match, and selection
  rationale;
- investability, constituent or rule methodology when relevant, and
  point-in-time composition requirements;
- price versus total-return basis, corporate-action/distribution treatment,
  currency/FX, calendar/timezone, coverage, rebalance, and missing-date policy;
  and
- whether the comparison is cost-free and why that is appropriate.

No silent benchmark substitution, intersection, forward-fill, or zero-fill is
allowed for formal evidence.

The `risk_free_policy` records a series or reviewed `NOT_APPLICABLE` decision.
A series requires source, currency, tenor, quote type, units, day count,
compounding, release/availability lag, revision policy, interval conversion,
calendar, and missing policy. The current zero-risk-free Sharpe-style metric
remains an unadjusted diagnostic convention; it is not formal risk-free
evidence.

## Private Manifest and Public Projection

The complete `private_full_manifest`, locator map, entitlement evidence,
restricted query/config details, actual paths, approved hashes, and sensitive
quality artifacts stay outside the repository.

Tracked records use a schema-versioned `public_redacted_projection` built by
allowlist. It may contain logical IDs, declared roles, non-sensitive policy
states, the safe dataset-review decision reference, redacted evidence
references, and only hashes whose publication is explicitly permitted.

Tracked records must not contain private absolute paths, usernames/home
directories, account or contract IDs, license documents, credentials, tokens,
signed URLs, restricted query parameters, raw private rows, symbol-level
restricted data, or private performance values. A content hash is not
automatically public merely because it is non-reversible.

Validation errors and public logs identify an `input_id`, field, and safe row
locator without echoing a private path or raw value. Existing user-specific
EODHD defaults and historical checkpoints remain legacy diagnostic artifacts;
they do not satisfy this public projection or any formal dataset review.

## Sample Registry and Holdout Exposure Ledger

Each protected sample is registered before access with:

- immutable sample ID and dataset manifest ID;
- exact inclusive window and applicable asset/universe scope;
- purpose and initial classification;
- `sealed_at`, sealing actor, evidence reference, and permitted access policy;
  and
- overlap relation to every existing sample.

The future exposure ledger records:

- schema version and immutable exposure ID;
- actor, actor type, tool/process, authorization reference, and purpose;
- dataset manifest/input IDs and exact window;
- `classification_before`;
- `accessed_at` and distinct `recorded_at`;
- `backfilled`;
- artifact class and field/metric names accessed, without metric values;
- code SHA and artifact evidence references;
- `design_impact`: none, possible, confirmed, or unknown;
- `classification_after` and downgrade reason; and
- correction/supersession link without modifying the original record.

Stage 4 owns append-only enforcement, pre-access intent allocation, completion
records, record chaining, and completeness tests. Stage 3 defines the schema
and downgrade semantics only.

Access to raw or adjusted asset prices, benchmark or total-return levels,
distributions/corporate-action terms, risk-free inputs, returns, labels,
holdings, trades, equity/cost paths, diagnostic values, directions,
magnitudes, ranks, plots, per-fold results, reports, or any other input from
which protected outcomes can be directly or indirectly reconstructed removes
pristine holdout status. Metadata-only intake can preserve a sealed
classification only when its allowlisted fields cannot reveal or reconstruct
outcomes and its access is recorded prospectively.

Unlogged access, a `backfilled` record, unknown access time/actor, or uncertain
`design_impact` cannot prove a holdout; the affected and overlapping interval
becomes `pseudo_holdout` or `historical_evaluation`. If it influenced design or
tuning, it becomes `development`; selection within a preregistered trial budget
may be `validation`.

Classification moves only toward greater exposure. An existing window is never
upgraded. A new holdout requires a distinct, prospectively sealed and
information-independent sample. After one frozen evaluation, that window is
`historical_evaluation` for every later campaign.

Repository evidence confirms that private diagnostics and subsequent reviews
accessed results spanning 2025-05-01 through 2026-05-31. That interval is
`historical_evaluation`, not a pristine holdout. No performance value needs to
be disclosed to record this access fact.

## Formal Blocking Decision Table

| Condition | Stage 3 decision |
| --- | --- |
| License is `asserted`, `unknown`, expired, incompatible, or lacks owner review | `blocked` |
| Actual content hash, retrieval time, extraction identity, version, or lineage is absent | `blocked` |
| Dataset-review decision is absent, self-issued, stale, version-mismatched, or outside reviewer authority | no `dataset_manifest_reviewed` |
| Ticker is the only identity, or membership availability is retrospective/unknown | `diagnostic_only` or `blocked` |
| Listing, delisting, terminal value, or material corporate-action terms are unresolved | `blocked` for affected windows |
| Field adjustment, dividend, volume, currency, unit, or revision semantics are unknown/incompatible | `blocked` |
| Filing/classification knowledge time or vintage cannot be reconstructed | `diagnostic_only` |
| Missing/stale/suspension state is unexplained or silently filled | `blocked` |
| Calendar/session/timezone or benchmark compatibility is unresolved | `blocked` |
| Public artifact may reveal restricted metadata, paths, raw values, or performance | `blocked` |
| Protected access is missing, backfilled, uncertain, or overlaps exposed information | downgrade; no holdout claim |
| Stage 4 trial/access completeness or Stage 5 statistical controls are absent | no `formal_interpretation_eligible` |

## Deterministic Stage 3 Test Matrix

| Case | Input or counterexample | Required decision |
| --- | --- | --- |
| `PIT-001` | License is merely asserted or unknown. | Formal use is blocked; automated checks do not claim legal verification. |
| `PIT-002` | A mutable file has only a timestamp, hash plan, placeholder, or malformed digest. | It is not an immutable dataset version. |
| `PIT-003` | Manifest/decision object keys or non-semantic rows are reordered, or identical bytes arrive through different extraction, transformation, or environment lineage. | `pit_canonical_json_v1` reordering preserves the applicable hash; changed identity-bearing lineage/environment/decision fields create a distinct version and hash. |
| `PIT-004` | Membership or another time-varying record is historically effective or publicly released but its conservative `known_at` is after the signal date. | It is unavailable to that signal. |
| `PIT-005` | One ticker is reused by two permanent securities or crosses listing episodes. | No identity join or return stitching occurs. |
| `PIT-006` | A held security delists or merges without accepted terminal evidence. | The affected window blocks; the position never silently disappears or becomes zero return. |
| `PIT-007` | A total-return-adjusted series is combined with a separate cash dividend, or price/volume adjustment sets conflict. | Double counting or incompatible dollar volume is rejected. |
| `PIT-008` | A later fundamental restatement or classification revision is queried before its availability timestamp. | The later vintage is unavailable and never back-propagates. |
| `PIT-009` | Holiday, provider gap, zero volume, halt, suspension, stale print, and delisting share a numeric missing representation. | Typed status remains distinct; no silent fill or inference occurs. |
| `PIT-010` | Benchmark basis, currency, calendar, coverage, or risk-free conversion is incomplete or incompatible. | Formal benchmark/risk-adjusted interpretation blocks without substitution. |
| `PIT-011` | A public projection contains a private path, account/license evidence, restricted hash, raw value, or private metric. | Serialization fails closed through the allowlist. |
| `PIT-012` | Outcome-reconstructible price/benchmark/corporate-action data is viewed, or protected-sample access is recorded after the fact or has unknown actor/time/impact. | It cannot retain or establish holdout status and is downgraded. |
| `PIT-013` | An exposed interval overlaps a nominally sealed window. | Atomic intervals are split; uncertain overlap downgrades the nominal window. |
| `PIT-014` | This contract is accepted but no exact manifest/projection/contract-bound, non-self-issued dataset-review decision or later program gates have passed. | The methodology contract exists, while a missing/stale/contract-mismatched decision leaves dataset verification and formal interpretation blocked. |

## Accepted Decisions and Deferred Implementation

Stage 3 accepts the provider-agnostic contract only after its protected PR,
required CI, and current-head review gates pass. It creates no data claim,
research trial, holdout access, factor result, or performance evidence.

Deferred work includes:

- dataset-specific private manifests and safe public projections;
- deterministic manifest/field/calendar/security-master validators;
- provider-specific extensions after a separate selection and authorization;
- Stage 4 immutable experiment, trial, and exposure-ledger implementation;
- Stage 5 statistical validation;
- later data-provider, benchmark, cost, capacity, factor, strategy, portfolio,
  reproduction, and LEAN gates.

Until those gates exist and a declared dataset version passes them, the static
EODHD workflow, current local CSV inventory, loader validation, fixed-cohort
diagnostics, and synthetic fixtures remain diagnostic evidence only.
