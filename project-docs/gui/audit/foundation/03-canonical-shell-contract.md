# Canonical page shell proposal

You do **not** need many shells.
You need **one base shell** and **three allowed variants max**.

Anything beyond that will turn into page-by-page improvisation again.

---

## 1. Core rule: one shared base shell for everything

Every page should inherit the same base frame.

### Base shell contract

#### A. Persistent app chrome

Already present and broadly fine:

* left nav
* top system bar

Do not let individual pages reinvent this layer.

#### B. Page container

Inside the chrome, every page should start with one consistent page container:

* same max width behavior
* same top padding
* same left/right padding
* same vertical spacing rhythm
* same content alignment line

This is the first discipline you are missing.

#### C. Standard page anatomy

Every page should be composed from these zones only:

1. **Page header**
2. **Optional page controls row**
3. **Primary work area**
4. **Optional secondary/supporting area**

That is it.

No random extra intro band, no floating summary strip, no ad hoc card row unless the shell variant explicitly allows it.

---

## 2. Variant A — Standard admin shell

This should be the default shell for most pages.

Use it for:

* Home
* Integrity Checks
* most Admin tabs
* simple settings/tool pages
* overview/monitoring pages

### Structure 1

#### Zone 1: Compact page header

Contains only:

* page title
* short one-line description or context
* optional compact page-level status on the right

It should **not** contain:

* large CTA buttons
* multiple cards
* long explanation blocks
* workflow teaching copy
* duplicated navigation

#### Zone 2: Optional page controls row

Directly below the header.

This row is for page-scoped controls such as:

* primary page action
* secondary action
* mode toggle
* filter summary
* date range
* scan/run action

This row should be:

* compact
* horizontal
* predictable
* visually subordinate to the title but above content

#### Zone 3: Main content body

This is the dominant area.

Allowed content types:

* overview metrics
* table/list
* split master-detail
* form/tool panel
* dashboard blocks

#### Zone 4: Secondary/supporting content

Only below the main work area, or in a right-side panel when the page genuinely needs persistent detail.

Good uses:

* technical notes
* logs
* expanded diagnostics
* secondary charts
* explanatory help

Not allowed:

* repeating the page introduction again

### When to use

Use this shell when the user is primarily:

* monitoring
* checking status
* configuring
* launching a tool
* reading operational summaries

### Pages that should use it

* **Home**
* **Integrity Checks**
* **Admin Overview**
* **Admin Library Rules**
* **Admin Integrity Check**
* **Admin System Health**
* **Admin Performance Lab**
* **Admin Reset**

---

## 3. Variant B — Workflow shell

This is for sequential task execution and decision-heavy review.

Use it for:

* Import
* Organize
* Duplicate Review / Review duplicates

This is the most important shell in your product because this is where operator effectiveness lives or dies.

### Structure 2

#### Zone 1: Compact workflow header

Contains only:

* workflow title
* current context or short subtitle
* compact progress/status summary on the right if needed

It must not be a hero banner.

#### Zone 2: Workflow control row

This is a fixed, disciplined control band directly under the header.

Allowed contents:

* step indicator
* current mode/tab
* back/next/group navigation
* primary workflow action
* optional scoped filters relevant to the current workflow only

This row is where workflow control belongs.
Not in the page header.
Not scattered in multiple stacked strips.

#### Zone 3: Primary work surface

This must dominate the page.

Examples:

* current import setup step
* current organize step form
* duplicate comparison workspace

The page should reach this area fast.

#### Zone 4: Secondary evidence / detail

Below the primary work surface, or in a collapsible side panel if truly needed.

Examples:

* technical details
* step guidance
* extra metadata
* audit trail
* additional candidate thumbnails

Core rule:

* supporting detail must not push the primary work surface off the first screen

### Special rule for visual review workflows

For duplicate comparison:

* image comparison is the work surface
* recommendation is support
* review status is support
* technical details are tertiary

That ordering must become structural, not merely stylistic.

### When to use this

Use this shell when the operator is primarily:

* progressing through steps
* making decisions
* reviewing one unit at a time
* executing a guided process

### Pages that should use

* **Import**
* **Organize**
* **Duplicate Review → Review duplicates**

---

## 4. Variant C — Browse/list shell

This is for scanning many items, queues, galleries, lists, or feeds.

Use it for:

* Library
* Duplicate Review → Ready for Bin
* Duplicate Review → Recycle Bin
* Duplicate Review → Playback issues
* Integrity queue/detail area
* Admin Activity
* Admin File History
* System Health feeds/log-style sections

### Structure 3

#### Zone 1: Compact page or section header

Contains:

* title
* concise context
* optional result count or scope summary

Do not put filter state into a big hero.

#### Zone 2: Sticky toolbar row

This is the key feature of this shell.

Contains:

* filters
* sort
* density/view mode
* search
* batch action
* result count
* maybe one primary action

This row should be:

* compact
* sticky where useful
* stable across sibling pages

This is where Library and queue pages are currently drifting badly.

#### Zone 3: Result area

The result area is dominant and starts early.

Possible sub-patterns:

* table/list
* gallery grid
* compact cards
* split list-detail
* focus mode item panel

#### Zone 4: Optional detail panel or bulk footer

Used only if the page needs:

* selected item detail
* batch operation controls
* drill-in preview

### Important density rule

This shell must optimize for scan efficiency. That means:

* compact metadata
* constrained card height
* no oversized explanatory boxes between toolbar and results
* item actions predictable and repeated consistently

### When to use 3

Use this shell when the operator is primarily:

* scanning
* filtering
* selecting
* triaging
* browsing
* restoring/moving items in bulk
* reviewing feeds or history

### Pages that should use it 3

* **Library**
* **Duplicate Review → Ready for Bin**
* **Duplicate Review → Recycle Bin**
* **Duplicate Review → Playback issues**
* **Integrity Checks → queue/detail work area**
* **Admin Activity**
* **Admin File History**
* parts of **Admin System Health**

---

## 5. Hard rules that apply across all variants

These are the real contract. Without these, the variants will collapse into soft opinion.

### Rule 1: No hero banners in operator pages

Large marketing-style headers are banned.

Allowed:

* compact title row
* one-line subtitle
* compact status/action area

Not allowed:

* giant padded header panels that delay the job

---

### Rule 2: One primary control row per page

A page may have:

* one page/workflow toolbar row

Not:

* header CTAs
* another filter row
* another status row
* another action strip
* another mode row
  unless the shell explicitly needs them and they are structurally distinct

Right now too many pages have 3–5 bands before content.

---

### Rule 3: The primary work surface must begin early

On common laptop resolution, the operator should see the start of the real work without needing to scroll through ceremony.

This is especially mandatory for:

* Organize
* Duplicate Review
* Library
* Integrity queue/detail

---

### Rule 4: Supporting content must be demoted

These can exist, but must not dominate above the fold:

* KPI cards
* guidance text
* “what this helps with”
* recommendation explanations
* technical notes
* notices unless critical
* repeated chip/status clusters

---

### Rule 5: Action scope must be visually obvious

Every action must read as one of:

* **page-level**
* **section-level**
* **item-level**

No ambiguity.

Examples:

* page action in toolbar
* section action in section header
* item action inside row/card/detail panel

---

### Rule 6: Cards are not the default layout primitive

Use cards only when they represent:

* a real item
* a real metric
* a real tool block
* a real grouped surface

Do not use cards just to create spacing or containment everywhere.

---

### Rule 7: Long technical content must be contained

Paths, hashes, logs, and payloads must never be allowed to break the layout.

That means shell-level rules for:

* wrapping
* truncation
* internal scroll
* fixed panel boundaries

---

### Rule 8: Tabs are mode selectors, not extra page introductions

If a page has tabs:

* the tab content should begin quickly
* each tab must not repeat a big page intro pattern
* sibling tabs should share the same internal shell where possible

This is especially relevant for:

* Duplicate Review
* Admin

---

## 6. Mapping your current product to the three-shell model

### Standard admin shell

* Home
* Integrity Checks top-level page
* Admin Overview
* Admin Library Rules
* Admin Integrity Check
* Admin System Health
* Admin Performance Lab
* Admin Reset

### Workflow shell

* Import
* Organize
* Duplicate Review → Review duplicates

#### Browse/list shell

* Library
* Duplicate Review → Ready for Bin
* Duplicate Review → Recycle Bin
* Duplicate Review → Playback issues
* Integrity queue/detail region
* Admin Activity
* Admin File History
* System Health feeds and diagnostics lists

---

## 7. What this shell model deliberately avoids

This proposal is deliberately **strict**. It avoids:

* a separate “dashboard shell”
* a separate “settings shell”
* a separate “detail shell”
* a separate “analytics shell”
* a separate “gallery shell”

Why? Because those are mostly content differences, not true shell differences.

If you allow too many shell names, the team will rationalize inconsistency instead of fixing it.

---

## 8. The blunt recommendation

If I had to reduce this to one sentence:

**Build one compact admin page frame, then allow only three page modes: standard admin, workflow, and browse/list.**

That is enough structure to clean this product up without creating a design system fantasy.

