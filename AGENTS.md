# AGENTS.md

This file is the single source of truth for agent operating instructions in this repository.

## Scoped Instructions

- `documentation/LOCAL_INSTRUCTIONS.md`
  - Scope: `documentation/` folder only.
  - Purpose: documentation-specific handling notes.
  - Precedence: this root `AGENTS.md` remains authoritative if any conflict exists.

## Contribution Workflow

- `CONTRIBUTING.md`
  - Scope: human and agent contribution process (branching, PR, review, merge).
  - Purpose: operational workflow guidance.
  - Precedence: this root `AGENTS.md` remains authoritative for runtime invariants and safety constraints.

## Branch Safety Guard

Before making any repository file change, agents must run:

1. `git rev-parse --abbrev-ref HEAD`
2. `git status --porcelain`

Rules:

- If the current branch is `develop`, do not edit files.
- If the current branch is `develop` and `git status --porcelain` is non-empty, warn that there are uncommitted changes on `develop` and stop.
- Require creating or switching to a non-protected branch before any edit.
- Allowed edit branches are `feature/*`, `feat/*`, `fix/*`, `docs/*`, and `chore/*`.
- Do not commit directly to `develop` even if the worktree is clean.

## Pre-Push Validation

Before pushing a branch or opening/updating a PR, agents must run:

1. `python -m pytest -q` from the repository's active project environment

Additional rules:

- If frontend code changed, agents must also run the frontend test command defined by the relevant `package.json` before push/PR.
- Agents must not push or open/update a PR with failing full local Python suite results unless the user explicitly approves skipping or deferring that validation.
- If a validation step is skipped with user approval, the agent must state that clearly in its summary.

## PR Metadata Hygiene

Before opening or updating a PR, agents must verify that the PR has the expected repository metadata applied.

Agents must ensure:

- the PR is assigned appropriately
- the PR has the expected labels for the slice/risk/category
- the PR is linked to the correct project when the repository workflow expects project tracking
- any expected project field values are set or explicitly checked

Canonical sources:

- label expectations come from the repository's existing GitHub label taxonomy
- project and project-field expectations come from the repository's active GitHub project workflow

If any PR metadata step is skipped or cannot be completed, the agent must say so clearly in its summary.

## Issue Metadata Hygiene

Before creating or updating a tracked GitHub issue, agents must verify that the issue has the expected repository metadata applied.

Agents must ensure:

- the issue has the expected labels for the slice/risk/category
- the issue is linked to the correct project when the repository workflow expects project tracking
- any expected project field values are set or explicitly checked

Canonical sources:

- label expectations come from the repository's existing GitHub label taxonomy
- project and project-field expectations come from the repository's active GitHub project workflow

If any issue metadata step is skipped or cannot be completed, the agent must say so clearly in its summary.

## GitHub Project Management

When creating or updating issues that require project field values (e.g., Status), use this deterministic workflow:

### DETERMINISTIC: Add Issue + Set Status in 2 Commands

```bash
# Step 1: Add to project and capture item ID from JSON output
gh project item-add 8 --url "https://github.com/harishkamathuk/media-manager/issues/${ISSUE_NUMBER}" --owner "harishkamathuk" --format json | jq -r '.id'

# Step 2: Set status using the item ID from step 1 + hardcoded status option ID
gh project item-edit --id "${ITEM_ID}" --project-id "PVT_kwHOAK3mu84BTo-6" --field-id "PVTSSF_lAHOAK3mu84BTo-6zhA2m74" --single-select-option-id "${OPTION_ID}"
```

Where:
- `${ISSUE_NUMBER}` = the GitHub issue number (e.g., 114)
- `${ITEM_ID}` = project item ID returned from Step 1 (e.g., `PVTI_lAHOAK3mu84BTo-6zgqQwo8`)
- `${OPTION_ID}` = status option from table below

### Hardcoded Project IDs (Media Manager Delivery - Project #8)

| Project Element | ID |
|-----------------|-----|
| Project | PVT_kwHOAK3mu84BTo-6 |
| Status Field | PVTSSF_lAHOAK3mu84BTo-6zhA2m74 |

Status Options:

| Status | Option ID |
|--------|-----------|
| Backlog | 3f6a1705 |
| Ready | 25b0b2ed |
| In Progress | 27d9491f |
| In Review | 17f0a9e6 |
| Done | 98236657 |
| Blocked | db24be51 |

### Why This Works

- `--format json` on `item-add` + `jq -r '.id'` returns the new item ID directly (no pagination)
- Hardcoded status option IDs skip the lookup round-trip
- `item-edit` returns exit code 0 on success (no output = success)
- Do NOT query for item IDs via pagination - it's flaky and slow

### Adding Milestone to Issue

```bash
gh issue edit ISSUE_NUMBER --milestone "GUI / UX Rework"
```

## Post-PR Monitoring

After opening a PR, agents must monitor the PR for near-term GitHub status changes and review feedback.

Agents must:

- check for GitHub check status, review status, and bot/reviewer feedback after opening the PR
- report any actionable review comments, failing checks, or missing metadata back to the user
- explicitly say if monitoring was attempted but GitHub/network status prevented verification

Agents do not need to monitor indefinitely, but they must perform an initial follow-up pass after PR creation unless the user explicitly declines it.

---

This repository is developed using agent-driven workflows.

Agents are expected to read this file before proposing or applying changes.

This system is a failure-sensitive, stateful media management engine.
It is not a CRUD app. It is not a scripting playground.
Every change must respect runtime invariants.

---

## 1. Core System Invariants

These must NEVER be violated:

1. No filesystem mutation occurs without durable DB gating.
2. All apply operations must be restart-safe.
3. All operations must be idempotent.
4. Planning produces zero side effects.
5. Apply never invents state; it consumes planned state.
6. State transitions must be explicit and validated.
7. Drift must be detectable and observable.
8. Failure must produce durable facts.

If a proposed change weakens any invariant, it is invalid.

---

## 2. Architectural Model

The system is composed of:

- Planner
- Apply Engine
- Canonical Persistence Layer
- Drift Detection
- Failure Logging
- Run Lifecycle Controller

Agents may modify components only if they understand:

- Intent vs Fact separation
- Planned Action vs File Action distinction
- Run lifecycle semantics
- Resume semantics
- Schema gating

If uncertain, inspect schema definitions before proposing logic changes.

---

## 3. Change Discipline

Agents must follow this order:

1. Read schema definitions.
2. Read state transition rules.
3. Identify invariants impacted.
4. Propose change.
5. Define failure semantics.
6. Define idempotency behavior.
7. Define resume behavior.

No change is complete without specifying:

- What happens on crash?
- What happens on retry?
- What happens on partial completion?

---

## 4. Planning Rules

Planner:
- Is pure.
- Reads durable state.
- Emits planned_actions.
- Must be deterministic for identical inputs.
- Must not write filesystem.
- Must not mutate file_actions.

Planner output must be reproducible.

If adding a new action type:
- Define canonical shape.
- Define idempotency key.
- Define validation rules.

---

## 5. Apply Rules

Apply:
- Consumes planned_actions.
- Creates file_actions.
- Performs filesystem mutation only after DB gating.
- Must append failure_events on any error.
- Must abort run on DB write failure.

Strict rule:
If DB write fails, NO filesystem operation may execute.

Resume contract:
- A run may resume only from a durable state boundary.
- Partially completed file_actions must be detectable.
- No action may execute twice unless idempotent by design.

---

## 6. Schema Modifications

Schema changes require:

- Explicit migration plan.
- Backward compatibility statement.
- State transition updates.
- Resume safety validation.
- Drift implications analysis.

Never:
- Remove a column used in gating.
- Change enum values without transition mapping.
- Introduce nullable state columns without invariant review.

---

## 7. Testing Expectations

Any non-trivial change must include:

- Idempotency test
- Resume test
- Failure injection test
- Drift detection test (if applicable)

Tests must validate:

- Crash safety
- Partial execution recovery
- Deterministic planning

---

## 8. Observability

All long-running operations must:

- Emit structured logs
- Record run_id
- Record action_id
- Record timestamps
- Record outcome

No silent failure.
No implicit retries.

---

## 9. Forbidden Patterns

Agents must not:

- Introduce hidden side effects
- Perform filesystem ops outside apply engine
- Mutate durable state inside planner
- Add implicit retries
- Swallow exceptions
- Introduce dual sources of truth

---

## 10. When Unsure

If ambiguity exists:

- Do not guess.
- Do not "simplify".
- Propose clarification instead of implementation.

This system prioritizes safety and determinism over convenience.

---

## 11. OpenCode Pilot Guardrails

Unless the user explicitly instructs otherwise, agent activity in this repository should default to a conservative mode focused on:

- documentation support
- repository reading
- GitHub issue / PR read-and-report tasks

In this conservative mode, agents must not:

- edit code without explicit user instruction
- create or modify GitHub issues, PRs, or comments without explicit approval
- run destructive shell commands
- invent architecture decisions or system behavior not supported by repository sources

For documentation work, agents should:

- prefer the smallest valid documentation artifact
- prefer updating existing documentation over creating overlapping files where appropriate
- classify the requested artifact before editing
- explain why the chosen destination is appropriate
- draft content before applying file edits when the task is exploratory, note-shaping, or documentation design work
