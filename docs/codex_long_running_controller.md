# Codex Long-Running Controller

Canonical responsibility: staged workflow state transitions, external gates,
GitHub review lifecycle, waiting, stop conditions, and completion reporting.

## Scope And Authority

This process is subordinate to the
[repository authority boundary](../AGENTS.md#authority-and-scope), research
charter, and current higher-level instructions. It grants no authority.
Eligibility is not authorization; every external, sensitive, or destructive
operation must satisfy that boundary.

## Startup And Freshness

1. After `AGENTS.md`, read `docs/current_handoff.md`,
   `docs/codex_long_running_controller.md`, and `docs/current_roadmap.md` for the
   recorded checkpoint, execution gates, and program status, respectively.
2. Use `docs/repo_map.md` for targeted orientation and read only active-stage
   contracts. Research or code stages also require `PROJECT_SPEC.md`.
3. With capped output, check branch/tree state, local and remote `main`, recent
   history, and relevant PR state; verify the live remote before choosing a base.
4. If the tree is dirty or diverged, preserve it in place and use a clean
   worktree. Do not pull, reset, clean, or stash unreviewed user work.
5. Classify unrelated open or Draft PRs once by dependency, changed-file overlap,
   and semantic conflict. Do not rebase, close, merge, or overwrite them without
   authorization.

## Select And Bound The Stage

- `docs/current_handoff.md` owns the latest recorded operational checkpoint and
  next-safe-action routing. Its remote facts are cached evidence, not live state.
- `docs/current_roadmap.md` owns program stage sequence, dependencies, gate and
  completion criteria, and coarse stage status.
- Choose one coherent stage; keep unrelated fixes in separate branches and PRs.
- Research methodology comes from `PROJECT_SPEC.md`, the charter, roadmap, and
  `docs/eodhd_sp500_diagnostic_campaign_contract.md`, not this controller.
- Do not infer permission for vendor access, protected samples, private results,
  deployment, brokerage behavior, or a broader research interpretation from a
  stage description.

## Local Execution And Validation

- Use a clean `codex/` branch or worktree and state the intended edits first.
- Add or update tests and durable records required by `AGENTS.md`; stage only
  files in the declared scope.
- Run focused tests, then the baselines defined by `.github/workflows/ci.yml`.
- Check whitespace in all states: `git diff --check`,
  `git diff --cached --check`, and `git diff --check origin/main...HEAD` (or the
  established base range) for unstaged, staged, and committed changes.
- For workflow/Skill changes, audit the Skill and deterministically regenerate
  `docs/repo_map.md`. Before publication, review scope, Unicode, privacy, and guardrails.
- Use `docs/engineering_log.md` for implementation/process evidence,
  `docs/decision_log.md` for durable choices, `docs/troubleshooting_log.md` for
  failures, and `EXPERIMENT_LOG.md` only for research experiments.

## External Authorization Gate

Apply the [repository authority boundary](../AGENTS.md#authority-and-scope) to
external, sensitive, or destructive operations. Workflow eligibility and
successful checks do not grant authority. Without explicit action-and-scope
authorization, stop after local validation.

## Predecessor PR Gate

- If a required predecessor is not verified merged, check once, report one gate
  summary, and pause. Without an explicit merged/resume/inspect request, do not
  re-query an unchanged gate, rerun baselines, or start its dependent stage.
- An unrelated PR is not automatically a predecessor. Record why it is
  independent and avoid overlapping files.
- Continue only from the newly verified remote baseline after the predecessor
  merges. A clean status check must precede any branch switch or update.

## GitHub Review Lifecycle

- Keep GitHub Codex Automatic Review disabled. Drafts get no request; an explicit
  `@codex review` is sent once only after validation and required CI stabilize on
  the final stable current head.
- Review is required for research semantics, returns, costs, benchmarks,
  implementation, CI, security, data handling, or execution scope. Trivial
  spelling, date, count, or equivalent metadata-only edits may omit it.
- Never repeat a request for an unchanged head. An actionable fix changes the
  head and requires validation, CI, and one new current-head review.
- A safe actionable finding may be fixed locally inside the already-authorized
  scope. Push and review-request actions still pass through the External
  Authorization Gate; a remediation authorization cannot expand the stage.
- A review-required PR is technically merge-eligible only when its current head
  has no unresolved actionable finding and all required checks and reviews pass.
  Technical eligibility never grants merge authority or action authorization.

## Waiting And Follow-Up

- Report an unchanged external gate once and pause; define no polling schedule.
- Use a product monitor or recurring wait only when the user explicitly requests
  monitoring. Reuse one matching monitor, perform read-only checks, and never
  duplicate review requests.
- Never decide a critical owner choice on the owner's behalf. Missing authority
  remains a paused gate rather than an implicit approval.

## Protected Merge Eligibility

Technical eligibility requires low/clear risk, expected author/head owner,
verified protections, checks and reviews, conflict/queue state, and file scope.
Pending or unverifiable evidence is ineligible; eligibility never authorizes
auto-merge or merge.

## Stop Conditions

Stop for missing authority; unclear tree/branch ownership; failed validation
outside safe remediation; unresolved P1/high risk; unverifiable protection,
checks, reviews, conflicts, or scope; destructive/security/privacy risk; or
unresolved provenance, license, point-in-time, benchmark, cost, timing, or
statistical choices. Also stop before unapproved vendor/private data,
credentials, brokerage/orders, live behavior, or out-of-scope interpretation.

## Completion Report

Report branch, commit/PR, risk, files, checks, findings, assumptions, external
authorization, and next gate. Keep state with the owners named in `Select And
Bound The Stage`, and history in logs; do not duplicate either across active sources.
