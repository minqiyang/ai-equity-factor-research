# Experiment and Trial Ledger Schema Registry R0 Contract

Contract ID: `experiment_trial_ledger_schema_registry_r0`.

Contract version: `0.1.0`.

This document defines the first fail-closed Stage 4B registry foundation under
the accepted `docs/experiment_trial_ledger_contract.md`. Its publication state
is determined by protected-main history and `docs/current_handoff.md`, not by a
claim inside this document.

R0 is deliberately incomplete. It freezes the registry meta-contract, the
closed 37-event vocabulary, deterministic registry identity, duplicate-safe
parsing, and the one event schema already exact in Stage 4A. It does not accept
a complete payload-schema registry and does not implement a ledger runtime.

## Evidence State and Non-Authorization

The packaged registry must remain
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` while any vocabulary event lacks an exact
schema. In R0:

- `LEDGER_EPOCH_CREATED` is the sole `FROZEN_SUPPORTED` event;
- the remaining 36 known events are listed as incomplete and rejected before
  append or action;
- an event outside the closed vocabulary is rejected as
  `UNKNOWN_EVENT_TYPE`; and
- registry or event ambiguity fails closed rather than being coerced,
  defaulted, stripped, or projected away.

R0 does not establish:

- 37-of-37 payload-schema acceptance;
- append-only storage, transactions, locking, restart, or recovery;
- entity allocation, lifecycle, campaign accounting, or trial completeness;
- protected-access capability enforcement;
- checkpoint latestness, anti-rollback, actor authority, or signatures;
- review, promotion, or formal historical interpretation; or
- LEAN, paper, brokerage, order, live, or real-money behavior.

No research trial, execution attempt, sample access, performance value, factor,
strategy, portfolio rule, or private path is created by this contract.
Trial count, execution-attempt count, and protected-sample access remain zero.

## Authoritative Artifacts

The R0 authority is:

- `src/ledger/schemas/experiment_trial_ledger_payload_schema_registry_v1.json`;
- its external lowercase SHA-256 sidecar;
- `src/ledger/schema_registry.py`; and
- `tests/test_ledger_schema_registry.py`.

The JSON artifact, not Python constants, is the registry authority. The Python
module implements the closed R0 meta-contract and validator. The independent
test tuple remains a separate oracle for the 37-event vocabulary.

The registry is packaged with the `ledger` namespace. Loading it through
`importlib.resources` must produce the same validated object in a source tree,
sdist, or wheel.

## Registry Identity

The exact registry digest preimage is the all-and-only parsed JSON registry
object under `pit_canonical_json_v1`, subject to this R0 restriction:

- every string and property name is ASCII;
- integers are I-JSON safe and Boolean values are never integers;
- floating-point and non-finite numbers are forbidden;
- object properties are sorted for canonical serialization;
- arrays remain semantically ordered; and
- no external, file, URL, network, or mutable path reference participates.

The lowercase SHA-256 is stored outside the preimage in the `.sha256` sidecar.
Only that sidecar is excluded. Every vocabulary item, type definition, event
schema, local constraint, incomplete-event declaration, and conformance vector
is inside the digest preimage. Source object-key reordering preserves the
digest; any semantic leaf mutation changes it.

Executable event validation and conformance-vector execution are bound to the
packaged sidecar digest. A caller-supplied object may be checked for generic R0
meta-contract consistency, but it cannot become validation authority merely by
being self-consistent or by promoting another event locally. Loading arbitrary
registry bytes requires an explicit expected digest; R0 event execution still
rejects any digest other than the packaged authority.

R0 does not claim a general RFC 8785 implementation. The ASCII-only registry
profile makes the accepted Stage 3 canonical JSON ordering unambiguous without
adding a dependency. A future registry that requires non-ASCII identity content
must separately review and test full canonicalization behavior.

## Duplicate-Safe Parsing

Raw registry and raw event JSON must be decoded as UTF-8 with duplicate-property
detection at every object nesting level. Duplicate keys are rejected before a
mapping exists. Parsing also rejects:

- floating-point JSON numbers;
- `NaN`, positive infinity, and negative infinity; and
- integers outside the I-JSON safe range.

Passing a mapping to `validate_event` cannot prove how the mapping was parsed.
Any future append boundary must therefore use the raw-byte
`validate_raw_event_bytes` path, or an independently reviewed parser with the
same pre-mapping guarantees.

## Closed R0 Schema Language

The R0 schema language is `ledger_closed_schema_dsl_v1` version `0.1.0`.
Every node has one closed `kind`; unknown descriptor properties and unknown
kinds are invalid. R0 supports only:

- `named`, for self-contained registry-local type references;
- `literal`, with type-sensitive equality;
- `typed_id`, with one exact lowercase prefix and 32 lowercase hexadecimal
  characters;
- lowercase `sha256`;
- `ledger_v1_utc_timestamp`;
- bounded `safe_integer`;
- `closed_object`, with explicit properties and required names;
- `array`, with explicit item schema, minimum/maximum cardinality, and either
  `ordered` or `sorted_unique` semantics;
- closed `enum`; and
- explicit `nullable`.

There are no defaults, open objects, wildcard fields, free-form validation
code, `eval`, JSONPath, remote references, or implicit coercions. Missing and
explicit null remain different.

R0 exposes one closed local-constraint predicate:
`path_equals_path`. Every constraint ID and both paths are registry-bound and
must resolve in the event schema. Stateful ledger rules remain outside this
shape validator and require later behavioral implementation and tests.

Adding a schema kind or local predicate requires a schema-language version
change and separate review. In particular, tagged unions for artifacts,
access, failures, and other event families are not inferred in R0.

## Registry Coverage Invariant

The registry contains:

1. one ordered, unique closed-event vocabulary;
2. one ordered list of exact supported event schemas, each keyed uniquely by
   `(ledger_schema_version, event_schema_version, event_type)`; and
3. one ordered, unique list of incomplete event types.

Supported and incomplete event types must be disjoint and their union must
equal the closed vocabulary exactly. A missing, duplicate, unknown, reordered,
or multiply keyed event invalidates the registry.

If the incomplete set is nonempty, the only valid registry state is
`SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`. Only a future separately reviewed registry
with no incomplete events may use `PAYLOAD_SCHEMA_REGISTRY_ACCEPTED`. That
state would accept payload shapes only; it would not make Stage 4B runtime
complete.

## Exact Epoch Schema

`LEDGER_EPOCH_CREATED` reuses the exact Stage 4A envelope and payload:

- ledger schema `experiment_trial_ledger_v1`;
- event schema `ledger_event_v1`;
- canonicalization `pit_canonical_json_v1`;
- event and operation-request projection IDs from the accepted ledger
  contract;
- typed ledger, event, operation, and claimed actor-attribution IDs;
- sequence exactly zero;
- previous event SHA-256 exactly null;
- event type exactly `LEDGER_EPOCH_CREATED`;
- subject type exactly `ledger`;
- subject ID exactly equal to `ledger_id`;
- valid ledger-v1 UTC timestamps;
- lowercase operation-request SHA-256; and
- an all-and-only payload containing `campaign_scope_ids`, exactly the empty
  array.

Unknown envelope or payload properties, missing values, null substitution,
Boolean-for-integer substitution, wrong ID prefix, uppercase digest, impossible
timestamp, nonempty scope, and subject mismatch are invalid.

No other event becomes append-valid in R0. The Stage 4A
`incomplete_trial_allocation_stub` remains rejection evidence.

## Conformance Vectors

The digest-bound registry vectors include:

- one exact valid epoch;
- epoch subject mismatch;
- epoch nonempty campaign scope;
- a known but incomplete `TRIAL_ALLOCATED`;
- an unknown event type; and
- a raw duplicate `event_type` in one object.

Independent tests also remove every required epoch envelope and payload field
one at a time, and mutate unknown properties, exact literals, nullability,
Boolean/integer distinction, ID prefixes, digest casing, timestamp validity,
registry keys, coverage partitions, schema keys, type definitions,
cardinalities, raw duplicate keys, oversized or unsafe integers, and
floating-point numbers. They also prove that a self-consistent caller-supplied
event promotion cannot bypass the packaged digest authority.

Vectors are synthetic ASCII evidence only. They do not allocate a ledger or
campaign and do not count as research trials or attempts.

## Deferred Event-Family Decisions

The remaining schemas cannot be reconstructed from Stage 4A test helpers or
narrative field lists. Before an event family becomes supported, a separate
reviewable decision must freeze:

- exact subject type and typed-ID namespace;
- exact all-and-only campaign-scope formula;
- all fields, nested objects, required/optional/null rules, enums, unions, and
  collection order/uniqueness;
- event-local constraints versus stateful ledger invariants;
- safe reason, role, class, and evidence-reference vocabularies; and
- at least one hand-reviewed positive vector plus a killing negative for every
  local constraint.

Candidate batches are allocation/registration, trial/attempt/artifact,
access/exposure, and closure/review/adjudication. `EVENT_SUPERSEDED` requires
special scope and target-binding review. No batch may use a generic object,
free string, opaque metadata, hash-only stand-in, or test-only synthetic fact
set to simulate exact coverage.

Backend, private-location, transaction/recovery, external checkpoint
currentness, authentication/authorization, signature, fork resolution, and any
new production dependency remain separate owner decisions.
