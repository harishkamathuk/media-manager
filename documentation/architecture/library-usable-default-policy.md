# Library Usable-Default Policy

## Purpose

This document defines usable-default Library browsing only in terms of the current Gallery state model already exposed in this repo. It is the source of truth for follow-on work in #111, #112, #113, and #114.

## Current Gallery State Model

- The Gallery frontend consumes `CanonicalFile.integrity_status?: "SUSPECT" | "BROKEN" | null` and no other Library-facing health field (`operator_console/gui_app/src/types/media.ts:1-11`).
- The canonical gallery backend only attaches `integrity_status` when the latest integrity row is `BROKEN` or `SUSPECT`; items with `OK` are surfaced as `integrity_status = null` (`media_manager/app/persistence/operator_console.py:1595-1623`).
- The default gallery dataset currently includes only active canonical items whose paths resolve to `image` or `video` (`media_manager/app/persistence/discovery_query.py:208-259`).
- The existing backend test proves the current Library-facing state surface is:
  - healthy item -> `integrity_status = null`
  - broken item -> `integrity_status = BROKEN`
  - suspect item -> `integrity_status = SUSPECT`
  (`media_manager/tests/test_operator_console_canonical_gallery.py:510-619`).
- The current Library UI text claims usable-default exclusion, and the current Integrity route is shown only for `BROKEN` / `SUSPECT` items (`operator_console/gui_app/src/pages/GalleryPage.tsx:326-356`).

## Policy Table

| Current Gallery state | Included in default Library | Reason |
|---|---|---|
| Active canonical image/video item with `integrity_status = null` | Yes | This is the current healthy/default-visible state exposed by the Gallery model. `OK` is not separately surfaced to the Library; it collapses to `null`. |
| Active canonical image/video item with `integrity_status = BROKEN` | No | This is an explicit integrity-problem state already exposed in Gallery and already associated with Integrity workflow routing. |
| Active canonical image/video item with `integrity_status = SUSPECT` | No | This is an explicit warning/problem state already exposed in Gallery and already associated with Integrity workflow routing. |

## Term Mapping

- `unplayable`: not separately represented in current Gallery state. The current repo only exposes `BROKEN` / `SUSPECT` as Library-facing integrity problem states. If product language continues using `unplayable`, follow-on work should either map it explicitly to one of those states or mark it as broader than the current Gallery model.
- `unreadable`: indirectly present in integrity persistence via `readability_ok`, but not exposed in the current Gallery payload or query inputs (`media_manager/tests/test_operator_console_canonical_gallery.py:584-609`). It is therefore not currently a direct Library policy input.
- `unknown`: not a current Gallery state. `UNKNOWN` exists in duplicate recommendation types, not in `CanonicalFile` or the canonical gallery response (`operator_console/gui_app/src/types/media.ts:53-100`).
- `unscanned`: not a current Gallery state. The Gallery payload does not expose scan presence/absence as a separate field.

## Implementation Notes

- Follow-on backend work should implement usable-default exclusion using only the current Gallery-facing states above unless a later issue deliberately expands the state model.
- Follow-on UI messaging must not claim support for `unplayable`, `unreadable`, `unknown`, or `unscanned` as separate Library rules unless those concepts are first made explicit in Gallery data.
