# App Settings Authority Model Note

## Status
- Draft
- Date: 2026-04-23

## Context

The "App Settings / ENV Migration" milestone backlog mixes multiple work types:

- authority-model decisions
- concrete DB-first migration slices
- Admin UI/operator clarity
- docs / `.env.sample` / sync hygiene
- final acceptance / drift cleanup

Treating the milestone as a flat backlog would create churn and rework. Some slices depend on settled authority semantics. Others are downstream of those decisions.

## Classification buckets

- `DB-first dual-read` — env provides bootstrap default; DB is authoritative at runtime; reads come from DB
- `env-only` — correctness-sensitive or safety-sensitive; runtime mutation is not safe
- `DB-visible but non-editable` — value lives in DB but is set only at deploy time
- `editable low-risk runtime` — narrow allowlist of safe runtime-editable settings
- `editable but safety-guarded` — editable at runtime but with explicit operator confirmation or destructive-safety checks
- `remove from the surface` — present in catalog/validation but not part of the durable runtime settings surface

## Repo-grounded decisions

### `benchmark_stale_after_seconds`
Recommended: `DB-first dual-read`
Reason: already has a live runtime reader and existing runtime dual-read treatment. Migration path is clear.

### `benchmark_max_items`
Recommended: `remove from the surface`
Reason: present in catalog/validation but not established as an active runtime dual-read authority path.

### `allow_planner_mv_reads`
Recommended: `env-only`
Reason: correctness-sensitive planner/materialized-read safety boundary. Runtime mutation is not obviously safe without an explicit authority decision.

### Storage path family
- `canonical_storage_path` → `env-only`
- `duplicate_storage_path` → `env-only`
- `video_thumbnail_cache_dir` → `DB-first dual-read` (already lower-risk path)

Reason: storage paths involve deployment/bootstrap topology and filesystem concern. Env-only settings are more appropriate for these until a storage-path authority model is explicitly decided.

### Admin-safety family
- `db_reset_include_dynamic` → `env-only`
- `db_reset_challenge_word` → `env-only`

Reason: destructive safety boundary. These settings govern irreversible database operations. Runtime UI mutation is not appropriate.

### `tag_normalization_remove_punctuation`
Recommended: `DB-first dual-read` migration candidate
Reason: low-risk boolean policy input with a narrow read path. Suitable early migration slice.

### `required_metadata_codes`
Recommended: `DB-first dual-read` migration candidate
Reason: plausible candidate but broader planner/required-metadata implications than tag normalization. Lower priority than tag normalization.

### Canonical selection policy inputs
Deferred pending clarification. An existing durable DB-backed `PolicySettingsService` / policy-settings path already exists for these. Authority overlap must be resolved before implementation to avoid conflicting dual-read paths.

## Sprint sequencing consequence

Recommended current sprint order:

1. Settle decisions: #58, #29, #30, #32, #34
2. Implement #28 (tag normalization migration)
3. Implement #27 (required metadata codes migration)
4. Stop and reassess #31 before coding

## Explicitly blocked / deferred

- #33 — blocked by storage-path authority decision
- #35 — blocked by admin-safety authority decision
- #31 — deferred pending clarification against existing policy-settings authority path
- #25, #26, #38 — should not outrun settled backend authority semantics
- #36, #37, #39, #40, #41, #59 — downstream work, not current sprint work

## Practical rule

1. Make authority true
2. Migrate the safe runtime settings
3. Explain it in UI/docs
4. Do cleanup and acceptance