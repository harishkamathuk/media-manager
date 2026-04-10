# Original audit request

## What we should do

As you send screenshots, I will turn them into a compact audit with this structure:

| Page | Shell pattern | Header type | Actions location | Main drift | Severity | Recommended target shell |
| ---- | ------------- | ----------- | ---------------- | ---------- | -------- | ------------------------ |

And then I will roll that up into:

1. recurring drift across the product
2. a **canonical shell contract** with only **2–3 variants max**
3. implementation order for **#8 → #9 → #10**
4. a **tight Codex prompt for #8** based on actual evidence, not guesswork

## What I will look for in each screenshot

I will ignore visual taste and focus on operator-product fundamentals:

### 1. Shell pattern

The real page frame, not styling:

* full-width dashboard shell
* centered content shell
* split panel shell
* detail/review shell
* list + filters shell

### 2. Header type

Whether the header is:

* oversized editorial header
* compact admin title row
* title + metadata row
* title + embedded actions
* duplicated header/nav block

### 3. Actions location

Whether actions are:

* in page header
* floating above content
* repeated in cards and header
* buried below the fold
* split between top right / inline / footer

### 4. Main drift

The single biggest structural problem:

* page starts too “tall”
* action hierarchy unclear
* content too fragmented into cards
* page shell changes between sibling pages
* inconsistent width/alignment
* summary blocks pushing the job below the fold
* duplicated navigation or duplicated controls

### 5. Severity

I will rate it bluntly:

* **High** = harms task flow
* **Medium** = causes friction/confusion
* **Low** = noticeable inconsistency but not blocking

### 6. Recommended target shell

I will map each page to one canonical shell, not invent a special case.

---

## Likely drift themes we are trying to confirm

Based on what you have already said about Media Manager, I would expect these to show up repeatedly:

### A. Marketing-style headers in an operator tool

Too much top-of-page ceremony.
An admin product should get to the job quickly.

### B. CTAs embedded in headers

This usually creates layout drift because every page improvises differently.

### C. Action placement is inconsistent

Some actions in header, some inside cards, some below fold.
That is death for operator muscle memory.

### D. Page rhythm is inconsistent

Different spacing, different max widths, different title-to-content gaps, different card stacking rules.

### E. Cards are being used as layout crutches

Instead of one strong workflow frame, the page gets broken into too many boxes.

### F. Supporting information competes with the main task

Status chips, counts, summaries, help text, metadata all fighting for priority.

If the screenshots confirm that, then #8, #9, and #10 are the right foundation issues.

---

## My strong recommendation on shell variants

Do **not** create lots of shells. That is how teams end up with “reusable inconsistency.”

You probably want **3 variants at most**:

### Variant 1 — Standard admin page

Use for dashboards, settings, list pages, inspection pages.

Structure:

* compact page header
* optional metadata/subtitle row
* optional action bar directly under header
* main content area with consistent width and spacing

This should be the default for most pages.

### Variant 2 — Workflow/review page

Use for duplicate review, queue triage, integrity review, anything sequential and decision-heavy.

Structure:

* very compact title row
* persistent workflow action area in a fixed predictable place
* dominant primary work surface
* secondary technical/context panels below or aside

This is for “do the job now” screens.

### Variant 3 — Dense data/list page

Use for tables, queues, search, history, logs.

Structure:

* compact header
* sticky filters/toolbar zone
* results/list/table as the dominant body
* row-level actions standardized

This is basically a specialization of Variant 1, not a totally different philosophy.

That is enough. Anything beyond this is probably indulgence.

---

## Recommended implementation order

This should be the order unless the screenshots prove otherwise:

### First: #8 Define compact admin-oriented page shell and layout system

Because this sets:

* page width rules
* header structure
* content start position
* spacing tokens/rhythm
* where action zones can exist
* which shell variants are allowed

Without this, #9 and #10 become scattered cleanup.

### Second: #9 Remove CTAs from page headers and standardize action placement

Once shell zones exist, move actions into the correct zones:

* page-level actions
* workflow actions
* row/item actions
* secondary utilities

This is about control placement discipline.

### Third: #10 Standardize spacing, page rhythm, and cross-page alignment

Do this after shell and action placement are fixed, otherwise you will be polishing unstable layouts.

So in plain English:

**Structure first, actions second, spacing cleanup third.**

That is the right sequence.

---

## What I need from you

Send the screenshots of the main pages. Ideally include:

* dashboard/home
* duplicates review
* recycle bin
* playback/integrity issues
* admin/settings
* any dense list/table page
* any detail page that feels messy

Once you send them, I will give you:

1. the page inventory table
2. recurring drift summary
3. shell contract with 2–3 variants
4. implementation order with rationale
5. a tight Codex prompt for **#8** only

One practical note: send the pages as they really are, not the “best looking” ones. The ugly pages are where the truth is.
