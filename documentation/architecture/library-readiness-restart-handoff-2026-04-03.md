# Library Readiness Restart Handoff (2026-04-03)

## Purpose

This document is a practical restart guide for continuing the current operator-console product work on another PC without rediscovering already-settled context.

It captures:

- current repository state
- the product and UX decisions that are already settled
- the most important files and documents to read first
- the recommended environment setup and branch workflow
- the next implementation target: `Library Readiness`

This is a handoff note, not a normative spec. `AGENTS.md` and `CONTRIBUTING.md` remain authoritative for runtime safety and contribution workflow.

## Current Repository State

As of this handoff:

- base branch: `develop`
- repo worktree expected state: clean before new work
- latest observed `origin/develop` / `develop` commit during handoff preparation:
  - `c609043` `feat: add duplicate integrity decisioning workflow (#145)`

Important implication:

- the earlier UX modernization work is already merged
- duplicate review has continued evolving well beyond the original UI-only refresh
- `Library Readiness` has not been implemented yet

## Product Direction Already Chosen

These decisions are already established and should be treated as baseline unless deliberately reconsidered.

### Navigation / IA

Primary operator-console navigation is now:

- `Home`
- `Import`
- `Organize`
- `Library`
- `Duplicate Review`
- `Integrity Checks`
- `Admin`

Current route wiring lives in:

- `operator_console/gui_app/src/App.tsx`
- `operator_console/gui_app/src/components/layout/Sidebar.tsx`

### Admin Consolidation

These product changes are already done:

- `Runs` is no longer a top-level destination
- `Ledger` is no longer a top-level destination
- both were folded into the integrated `Admin` workspace
- `Policy` is no longer a primary-nav page in product terms; it now lives in `Admin` as `Library Rules`

Compatibility routes remain in place:

- `/runs` -> Admin activity tab
- `/ledger` -> Admin file-history tab
- `/policy` -> Admin library-rules tab

### Library / Duplicate UX Direction

Already completed:

- `Gallery` was renamed in navigation to `Library`
- the Library hero/header was compacted and de-KPI'd
- the older duplicate screen was redesigned into a user-facing review surface
- the duplicate workspace has since expanded to include recommendation, recycle-bin, restore, and playback issue flows

Important current truth:

- `Duplicate Review` is now both a UX surface and an evolving decisioning workflow
- any new product planning must account for the newer duplicate-integrity architecture, not only the earlier UI refresh work

### Product Framing

The strongest current product direction is:

- Media Manager should act as a preparation and curation layer
- PhotoPrism is the downstream library destination
- the app should optimize for readiness, review, structure, and handoff quality
- it should not drift into building a separate media-consumption product unless there is a direct workflow reason

## Read First On The New Machine

Read these in order before making new design or implementation decisions.

### 1. Safety and workflow

- `AGENTS.md`
- `CONTRIBUTING.md`

Why:

- `AGENTS.md` defines the non-negotiable invariants for this failure-sensitive media system
- `CONTRIBUTING.md` defines the required branch / PR / merge process

### 2. GUI architecture and supported API boundary

- `operator_console/gui_app/README.md`
- `documentation/api/api-operator-console.md`
- `documentation/architecture/api-only-transition.md`

Why:

- these define the supported GUI runtime boundary
- the GUI must consume `/api/*` via the shared API client
- `gui_upstream/` is still reference-only, not runtime authority

### 3. Recent duplicate / integrity architecture

- `documentation/architecture/duplicate-integrity-decisioning-spec.md`
- `documentation/architecture/duplicate-integrity-decisioning-implementation-plan.md`
- `documentation/architecture/duplicate-recycle-bin-lifecycle.md`
- `documentation/architecture/integrity-reclaim-rollout.md`

Why:

- this is the newest major product + architecture seam in the operator console
- it materially changes how duplicate review should be understood and extended
- it is more current than the earlier duplicate UX plan alone

### 4. Current live entrypoints

- `operator_console/gui_app/src/App.tsx`
- `operator_console/gui_app/src/components/layout/Sidebar.tsx`

Why:

- these are the route and navigation truth for the current app

### 5. Current product surfaces

- `operator_console/gui_app/src/pages/DashboardPage.tsx`
- `operator_console/gui_app/src/pages/OperationsPage.tsx`
- `operator_console/gui_app/src/pages/PipelineWizard.tsx`
- `operator_console/gui_app/src/pages/GalleryPage.tsx`
- `operator_console/gui_app/src/pages/DuplicatesPage.tsx`
- `operator_console/gui_app/src/pages/AdminPage.tsx`

Why:

- these pages reflect the current product shape after the IA and UX cleanup work
- any new top-level feature should integrate with this structure rather than re-litigating it

## Environment Setup On The New PC

Start from a fresh checkout and confirm the branch state first.

```bash
git fetch origin
git checkout develop
git pull --ff-only origin develop
git status --porcelain
gh auth status
```

Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

GUI environment:

```bash
cd operator_console/gui_app
npm install
cd "$(git rev-parse --show-toplevel)"
```

Recommended validation before new work:

```bash
./.venv/bin/pytest -q
cd operator_console/gui_app && npm run build
```

If you want a faster UI-focused sanity check first:

```bash
cd operator_console/gui_app
npm test -- src/test/duplicates-page.test.tsx src/test/library-actions-page.test.tsx
npm run build
```

## What Not To Re-Invent

These are already settled enough that they should not be re-solved unless there is a clear reason:

- top-level nav naming (`Home`, `Import`, `Organize`, `Library`, `Duplicate Review`, `Integrity Checks`, `Admin`)
- folding `Runs` and `Ledger` into `Admin`
- moving `Policy` into `Admin` as `Library Rules`
- compact Library hero treatment
- duplicate review’s user-facing framing
- duplicate recommendation derivation direction, which now has dedicated architecture documents

Avoid these traps:

- do not rebuild `Library Readiness` as another `Admin` page
- do not duplicate existing flows from `Organize`, `Library`, or `Duplicate Review`
- do not present weak heuristics as strong readiness truth

## The Next Planned Feature

### Feature Name

`Library Readiness`

### Why it matters

This is the clearest missing product layer in the current app.

The app already has:

- operational actions (`Import`, `Organize`)
- review surfaces (`Library`, `Duplicate Review`, `Integrity Checks`)
- governance / system surfaces (`Admin`)

What it does not yet have is one place that answers:

- `Is this library ready for PhotoPrism?`

### Current implementation status

- planned only
- not present in current routes, navigation, or code
- not mentioned as a first-class feature in current UI

### Intended role

`Library Readiness` should become an outcome-oriented preflight surface that:

- aggregates the most important readiness checks
- stays honest about which checks are authoritative vs advisory
- routes the user into the right existing screen to fix issues
- frames the product around PhotoPrism preparation

## Recommended Phase 1 Shape For Library Readiness

Phase 1 should be deliberately conservative and use existing data sources first.

### Core goals

- answer the user’s readiness question in one place
- avoid inventing a backend-heavy scoring engine immediately
- reuse current API reads and UI surfaces
- keep unsupported or unknown checks explicitly marked as such

### Proposed page behavior

The page should:

- live as a top-level route and navigation item
- present a compact hero with PhotoPrism-oriented framing
- show an overall status:
  - `ready`
  - `warning`
  - `blocked`
  - `unknown`
- show a small set of readiness cards
- provide drill-down CTAs into existing screens

### Phase 1 checks

Use existing read paths only at first.

Recommended initial checks:

- duplicate review status
- library rules status
- processing / recent failed run status
- advisory folder-structure signal if path data is defensible
- metadata quality only if the current API truly supports a credible check

Important constraint:

- do not overclaim metadata quality, sidecar integrity, or PhotoPrism compatibility if the backend does not yet expose those facts robustly

### Phase 1 should not do

- no durable readiness state
- no PhotoPrism API integration
- no sidecar integrity engine
- no export or staging workflow
- no fake scoring model that looks more authoritative than it is

## Suggested Restart Workflow For The Next Feature

When you are ready to continue work, use this exact sequence.

### 1. Rebase on clean `develop`

```bash
git checkout develop
git pull --ff-only origin develop
git status --porcelain
```

### 2. Create a fresh feature branch

Suggested name:

```bash
git checkout -b feature/library-readiness
```

### 3. Implement in this order

1. Add new route and sidebar item
2. Create `LibraryReadinessPage`
3. Add a small readiness-model helper and types
4. Wire existing queries only
5. Build status cards and drill-down CTAs
6. Keep copy plain-English and conservative

### 4. Validate

```bash
cd operator_console/gui_app
npm run build
```

Optional targeted tests:

```bash
npm test -- src/test/duplicates-page.test.tsx
```

If broader changes reach the backend or core workflows:

```bash
cd "$(git rev-parse --show-toplevel)"
./.venv/bin/pytest -q
```

### 5. Finish through the standard PR workflow

Follow `CONTRIBUTING.md` exactly:

- commit on the feature branch
- push the branch
- raise a PR to `develop`
- review from a senior/invariant-safe perspective
- merge only after checks pass
- delete the feature branch after merge

## Recommended Implementation Starting Points

If starting `Library Readiness`, open these files first:

- `operator_console/gui_app/src/App.tsx`
- `operator_console/gui_app/src/components/layout/Sidebar.tsx`
- `operator_console/gui_app/src/pages/GalleryPage.tsx`
- `operator_console/gui_app/src/pages/DuplicatesPage.tsx`
- `operator_console/gui_app/src/pages/AdminPage.tsx`

Why these files:

- `App.tsx` is route truth
- `Sidebar.tsx` is nav truth
- `GalleryPage.tsx`, `DuplicatesPage.tsx`, and `AdminPage.tsx` show the current product voice, density, and interaction style that a new top-level page should match

## Strong Mental Model For Continuing This Work

Think of the current app as four layers:

- `Import` / `Organize`
  - operational workflow
- `Library` / `Duplicate Review` / `Integrity Checks`
  - human review surfaces
- `Admin`
  - rules, diagnostics, deeper investigation
- `Library Readiness`
  - planned outcome layer above the others

That last layer should not replace the existing screens.

Instead, it should:

- summarize readiness
- expose blockers and warnings clearly
- route the user to the right existing screen
- make the app’s PhotoPrism-prep purpose obvious

## Final Notes

Before making new architectural decisions on the new PC:

- always confirm the current `develop` head first
- re-read the duplicate-integrity docs because that area is moving fast
- prefer additive integration over reworking settled IA
- keep Phase 1 of `Library Readiness` honest, small, and defensible

If this document becomes stale, update the observed branch head and any changed route names before using it as the next handoff source.
