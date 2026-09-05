# Track B v7 Public-Safe Design Candidate

Card: `EFR-TB-DESIGN-CANDIDATE-1`, attempt `A1`, lane `CRITICAL`.
Status: `DESIGN_CANDIDATE_RUNTIME_NOT_IMPLEMENTED`.
Evidence ceiling: `DIAGNOSTIC_ONLY`.

The user identifies plan v7 as accepted. Its two-file manifest SHA-256 is
`4b721dd2f4eb05702a91226697a1684cbbad033476793dec2d4b37b7d778b1b7`. Source Markdown/JSON and the frozen candidate were verified
byte-identical. This is the public normative projection, without private plan
provenance or an independent gate verdict. Base commit:
`6060381f9d821a7f92eb90358413d1ffb189fba4`.

The JSON fixture is a design inventory and synthetic operand specimen, not a
schema registry, authority catalog, external-key type or executable DSL.
Existing schema owners retain authority. Registry releases v1-v9 and the
validator remain unchanged. Runtime tests below are obligations for the later
runtime PR. This candidate runs static design checks and existing repository
tests. No SQLite runtime, append, protected read, trial run, identity operation,
production catalog or investment result is delivered.

## 1. Artifact ownership and frozen baseline

Existing family, sample, binding, trial-allocation, inventory-seal,
attempt-allocation, attempt-start, ledger and registry contracts receive additive
`Track B v7 Design Candidate Extension` sections. Original bytes remain pinned
before those sections. The synthetic fixture records baseline hashes and native
tuple mappings. Existing stronger owner predicates remain mandatory.

Markdown owns normative prose and the required test table. The fixture owns its
structured mirror and synthetic specimens. Every test row and mandatory variant
must match in both directions. Static checks do not prove a passing runtime
catalog or execution of any runtime refusal. The owner gate must approve the
additive schema mappings before runtime admission.

## 2. Families and exact runtime vocabulary

Twelve families partition the 37-name design vocabulary exactly once. Only the
following 14 exact names may append in the runtime PR:

```text
LEDGER_EPOCH_CREATED
CAMPAIGN_ALLOCATED
EXPERIMENT_ALLOCATED
TRIAL_FAMILY_REGISTERED
SAMPLE_REGISTERED
CAMPAIGN_ENTITY_BOUND
STAGE3_SAMPLE_REFERENCE_BOUND
TRIAL_ALLOCATED
CAMPAIGN_INVENTORY_SEALED
ATTEMPT_ALLOCATED
ATTEMPT_STARTED
ACCESS_INTENT
ACCESS_STARTED
ACCESS_COMPLETED
```

| Family | Design vocabulary |
| --- | --- |
| F1 | `LEDGER_EPOCH_CREATED` |
| F2 | `CAMPAIGN_ALLOCATED`, `EXPERIMENT_ALLOCATED`, `TRIAL_FAMILY_REGISTERED`, `SAMPLE_REGISTERED`, `CAMPAIGN_ENTITY_BOUND`, `STAGE3_SAMPLE_REFERENCE_BOUND` |
| F3 | `TRIAL_ALLOCATED` |
| F4 | `CAMPAIGN_INVENTORY_SEALED`, `CAMPAIGN_AMENDMENT_PROPOSED`, `CAMPAIGN_INVENTORY_AMENDED` |
| F5 | `ATTEMPT_ALLOCATED`, `ATTEMPT_STARTED`, `ATTEMPT_COMPLETED`, `ATTEMPT_FAILED`, `ATTEMPT_INVALID`, `ATTEMPT_ABORTED` |
| F6 | `TRIAL_COMPLETED`, `TRIAL_FAILED`, `TRIAL_INVALID`, `TRIAL_ABORTED`, `TRIAL_EXCLUDED` |
| F7 | `ARTIFACT_DISPOSITION_RECORDED` |
| F8 | `ACCESS_INTENT`, `ACCESS_STARTED`, `ACCESS_COMPLETED`, `ACCESS_FAILED`, `ACCESS_ABORTED`, `ACCESS_CANCELLED` |
| F9 | `EXPOSURE_DECISION` |
| F10 | `CAMPAIGN_EVIDENCE_FROZEN`, `CHECKPOINT_REFERENCE_RECORDED`, `CAMPAIGN_ACCOUNTING_CLOSED` |
| F11 | `REVIEW_DECIDED`, `PROMOTION_DECIDED`, `CAMPAIGN_ADJUDICATED` |
| F12 | `EVENT_SUPERSEDED` |

The other 23 names are vocabulary coverage only and refuse with
`WIRE_TYPE_NOT_SELECTED`. Retry relation is non-appendable. Any wire-budget
extension requires an explicit owner gate and new authorization.

## 3. Design delivery and owner admission

This is the single public-safe design candidate for accepted Track B plan v7.
`OD-TB-V7-SCHEMA` is the existing schema/catalog owners' design approval gate.
The owner extensions freeze proposed paths and schema additions; missing or
ambiguous operands block admission. This candidate does not certify an external
catalog or claim that the owner gate has approved the proposed mappings.

The separately authorized later runtime PR uses stdlib `sqlite3`, a
caller-supplied database outside the canonical repository and synthetic catalogs.
Path A is first: epoch, campaign, experiment, family, local sample, trial, seal,
ACCESS_INTENT, then valid ACCESS_STARTED. Path A stops before ACCESS_COMPLETED
and does not claim terminal access completion, because EXPOSURE_DECISION is not
selected in the 14-wire budget; adding it requires an explicit owner gate.
ACCESS_COMPLETED remains selected only so its payload is frozen. No Stage 3 is
needed there. Path B follows through first ATTEMPT_ALLOCATED and ATTEMPT_STARTED.
No retry execution or terminal attempt is selected.

## 4. Transaction, evidence and currentness primitives

Every selected append obtains `BEGIN IMMEDIATE`, then fixes `as_of =
Clock.now_utc()` once. Resolve pinned evidence, inspect committed parents and
current heads, validate, and insert inside that transaction. Synthetic catalog
currentness is one stable snapshot through commit: catalog updates serialize with
the append and cannot race a successful check. A refusal rolls back all event,
head, origin-allocation and capability mutations. Contending writers inspect
state after obtaining the lock, not a pre-lock cache.

Typed owner-frozen catalog, acceptance, generation-authority and projection keys
resolve complete bytes. A resolver hit alone proves neither currentness nor
content equality. Bytes must bind the consuming subject/local ID, campaign scope
and pinned source event ID/hash. Mismatch refuses `RECORD_CONTENT_MISMATCH`.
Sole-current means exactly one valid, accepted, unrevoked, unsuperseded generation
at this `as_of`, using the owner's authority/entity/schema currentness stream.
Missing/noncurrent evidence refuses; stale, superseded and revoked acceptance use
`{EVENT}_ACCEPTANCE_STALE`, `_ACCEPTANCE_SUPERSEDED`, `_ACCEPTANCE_REVOKED` or
`_ACCEPTANCE_NOT_CURRENT`. Publication approval uses the analogous
`{EVENT}_PUBLICATION_APPROVAL_*` codes. Different authority streams must not be
merged merely because local entity IDs coincide.

`revalidate_family`, `revalidate_sample`, and `revalidate_trial_definition` resolve
from retained source-event payload tuples, prove their source bytes and content,
and check sole-current evidence. Family includes definition and acceptance;
sample includes complete record, acceptance, allowlisted projection and publication
approval; trial definition includes definition, acceptance, projection/approval and
trial-allocation authority. Every bound sample and inherited family is checked,
with exact ID-set coverage. Origin creation uses the proposed origin payload and
new local sample ID for the same sample bundle, since no retained origin exists yet.
Complete catalog records carry `private_input_producer_actor_ids`; reviewer
membership refuses `{EVENT}_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION` separately
from other role checks. Missing mandatory evidence or actor fields fails closed.

## 5. Baseline checks at every selected append

`LEDGER_EPOCH_CREATED`: empty ledger, sequence zero, empty payload
`campaign_scope_ids`. `CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED`: reservation-only
scope, existing parent epoch/campaign, unused ID, no definition-bearing fields.

`TRIAL_FAMILY_REGISTERED`: resolve definition and first sole-current acceptance,
content equality to the new family and scope. Reviewer, definition issuer and
envelope actor are pairwise distinct; exclude private-input producers as reviewers.

`SAMPLE_REGISTERED`: resolve complete local record, acceptance, allowlisted
projection and publication approval. Require sole-current acceptance and approval,
content equality to the new local sample, campaign and complete lineage/overlap
fields. Reviewer, record producer and envelope actor are pairwise distinct;
exclude private-input producers as reviewers. Section 6.4's shared origin predicate
is mandatory here, including checks against prior Stage 3 origins.

`STAGE3_SAMPLE_REFERENCE_BOUND`: the complete sample-origin bundle, content,
currentness, roles and shared origin predicate in section 6.4 are mandatory before
append. This is not exempt merely because the family/sample revalidation list
below names downstream events.

`TRIAL_ALLOCATED`: retained campaign/experiment/family/sample source digests match;
revalidate family, every bound sample and trial definition; relation acyclic;
code-tree/patch `prove_content_digest`. Reviewer, definition issuer and allocation
actor are pairwise distinct; reviewer and allocation actor must not belong to the
resolved definition's private-input producer set.

`CAMPAIGN_INVENTORY_SEALED`: section 6.1. `CAMPAIGN_ENTITY_BOUND`: source-byte proof,
content equality, family/sample revalidation and section 6.3 chronology/path checks.

`ATTEMPT_ALLOCATED`: first attempt only; trial in sealed set; current seal head.
Revalidate every family/sample and trial definition. Resolve plan, acceptance and
allocation authority; sole-current acceptance/authority and content binding to the
trial/attempt. Plan code/environment/input/retry/output equal trial definition.
Plan reviewer, plan issuer, trial-definition issuer and allocation actor are
pairwise distinct; reviewer and allocation actor must not be plan private-input
producers. `ATTEMPT_STARTED`: section 6.2.

`ACCESS_INTENT`: seal digest matches and is current; affected trial IDs are a
nonempty subset of the sealed set; empty set refuses
`ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY`; revalidate each affected trial's family
and the access sample. Resolve the three-field authorization and intent authority
and check currentness. Purpose cannot be `design`. Authorization issuer,
intent-authority issuer, accessor, inventory issuer and seal actor are pairwise
distinct; a prohibited equality refuses `ACCESS_INTENT_ROLE_COLLISION`. Bind nonempty typed `evidence_ref_ids` that resolve as immutable safe
evidence references; empty arrays refuse `{EVENT}_EVIDENCE_REF_SET_EMPTY`.
Unknown extra payload fields remain rejected.

`ACCESS_STARTED`: intent digest matches, each affected trial's family and the
sample revalidate, seal head remains current, start authority is current and bound
to this intent/actor/scope. Consume ACCESS in the append transaction. Bind nonempty
typed `evidence_ref_ids` that resolve; empty arrays refuse
`{EVENT}_EVIDENCE_REF_SET_EMPTY`. Unknown extra payload fields remain rejected.
`ACCESS_COMPLETED`: retained start exists; reader code/environment equal the
consumed ACCESS capability's intended reader;
`ACCESS_STARTED.recorded_at <= started_at <= ended_at`. Path A first checkpoint
does not append this event.

The family/sample revalidation boundaries are all-and-only:

```text
CAMPAIGN_INVENTORY_SEALED
CAMPAIGN_ENTITY_BOUND
TRIAL_ALLOCATED
ATTEMPT_ALLOCATED
ATTEMPT_STARTED
ACCESS_INTENT
ACCESS_STARTED
```

Sample-origin validation additionally runs at `SAMPLE_REGISTERED` and
`STAGE3_SAMPLE_REFERENCE_BOUND`. The complete sample-bundle boundary set is those
two origin boundaries plus the seven revalidation boundaries; JSON explicitly
contains both sets and their union. Every origin check runs before insertion.

## 6. Binding repairs and required evidence

### 6.1 Inventory seal and resolved role separation

Within the append transaction resolve the complete inventory, its acceptance and
seal-authority; verify current acceptance and authority, scope/source content and
exact trial-ID set equality, not count equality. The claimed pre-seal head must
equal the stream head. For each sealed trial revalidate trial definition, family
and every bound sample, including publication approval. An invalid parent cannot
be hidden by a valid inventory-level acceptance.

The following semantic field bindings must be frozen to owner-native schema paths
in the design PR. Principals come from resolved bytes, never caller role labels:

| Principal | Resolved source |
| --- | --- |
| `inventory_issuer` | `resolved complete inventory record.issuer_actor_id` |
| `inventory_reviewer` | `resolved inventory acceptance.reviewer_actor_id` |
| `seal_authority_issuer` | `resolved seal-authority record.issuer_actor_id` |
| `seal_actor` | `CAMPAIGN_INVENTORY_SEALED request.actor_id` |
| `authorized_seal_actor` | `resolved seal-authority record.authorized_actor_id` |
| `private_input_producers` | `resolved complete inventory record.private_input_producer_actor_ids` |
| `included_trial_definition_issuer` | `resolved included trial-definition record.issuer_actor_id` |

Require `seal_actor == authorized_seal_actor`. Prohibit these equalities separately:

| Left | Must differ from |
| --- | --- |
| `inventory_reviewer` | `inventory_issuer` |
| `inventory_reviewer` | `seal_authority_issuer` |
| `inventory_reviewer` | `seal_actor` |
| `inventory_reviewer` | `included_trial_definition_issuer` |
| `inventory_issuer` | `seal_actor` |

A prohibited equality refuses `CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION`; an
unauthorized envelope actor refuses `CAMPAIGN_INVENTORY_SEALED_AUTHORITY_ACTOR_MISMATCH`.
Also require inventory reviewer not in `private_input_producers`, with the separate
private-producer refusal. The seal-authority issuer may be its authorized envelope
actor; that equality does not waive any prohibition above. These predicates apply
at seal even when no later ACCESS event occurs.

### 6.2 Attempt start: full inherited tuple equality

The same serialized transaction performs these steps:

1. Digest-match retained allocation and seal; reject prior start, noncurrent seal
   or trial absent from seal. Re-resolve inventory/acceptance from that current seal.
2. Revalidate family, every bound sample and trial definition from retained sources.
3. Re-resolve complete attempt-plan catalog key, plan acceptance and
   attempt-allocation authority from retained `ATTEMPT_ALLOCATED`; prove content
   binding and sole-current plan acceptance/allocation authority at this `as_of`.
4. Resolve the complete readiness record; require current, unsuperseded `READY`
   evidence bound to this trial/attempt/allocation.
5. Separately resolve the event-payload start-authority; require currentness and
   content binding to envelope actor, readiness executor, allocation tuple and
   readiness tuple. Start-authority is not a nested readiness operand.
6. Compare code/environment/input/retry/expected-output across trial definition,
   plan and readiness; mismatch refuses `ATTEMPT_STARTED_INHERITED_VALUE_MISMATCH`.
7. Compare every complete readiness operand below field-for-field against these
   exact same-transaction results. Missing/null fields, different identity or
   generation, omitted/extra samples or families all refuse
   `ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH`. Do not re-resolve a different right-hand
   operand selected by readiness or normalize away tuple identity differences.
8. Validate the constructed event and commit start before allowing EXECUTE consume.

| Readiness operand | Complete fields | Must equal |
| --- | --- | --- |
| `inventory_catalog_key` | Complete owner-typed 8-field inventory key, including sealed_trial_inventory_sha256 | Current inventory re-resolved from retained seal |
| `inventory_acceptance` | Complete owner-typed 4-field inventory acceptance | Sole-current inventory acceptance re-resolved from retained seal |
| `seal_event_id_sha256` | event_id and event_sha256 | Retained current inventory seal |
| `family_definition_and_acceptance` | Complete 8-field definition key, 4-field acceptance, trial_family_id, for every inherited family | Same-transaction revalidate_family results |
| `sample_record_acceptance_projection_publication_approval` | Complete 8-field record key, 4-field acceptance, 3-field projection, 4-field publication approval and sample_id, for every bound sample | Same-transaction revalidate_sample results |
| `trial_definition_acceptance_projection_allocation_authority` | Complete 8-field definition key, 4-field acceptance, complete trial projection and approval, 4-field trial-allocation authority and trial_id | Same-transaction revalidate_trial_definition result |
| `attempt_plan_catalog_key` | Complete owner-typed 8-field attempt-plan catalog key | Exact plan key re-resolved from retained ATTEMPT_ALLOCATED at step 3 |
| `attempt_plan_acceptance` | Complete owner-typed 4-field plan-acceptance tuple | Exact sole-current plan acceptance re-resolved from retained ATTEMPT_ALLOCATED at step 3 |
| `attempt_allocation_authority` | Complete owner-typed 4-field attempt-allocation generation-authority tuple | Exact sole-current allocation authority re-resolved from retained ATTEMPT_ALLOCATED at step 3 |
| `attempt_allocation_event` | event_id and event_sha256 | Retained ATTEMPT_ALLOCATED event |
| `retained_source_event_id_hash` | Every source event_id and event_sha256: family registration, sample origin, campaign binding, trial allocation, inventory seal and attempt allocation | Exact retained source events used by this transaction |

In particular the plan, its acceptance and allocation authority are three distinct
comparisons against step 3, in addition to the allocation event's ID/hash. Equal
operational values do not make different plan evidence equal. Their killing cases
hold all operational values constant and change one readiness tuple at a time.
Start-authority currentness is tested independently of nested allocation authority.

### 6.3 Later-campaign references

Let `seq(C)` be the sequence of the unique committed `CAMPAIGN_ALLOCATED` for C.
An `external_reference` `CAMPAIGN_ENTITY_BOUND` requires target campaign distinct
from origin and `seq(target) > seq(origin)`. Equal campaign refuses
`CAMPAIGN_ENTITY_BOUND_NOT_LATER_CAMPAIGN`; distinct earlier target refuses
`CAMPAIGN_ENTITY_BOUND_EARLIER_CAMPAIGN`; missing campaign allocation refuses parent
order. A new ID alone does not establish chronology.

Binding references the existing sample_id and origin; it never allocates a second
origin (`CAMPAIGN_ENTITY_BOUND_SECOND_ORIGIN`). Target direct scope and binding
cannot coexist (`CAMPAIGN_ENTITY_BOUND_MIXED_PATH`). The origin's external tuple
must remain exact (`CAMPAIGN_ENTITY_BOUND_EXTERNAL_TUPLE_DRIFT`). Source-byte proof,
content equality and current family/sample evidence remain mandatory.

### 6.4 Complete Stage 3 bundle and symmetric origin exclusion

Before `STAGE3_SAMPLE_REFERENCE_BOUND`, resolve the complete Stage 3 sample record,
acceptance, allowlisted projection and publication approval. Acceptance and
publication approval must each be sole-current immediately before insertion at
this transaction's `as_of`; stale, superseded, revoked or absent evidence refuses
with the boundary-qualified codes in section 4. Require content equality to the
new local sample_id, campaign scope, pinned source bytes and the complete record's
canonical lineage and overlap fields. Sample reviewer, record producer and binding
envelope actor are pairwise distinct; reviewer is excluded from the complete
record's private-input producer set. These are the same sample-origin predicates
as local registration, with external complete-record resolution.

Both complete local and Stage 3 records must provide `canonical_sample_lineage_id`
as a `safe_public_id`. Resolve it from complete bytes; never synthesize it from the
local sample_id or trust request-only text. The complete owner authority/record
identity tuple is also taken from resolved bytes. Mutable acceptance/publication
generations do not create a new record identity. Missing local lineage refuses
`SAMPLE_REGISTERED_LINEAGE_REQUIRED`; any missing required origin identity blocks
admission under the design owner gate.

Within one ledger epoch, across all campaigns, there is at most one origin,
representation path and local sample_id for each canonical lineage and for each
exact authority/record identity tuple. At BOTH `SAMPLE_REGISTERED` and
`STAGE3_SAMPLE_REFERENCE_BOUND`, search committed origins of BOTH types and test
both uniqueness keys before insertion. A different tuple cannot bypass the lineage
check; the same tuple cannot be reintroduced as another identity. Neither a later
campaign nor another acceptance generation resets this invariant.

For deterministic refusals, an already allocated sample_id refuses
`SAMPLE_ID_ALREADY_ALLOCATED`; otherwise an exact record identity match refuses
`{EVENT}_RECORD_DUP`; otherwise a lineage match through the other representation
path refuses `{EVENT}_ORIGIN_PATH_CONFLICT`; a lineage match on the same path
refuses `{EVENT}_LINEAGE_DUP`. The tuple and lineage prohibitions are both mandatory
regardless of which refusal takes precedence. A second origin using the same ID
is also rejected; request replay must not append another origin.

The committed-state search and origin insertion are atomic under the writer lock.
Two competing connections, in either order, yield exactly one committed origin;
the loser rechecks committed state and refuses. Both local→external and
external→local paths, same-path collisions, exact tuple collisions and equal-lineage
but different-tuple collisions have mandatory tests. A later-campaign binding that
reuses the original sample_id is a legitimate reference subject to section 6.3,
and creates no additional origin or uniqueness reservation.

### 6.5 Complete v7-owned killing-test union

The table below and JSON `append_boundary_checks.killing_tests_v7` contain the
same exhaustive test IDs, boundary, fault and refusal content. All 40 predecessor
markdown IDs are retained with v7-owned conditions, plus the new cases. There is
no remainder-only test list. Every listed independent variant is mandatory in the
later runtime PR; an OR-fault fixture does not satisfy multiple variants.

Each negative starts from a passing synthetic boundary fixture. Change only the
specified operand; recompute fixture digests so malformed bytes or stale wrapper
hashes do not mask the intended predicate. Require the named refusal and no event,
head, origin or capability mutation, except the single winning concurrent append.
Where tuple and lineage guards overlap, assert each guard independently on the
resolved bundle as well as the full append refusal; removing one guard need not
make the append succeed while another mandatory guard still rejects it. Current
readiness wrapper evidence and all retained-allocation revalidation stay valid for nested
mismatch tests, while operational values stay equal. These are design obligations,
not tests executed by this authoring card. Refusal strings below are v7 design
mappings to freeze in the one design PR.

| ID | Boundary | Fault / mandatory independent variants | Refusal |
| --- | --- | --- | --- |
| T-B-START-READY-INV-TUPLE | ATTEMPT_STARTED | Mutate only the readiness inventory catalog key. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-FAM-TUPLE | ATTEMPT_STARTED | Mutate one readiness family tuple. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. Independent variants: definition key; acceptance tuple. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-SAMP-TUPLE | ATTEMPT_STARTED | Mutate one readiness sample tuple. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. Independent variants: record key; acceptance tuple; projection tuple. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-DEF-TUPLE | ATTEMPT_STARTED | Mutate only readiness trial-definition key. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-ACC-TUPLE | ATTEMPT_STARTED | Mutate one readiness acceptance tuple. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. Independent variants: inventory acceptance only; trial-definition acceptance only. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-PUB-TUPLE | ATTEMPT_STARTED | Mutate only readiness sample publication-approval tuple. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-AUTH-TUPLE | ATTEMPT_STARTED | Mutate only readiness attempt-allocation authority tuple; never start-authority. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-SRC-TUPLE | ATTEMPT_STARTED | Mutate one readiness retained source event hash. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. Independent variants: family registration; sample origin; trial allocation; inventory seal; campaign binding; attempt allocation. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-PLAN-TUPLE | ATTEMPT_STARTED | Mutate only readiness complete attempt-plan 8-field catalog key. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-PLAN-ACC-TUPLE | ATTEMPT_STARTED | Mutate only readiness complete plan-acceptance 4-field tuple. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-SEAL-TUPLE | ATTEMPT_STARTED | Mutate only readiness seal event id/hash. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-ALLOCATION-TUPLE | ATTEMPT_STARTED | Mutate only readiness attempt-allocation event id/hash. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-TRIAL-AUTH-TUPLE | ATTEMPT_STARTED | Mutate only readiness trial-allocation authority tuple. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-TRIAL-PUB-TUPLE | ATTEMPT_STARTED | Mutate only readiness trial projection or approval. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. Independent variants: projection only; approval only. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-SAMPLE-SET | ATTEMPT_STARTED | Omit or add an inherited sample in readiness. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. Independent variants: missing sample; extra sample. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-READY-FAM-SET | ATTEMPT_STARTED | Omit or add an inherited family in readiness. Keep plan/trial/readiness code, environment, input, retry and expected-output values identical; keep the retained allocation and catalog revalidation valid. Independent variants: missing family; extra family. | ATTEMPT_STARTED_INHERITED_TUPLE_MISMATCH |
| T-B-START-PLAN-STALE | ATTEMPT_STARTED | Retained attempt plan acceptance is stale. | ATTEMPT_STARTED_ACCEPTANCE_STALE |
| T-B-START-AUTH-STALE | ATTEMPT_STARTED | Event-payload start-authority is stale; inherited allocation authority remains valid. | ATTEMPT_STARTED_START_AUTHORITY_STALE |
| T-B-START-ALLOC-AUTH-STALE | ATTEMPT_STARTED | Retained attempt-allocation authority is stale; event-payload start-authority remains valid. | ATTEMPT_STARTED_ALLOCATION_AUTHORITY_STALE |
| T-B-START-READY-STALE | ATTEMPT_STARTED | Readiness itself is stale or superseded. Independent variants: stale readiness; superseded readiness. | ATTEMPT_STARTED_READINESS_NOT_CURRENT |
| T-B-START-INHERITED-MISMATCH | ATTEMPT_STARTED | Change only one operational value across readiness and accepted plan/trial definition. Independent variants: code; environment; input; retry; expected output. | ATTEMPT_STARTED_INHERITED_VALUE_MISMATCH |
| T-B-START-EXEC | ATTEMPT_STARTED | Start-authority binds a different executor than readiness.executor_actor_id. | ATTEMPT_STARTED_EXECUTOR_MISMATCH |
| T-B-BOUND-NOT-LATER | CAMPAIGN_ENTITY_BOUND | External target campaign equals origin campaign. | CAMPAIGN_ENTITY_BOUND_NOT_LATER_CAMPAIGN |
| T-B-BOUND-EARLIER | CAMPAIGN_ENTITY_BOUND | Distinct target campaign has a lower committed CAMPAIGN_ALLOCATED sequence. | CAMPAIGN_ENTITY_BOUND_EARLIER_CAMPAIGN |
| T-B-BOUND-SECOND-ORIGIN | CAMPAIGN_ENTITY_BOUND | Try to allocate a new local sample_id through an external-reference bind. | CAMPAIGN_ENTITY_BOUND_SECOND_ORIGIN |
| T-B-BOUND-MIXED-PATH | CAMPAIGN_ENTITY_BOUND | Target campaign already appears in origin direct scope; also request a binding. | CAMPAIGN_ENTITY_BOUND_MIXED_PATH |
| T-B-EXT-DRIFT | CAMPAIGN_ENTITY_BOUND | Change the external record tuple from the retained origin. | CAMPAIGN_ENTITY_BOUND_EXTERNAL_TUPLE_DRIFT |
| T-B-STAGE3-DUP-TUPLE | STAGE3_SAMPLE_REFERENCE_BOUND | Existing Stage 3 origin has the same authority/record identity tuple; propose a new local sample_id. | STAGE3_SAMPLE_REFERENCE_BOUND_RECORD_DUP |
| T-B-STAGE3-DUP-LINEAGE-DIFF-TUPLE | STAGE3_SAMPLE_REFERENCE_BOUND | Existing Stage 3 origin has same canonical lineage but different authority/record tuple; propose a new local sample_id. | STAGE3_SAMPLE_REFERENCE_BOUND_LINEAGE_DUP |
| T-B-STAGE3-LOCAL-PATH | STAGE3_SAMPLE_REFERENCE_BOUND | Commit local origin first; propose external origin for same lineage with a different tuple and sample_id. | STAGE3_SAMPLE_REFERENCE_BOUND_ORIGIN_PATH_CONFLICT |
| T-B-LOCAL-AFTER-STAGE3-LINEAGE | SAMPLE_REGISTERED | Commit Stage 3 origin first; propose local origin for same lineage with a different tuple and sample_id. | SAMPLE_REGISTERED_ORIGIN_PATH_CONFLICT |
| T-B-LOCAL-AFTER-STAGE3-TUPLE | SAMPLE_REGISTERED | Commit Stage 3 origin first; propose local origin with identical authority/record identity tuple and a new sample_id. | SAMPLE_REGISTERED_RECORD_DUP |
| T-B-LOCAL-DUP-LINEAGE | SAMPLE_REGISTERED | Existing local origin has same lineage but a different record tuple; propose another sample_id. | SAMPLE_REGISTERED_LINEAGE_DUP |
| T-B-LOCAL-DUP-TUPLE | SAMPLE_REGISTERED | Existing local origin has identical authority/record identity tuple; propose another sample_id. | SAMPLE_REGISTERED_RECORD_DUP |
| T-B-STAGE3-CONTENT | STAGE3_SAMPLE_REFERENCE_BOUND | Resolved complete record disagrees with requested local sample_id, campaign, lineage or overlap. | RECORD_CONTENT_MISMATCH |
| T-B-LOCAL-LINEAGE-MISSING | SAMPLE_REGISTERED | Resolved local record lacks canonical_sample_lineage_id. | SAMPLE_REGISTERED_LINEAGE_REQUIRED |
| T-B-STAGE3-ROLE | STAGE3_SAMPLE_REFERENCE_BOUND | One prohibited role equality or private-producer membership only. Independent variants: reviewer=producer; reviewer=envelope actor; producer=envelope actor; reviewer in private_input_producer_actor_ids. | STAGE3_SAMPLE_REFERENCE_BOUND_ROLE_COLLISION; private-producer variant uses STAGE3_SAMPLE_REFERENCE_BOUND_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION |
| T-B-STAGE3-ACC-STALE | STAGE3_SAMPLE_REFERENCE_BOUND | Pinned sample acceptance is stale at transaction as_of; all other evidence and roles valid. | STAGE3_SAMPLE_REFERENCE_BOUND_ACCEPTANCE_STALE |
| T-B-STAGE3-ACC-SUPERSEDED | STAGE3_SAMPLE_REFERENCE_BOUND | Pinned sample acceptance is superseded at transaction as_of; all other evidence and roles valid. | STAGE3_SAMPLE_REFERENCE_BOUND_ACCEPTANCE_SUPERSEDED |
| T-B-STAGE3-PUB-STALE | STAGE3_SAMPLE_REFERENCE_BOUND | Pinned publication approval is stale at transaction as_of; all other evidence and roles valid. | STAGE3_SAMPLE_REFERENCE_BOUND_PUBLICATION_APPROVAL_STALE |
| T-B-STAGE3-PUB-SUPERSEDED | STAGE3_SAMPLE_REFERENCE_BOUND | Pinned publication approval is superseded at transaction as_of; all other evidence and roles valid. | STAGE3_SAMPLE_REFERENCE_BOUND_PUBLICATION_APPROVAL_SUPERSEDED |
| T-B-ORIGIN-CONCURRENT | SAMPLE_REGISTERED + STAGE3_SAMPLE_REFERENCE_BOUND | Two connections race origin allocations for the same epoch lineage with different record tuples and sample_ids. Independent variants: local obtains writer lock first; Stage 3 obtains writer lock first. | Loser: {EVENT}_ORIGIN_PATH_CONFLICT; exactly one origin commits. |
| T-B-ORIGIN-CONCURRENT-SAME-PATH | SAMPLE_REGISTERED or STAGE3_SAMPLE_REFERENCE_BOUND | Two connections race different sample_ids for one epoch lineage on the same path. Independent variants: local/local different tuples; Stage3/Stage3 different tuples; local/local same tuple; Stage3/Stage3 same tuple. | Loser: {EVENT}_LINEAGE_DUP for different tuples, {EVENT}_RECORD_DUP for same tuple; exactly one origin commits. |
| T-B-SEAL-PARENT-FAM-STALE | CAMPAIGN_INVENTORY_SEALED | One sealed trial family acceptance is stale. | CAMPAIGN_INVENTORY_SEALED_ACCEPTANCE_STALE |
| T-B-SEAL-PARENT-SAMP-STALE | CAMPAIGN_INVENTORY_SEALED | One sample acceptance in one sealed trial is stale. | CAMPAIGN_INVENTORY_SEALED_ACCEPTANCE_STALE |
| T-B-SEAL-PARENT-DEF-STALE | CAMPAIGN_INVENTORY_SEALED | One sealed trial-definition acceptance is stale. | CAMPAIGN_INVENTORY_SEALED_ACCEPTANCE_STALE |
| T-B-SEAL-REVIEWER-ISSUER | CAMPAIGN_INVENTORY_SEALED | Inventory acceptance reviewer equals inventory issuer; neither is a private-input producer. | CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION |
| T-B-SEAL-REVIEWER-ACTOR | CAMPAIGN_INVENTORY_SEALED | Inventory acceptance reviewer equals envelope seal actor; private-producer exclusion still passes. | CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION |
| T-B-SEAL-REVIEWER-AUTHORITY | CAMPAIGN_INVENTORY_SEALED | Inventory acceptance reviewer equals seal-authority issuer only. | CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION |
| T-B-SEAL-REVIEWER-TRIAL-ISSUER | CAMPAIGN_INVENTORY_SEALED | Inventory acceptance reviewer equals one included trial-definition issuer; all other roles remain valid. | CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION |
| T-B-SEAL-ISSUER-ACTOR | CAMPAIGN_INVENTORY_SEALED | Inventory issuer equals seal actor only. | CAMPAIGN_INVENTORY_SEALED_ROLE_COLLISION |
| T-B-SEAL-AUTHORIZED-ACTOR | CAMPAIGN_INVENTORY_SEALED | Envelope actor differs from resolved seal authority authorized_actor_id. | CAMPAIGN_INVENTORY_SEALED_AUTHORITY_ACTOR_MISMATCH |
| T-B-FAM-STALE-TRIAL | TRIAL_ALLOCATED | Parent family acceptance is stale. | TRIAL_ALLOCATED_ACCEPTANCE_STALE |
| T-B-FAM-STALE-ATTEMPT | ATTEMPT_ALLOCATED | Parent family acceptance is stale. | ATTEMPT_ALLOCATED_ACCEPTANCE_STALE |
| T-B-FAM-STALE-ACCESS | ACCESS_INTENT | One affected trial family acceptance is stale. | ACCESS_INTENT_ACCEPTANCE_STALE |
| T-B-FAM-STALE-ACCESS-STARTED | ACCESS_STARTED | One affected trial family acceptance becomes stale after intent. | ACCESS_STARTED_ACCEPTANCE_STALE |
| T-B-SAMP-PUB-BIND | CAMPAIGN_ENTITY_BOUND | Sample publication approval is stale. | CAMPAIGN_ENTITY_BOUND_PUBLICATION_APPROVAL_STALE |
| T-B-SAMP-PUB-TRIAL | TRIAL_ALLOCATED | One bound sample publication approval is stale. | TRIAL_ALLOCATED_PUBLICATION_APPROVAL_STALE |
| T-B-SAMP-PUB-ACCESS | ACCESS_INTENT | Access sample publication approval is stale. | ACCESS_INTENT_PUBLICATION_APPROVAL_STALE |
| T-B-CONTENT-SCOPE | TRIAL_ALLOCATED | Resolved definition bytes bind another campaign scope despite a resolver hit. | RECORD_CONTENT_MISMATCH |
| T-B-SEAL-STALE-ATT | ATTEMPT_ALLOCATED | Referenced seal is not the current seal head. | ATTEMPT_ALLOCATED_SEAL_NOT_CURRENT |
| T-B-SEAL-STALE-ACC | ACCESS_INTENT | Referenced seal is not the current seal head. | ACCESS_INTENT_SEAL_NOT_CURRENT |
| T-B-NOT-IN-SEAL | ATTEMPT_ALLOCATED | Requested trial is absent from sealed_trial_ids. | ATTEMPT_ALLOCATED_TRIAL_NOT_IN_SEAL |
| T-B-PRIV-TRIAL | TRIAL_ALLOCATED | Definition reviewer belongs to private_input_producer_actor_ids despite otherwise separated actors. | TRIAL_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION |
| T-B-PRIV-INV | CAMPAIGN_INVENTORY_SEALED | Inventory acceptance reviewer belongs to inventory private_input_producer_actor_ids despite otherwise separated actors. | CAMPAIGN_INVENTORY_SEALED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION |
| T-B-PRIV-PLAN | ATTEMPT_ALLOCATED | Plan reviewer belongs to plan private_input_producer_actor_ids despite otherwise separated actors. | ATTEMPT_ALLOCATED_PRIVATE_INPUT_PRODUCER_ROLE_COLLISION |
| T-M3-5-START-ACTOR | EXECUTE capability consume after ATTEMPT_STARTED | Use start-event actor as consumer when readiness executor is a different actor. | CAPABILITY_CONSUMER_MISMATCH |
| T-B-INGRESS-COMMIT-FIELDS | ledger_operation_request_v1 ingress | Caller supplies a store-owned event field. Independent variants: sequence; recorded_at; previous_event_sha256; operation_request_sha256. | OPERATION_REQUEST_COMMIT_FIELD_FORBIDDEN |
| T-B-ACCESS-ATOMIC-ROLLBACK | ACCESS_STARTED | Force event validation failure after tentative ACCESS consumption within the transaction. | Injected append refusal; capability remains unconsumed, no event or head change. |
| T-B-ACCESS-EMPTY-TRIALS | ACCESS_INTENT | Request affected_trial_ids is empty; current seal and all other evidence remain valid. | ACCESS_INTENT_AFFECTED_TRIAL_SET_EMPTY |
| T-B-ACCESS-COMPLETED-BEFORE-START | ACCESS_COMPLETED | started_at is earlier than retained ACCESS_STARTED.recorded_at; ended_at remains after started_at. Path A does not append this event. | ACCESS_COMPLETED_STARTED_AT_BEFORE_START_COMMIT |
| T-B-ACCESS-EMPTY-EVIDENCE-REFS | ACCESS_INTENT, ACCESS_STARTED, ACCESS_COMPLETED | Request evidence_ref_ids is empty; all other evidence remains valid. Independent variants: ACCESS_INTENT; ACCESS_STARTED; ACCESS_COMPLETED. | {EVENT}_EVIDENCE_REF_SET_EMPTY |
| T-B-ACCESS-ROLE-COLLISION | ACCESS_INTENT | One prohibited equality among the five pairwise-distinct resolved principals; all other evidence remains valid. Independent variants: authorization issuer=intent-authority issuer; authorization issuer=accessor; authorization issuer=inventory issuer; authorization issuer=seal actor; intent-authority issuer=accessor; intent-authority issuer=inventory issuer; intent-authority issuer=seal actor; accessor=inventory issuer; accessor=seal actor; inventory issuer=seal actor. | ACCESS_INTENT_ROLE_COLLISION |

Positive controls: Path A first through ACCESS_INTENT then ACCESS_STARTED, stopping
before ACCESS_COMPLETED because EXPOSURE_DECISION is not selected; Path B with all
exact readiness operands equal; each origin path alone in a fresh epoch;
later-campaign reference reusing the same sample_id; and matching EXECUTE
consumption by a readiness executor different from the start-event actor.

Artifact QA must parse JSON; prove the 12/37/14/23 inventory, exact operand and
boundary agreement, and bidirectional ID-set equality and uniqueness; compare every
test row's boundary/fault/variants/refusal, retain all 40 predecessor markdown IDs,
and map all nine OPEN MATERIAL findings independently with nonempty coverage IDs.
Hash both public design Markdown/JSON deliverables into
`docs/experiment_trial_ledger_track_b_v7_design.artifacts.sha256`, then hash that
manifest. These document checks cannot establish runtime correctness or independent
gate acceptance.

## 7. Capability and ingress rules retained

Ingress is `ledger_operation_request_v1`. Reject caller-supplied commit-owned
sequence, recorded_at, previous-event hash and `operation_request_sha256`
fields. The store assigns these
inside `BEGIN IMMEDIATE`, then calls `validate_raw_event_bytes` on the constructed
event only. Invalid requests never bypass event validation or advance the head.

EXECUTE's intended consumer is the resolved readiness `executor_actor_id`.
The start-authority binds both that executor and the start-event envelope actor.
After committed `ATTEMPT_STARTED`, EXECUTE consume checks executor, trial/attempt,
code and environment; the start-event actor cannot substitute for the executor.
This specifies scope/consumer binding, not production authentication. ACCESS
consume and `ACCESS_STARTED` commit atomically; failure leaves the capability
unconsumed and event/head unchanged.

## 8. Access-pack payloads

Option `TB-XPO-1`. The following are all-and-only payload lists, matching JSON:

**ACCESS_INTENT_payload_all_and_only**

```text
campaign_scope_ids
inventory_seal_event_id
inventory_seal_event_sha256
sample_id
affected_trial_ids
purpose
intended_window_id
intended_field_class_ids
accessor_code_tree_sha256
accessor_environment_id
accessor_environment_lock_sha256
authorization_record_id
authorization_record_schema_version
authorization_record_sha256
intent_authority_generation
intent_authority_id
intent_authority_record_sha256
intent_authority_schema_version
access_capability_id
access_capability_record_canonicalization_id
access_capability_record_schema_version
access_capability_record_sha256
access_capability_record_version
evidence_ref_ids
```

**ACCESS_STARTED_payload_all_and_only**

```text
campaign_scope_ids
access_intent_event_id
access_intent_event_sha256
access_capability_id
reader_code_tree_sha256
reader_environment_id
reader_environment_lock_sha256
start_authority_generation
start_authority_id
start_authority_record_sha256
start_authority_schema_version
sample_id
evidence_ref_ids
```

**ACCESS_COMPLETED_payload_all_and_only**

```text
campaign_scope_ids
access_started_event_id
access_started_event_sha256
sample_id
actual_window_id
names_observed
protected_material_observed
reader_code_tree_sha256
reader_environment_id
reader_environment_lock_sha256
started_at
ended_at
backfilled
evidence_ref_ids
```
