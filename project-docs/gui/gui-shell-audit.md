# GUI Audi 

Below is the **first-pass page inventory only**, based on the screenshots you provided.

I have treated sibling tabs/views separately where the shell meaningfully changes.

## Page inventory

| Page                                                                         | Shell pattern                               | Header type                                                  | Actions location                                                                                   | Main drift                                                                                                                                                      | Severity       | Recommended target shell |
| ---------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------ |
| **Home**                                                                     | Dashboard / overview shell with right rail  | Large hero header + secondary side summary rail              | Right rail quick links, inline section links                                                       | Split attention between hero, right rail, stats, recent media, and needs-attention boxes; too much top-of-page ceremony for an operator landing page            | **Medium**     | **Standard admin shell** |
| **Import**                                                                   | Workflow launcher shell                     | Large hero header with embedded primary actions              | Primary CTAs inside hero; secondary controls in content blocks below                               | Header is doing too much work; page mixes landing-page intro, live status, and step setup without a single dominant work surface                                | **Medium**     | **Workflow shell**       |
| **Organize**                                                                 | Guided workflow shell                       | Large hero header + separate progress card                   | Abort and step navigation in progress area; form actions inline                                    | Too much vertical preamble before actual step workspace; progress, intro, and step content stack into a tall start                                              | **High**       | **Workflow shell**       |
| **Library**                                                                  | Browse / gallery shell                      | Large hero header carrying state metadata                    | Filters in toolbar below header; sort/density controls top right of toolbar; item actions on cards | Header contains state that belongs in the toolbar; browsing controls and content start too far down; grid feels detached from page frame                        | **High**       | **Browse/list shell**    |
| **Duplicate Review – Review duplicates (top view)**                          | Multi-mode review shell                     | Large hero header + tab strip + subheader                    | Filter chips on right, navigation toggle on left, review actions lower in content                  | Too many stacked control bands before the actual review target; recommendation/review/filter/navigation all compete                                             | **High**       | **Workflow shell**       |
| **Duplicate Review – Review duplicates (comparison area)**                   | Side-by-side decision workspace             | No new real header, content starts after several prior bands | Review action buttons below comparison; comparison selection lower still                           | Actual job is pushed below fold; comparison surface not visible as a complete unit; decision controls are separated from first meaningful visual evidence       | **High**       | **Workflow shell**       |
| **Duplicate Review – Review duplicates (lower comparison / technical area)** | Detail extension under comparison workspace | No distinct local header hierarchy                           | Thumbnail selection mid-page; technical details below                                              | Useful supporting detail occupies prime vertical space and extends the task too deep; weak distinction between core review surface and secondary detail         | **High**       | **Workflow shell**       |
| **Duplicate Review – Ready for Bin (overview top)**                          | Queue / batch action shell                  | Large hero header + tab strip + summary cards                | View toggles upper right; bulk action inside content area                                          | Yet another tall preamble before actual groups; summary cards and notices dilute the primary action of reviewing or moving eligible groups                      | **High**       | **Browse/list shell**    |
| **Duplicate Review – Ready for Bin (group cards)**                           | Card-based batch queue                      | Local section label only                                     | Per-card move action; selection/focus controls in cards                                            | Cards are information-heavy and bulky; too little scan efficiency; preferred/extra copy comparison consumes too much space for a list workflow                  | **High**       | **Browse/list shell**    |
| **Duplicate Review – Recycle Bin (overview top)**                            | Queue / lifecycle list shell                | Large hero header + tab strip + summary cards                | View toggles top right; restore actions within cards below                                         | Same structural bloat as Ready for Bin; lifecycle metrics and notices crowd out item browsing                                                                   | **High**       | **Browse/list shell**    |
| **Duplicate Review – Recycle Bin (gallery/card view)**                       | Gallery-card restore queue                  | No strong local header once cards begin                      | Restore button per card; paging above                                                              | Restore browsing is card-heavy and vertically wasteful; difficult to compare many entries quickly; metadata consumes too much visible area                      | **High**       | **Browse/list shell**    |
| **Duplicate Review – Playback issues**                                       | Sub-tab status/list shell                   | Large hero header + tab strip + local section header         | Back/open actions right side of section                                                            | Structurally overbuilt for sparse content; too many wrappers for a simple exception view                                                                        | **Medium**     | **Browse/list shell**    |
| **Integrity Checks – Overview/status**                                       | Monitoring dashboard shell                  | Large hero header with scan controls embedded                | Quick/Deep scan in hero; status below; queue lower                                                 | Hero is oversized for an operational scan screen; controls, status, KPIs, and queue all start too low                                                           | **High**       | **Standard admin shell** |
| **Integrity Checks – Queue/detail split view**                               | Split master-detail shell                   | Local section headers only once inside lower page            | Queue filters over list; row actions/detail actions in right panel                                 | Reasonable underlying pattern, but buried too far down and broken by width overflow/text bleed; shell does not protect the working area                         | **High**       | **Browse/list shell**    |
| **Admin – Overview (top)**                                                   | Workspace landing shell                     | Large hero header with pathway cards + tab strip             | Cards in hero area; tabs below                                                                     | Hero repeats navigation and explanation that the tabs already represent; page starts like a brochure instead of an admin console                                | **High**       | **Standard admin shell** |
| **Admin – Overview (content)**                                               | Admin dashboard / launchpad                 | Local explanatory block + stat cards + action cards          | Cards act as navigation/actions                                                                    | Better than the top section, but still card-heavy and vertically loose; too much explanatory framing before utility                                             | **Medium**     | **Standard admin shell** |
| **Admin – Activity**                                                         | Split list-detail admin shell               | Local explanatory header inside tab                          | Table/list on left; selected job panel on right                                                    | One of the stronger underlying patterns, but still burdened by explanatory blocks and tall KPI band above the work area                                         | **Medium**     | **Browse/list shell**    |
| **Admin – Library Rules**                                                    | Settings / policy shell                     | Local explanatory header + KPI cards                         | Rule selection in body; settings expressed as large tiles                                          | Tiles are too large and consume too much space for settings state; summary card band dominates over actual rule editing/selection                               | **Medium**     | **Standard admin shell** |
| **Admin – File History**                                                     | Lookup / split interaction shell            | Local explanatory header + KPI cards                         | Search-mode tiles in body; selected file panel on right                                            | Discovery choices are presented as oversized cards; too much top-of-page explanation before lookup begins                                                       | **Medium**     | **Browse/list shell**    |
| **Admin – Integrity Check**                                                  | Tool/action shell                           | Local explanatory header + KPI cards                         | Run action at form row end                                                                         | Better focused than some others, but still starts too low due to repeated explanatory and KPI sections                                                          | **Medium**     | **Standard admin shell** |
| **Admin – System Health (top)**                                              | Monitoring dashboard shell                  | Local explanatory header + KPI cards                         | Reconcile action inside large content card                                                         | Feels like stacked dashboards inside a dashboard; action block and charts compete without a clear primary reading path                                          | **Medium**     | **Standard admin shell** |
| **Admin – System Health (signals / monitoring)**                             | Two-column diagnostics shell                | No strong local hierarchy after scroll                       | Prometheus/Grafana actions embedded in panel                                                       | Dense technical data is readable enough, but panel framing is bulky and wastes horizontal space; lists feel boxed rather than structured                        | **Medium**     | **Browse/list shell**    |
| **Admin – System Health (operation feed)**                                   | Feed/list shell                             | Simple section header                                        | Status badges row-aligned in list                                                                  | This underlying pattern is fairly sound; biggest problem is that it lives too deep under earlier page chrome                                                    | **Low–Medium** | **Browse/list shell**    |
| **Admin – Performance Lab**                                                  | Tool form + queue/detail shell              | Local explanatory header                                     | Benchmark actions inline within forms                                                              | Not terrible structurally, but still inflated by repeated explanatory banding and large cards; tool forms should start sooner                                   | **Medium**     | **Standard admin shell** |
| **Admin – Reset**                                                            | Destructive action shell                    | Local explanatory header                                     | Preview/execute actions inside danger panel                                                        | Clearer than many pages, but still padded by repeated header/tabs/explanation before the danger zone; destructive workspace should be more direct and contained | **Medium**     | **Standard admin shell** |

---

## Quick read of the inventory

Even without the cross-page synthesis yet, the table already shows three blunt truths:

### 1. The dominant drift is **top-of-page inflation**

Too many pages spend vertical space on:

* oversized hero headers
* repeated explanations
* duplicated navigation layers
* summary/KPI bands before the real task

### 2. Your strongest candidate shells are already visible

You do not have twenty patterns. You really have about three:

* **standard admin shell**
* **workflow shell**
* **browse/list shell**

That is good news. The product is messy, but not structurally hopeless.

### 3. The worst offenders are the pages where the job is visual or sequential

The highest-severity drift is in:

* **Organize**
* **Library**
* **Duplicate Review**
* **Integrity Checks**

That is not accidental. These are pages where the operator needs the work surface early, and the current layout keeps delaying it.

## Recurring layout drift across the product

Below is the **cross-page drift only**. No shell contract yet, no implementation plan yet.

---

### 1. Top-of-page inflation is the core structural problem

This is the biggest recurring issue across the product.

Most pages spend too much vertical space before the operator reaches the real work surface. That inflation usually comes from some combination of:

* large hero headers
* explanatory intro copy
* tab strips
* KPI or summary cards
* notices/banners
* secondary control bars

The result is predictable:

* the real task starts below the fold
* the page feels slower than it is
* operators must scroll before they can even orient themselves to the job

This is visible on:

* **Home**
* **Import**
* **Organize**
* **Library**
* **Duplicate Review** almost everywhere
* **Integrity Checks**
* most **Admin** tabs

This is not just “a bit roomy.” It is a systemic shell problem.

---

### 2. Headers are trying to do too many jobs

Across the product, the page header often acts as all of these at once:

* title
* mission statement
* status summary
* workflow explanation
* CTA container
* navigation preface
* state display

That is bad discipline for an operator UI.

A header should usually do only a small number of things:

* identify the page
* optionally show compact context/state
* optionally expose page-level actions

Instead, many pages use the header as a landing-page billboard. That is why the product often reads like a guided brochure rather than a working console.

Strong examples:

* **Home**
* **Import**
* **Library**
* **Duplicate Review**
* **Integrity Checks**
* **Admin workspace**

---

### 3. Control placement is inconsistent and fragmented

The product does not yet have a stable action hierarchy.

Controls appear in too many different places:

* inside hero headers
* in subheaders below tabs
* on the left of one control row and the right of another
* inside cards
* at the bottom of a comparison section
* embedded in local detail panes

That causes two problems:

* operators cannot build muscle memory
* the page feels noisier because the eye has to keep hunting for the “real” action point

Recurring examples:

* **Import**: CTAs in header, live state below, setup lower down
* **Duplicate Review**: filters, group navigation, human review actions, movement actions, selection actions all separated
* **Integrity Checks**: scan actions in hero, queue filters lower, detail actions in panel
* **Admin**: tab-level actions vary widely from section to section

This drift is exactly why issue **#9** exists, but the root cause starts in the shell.

---

### 4. Workflow pages are not giving priority to the work surface

Your most important operator workflows are:

* Organize
* Duplicate Review
* Integrity Checks
* parts of Admin Activity / File History

These pages should foreground the **primary working surface**:

* the current step
* the current comparison
* the queue and selected item
* the input form and current output

Instead, many pages foreground surrounding explanation and supporting state first.

The clearest failure is **Duplicate Review**:

* the recommendation, tabs, filters, review state, notices, and group navigation all appear before the visual comparison really takes hold
* the image comparison itself does not dominate the page strongly enough
* supporting metadata is consuming premium space that should belong to visual judgement

That same pattern appears in **Organize**:

* intro + progress + workspace staging pushes the actual step surface down

And in **Integrity Checks**:

* scan hero + summary + KPI band delay the actual queue/detail workspace

This is not cosmetic drift. It directly harms task completion.

---

### 5. Supporting information is routinely over-promoted

The product often gives too much visual weight to information that is real but secondary.

Recurring examples:

* summary stats
* helper copy
* workflow reminders
* chip badges
* section framing cards
* state labels
* “what this helps with / when to use it / try questions like” blocks

These things are not useless. The problem is **rank**.

They often appear:

* too high on the page
* too large
* too boxed-off
* too repeated across sibling screens

This is especially visible in:

* **Admin**
* **Duplicate Review**
* **Integrity Checks**
* **Library** header state chips

The product keeps explaining itself instead of getting on with the job.

---

### 6. The UI overuses cards as layout scaffolding

Cards are being used for too many roles:

* grouping
* navigation
* summaries
* workflow framing
* item display
* tool launchers
* detail containers
* state containers

When everything becomes a bordered rounded rectangle, hierarchy weakens. The screen turns into a pile of compartments rather than a controlled workspace.

You can see this on:

* **Home**
* **Admin Overview**
* **Ready for Bin**
* **Recycle Bin**
* **System Health**
* **Library Rules**
* **File History**
* **Performance Lab**

This creates two specific forms of drift:

* **visual fragmentation**
* **wasted padding**

The product often feels boxed rather than structured.

---

### 7. Browse/list workflows are not optimized for scan efficiency

Several pages are fundamentally browse, queue, or list workflows, but they are rendered with too much per-item ceremony.

Examples:

* **Ready for Bin**
* **Recycle Bin**
* **Integrity Queue**
* **Admin Activity**
* parts of **Library**

The core issue is that these pages often prefer:

* large cards
* oversized item blocks
* repeated labels
* verbose per-item metadata
* large side-by-side visual containers

when the task really needs:

* fast scanning
* clear sort/filter model
* compact row/card density
* obvious primary action per item
* tighter alignment

This is why some pages feel much heavier than the underlying task actually is.

---

### 8. There is weak separation between page-level, section-level, and item-level controls

A mature admin UI usually distinguishes:

* **page-level** controls: global to the screen
* **section-level** controls: affect one region
* **item-level** controls: affect a row/card/group/file

Your current layouts often blur these boundaries.

Examples:

* duplicate review state chips vs group navigation vs review decisions
* recycle-bin mode toggles vs item restore actions
* integrity scan controls vs queue filters vs file actions
* admin tab navigation vs in-panel tool actions

This causes accidental competition:

* page-level actions look like section utilities
* item-level actions float like page controls
* operators cannot quickly infer “what scope does this affect?”

That is a shell and rhythm problem, not just a component problem.

---

### 9. Repeated explanatory blocks create cross-page sameness without real consistency

A lot of pages use a repeated pattern like:

* what this helps with
* when to use it
* try questions like

On paper that sounds consistent. In practice it is over-applied.

Why this drifts:

* it makes many pages start with the same educational overhead
* it consumes prime space even on pages used repeatedly by the same operator
* it gives a false sense of consistency while the actual work areas remain inconsistent

This is especially visible across the **Admin** tabs.

So the product has consistency in the wrong layer:

* **same explanation framing**
* **different real workspace structures**

That is backwards.

---

### 10. Tabbed pages often duplicate hierarchy instead of simplifying it

Tabs are supposed to reduce complexity by segmenting modes.

But on several pages, the tab system sits underneath:

* a hero header
* a secondary explanatory section
* local title/subtitle
* summary cards

So the tabs do not reduce hierarchy. They add another layer to it.

Most visible in:

* **Duplicate Review**
* **Admin**

This is why those pages feel stacked rather than composed.

---

### 11. Visual workflows are not behaving like visual workflows

Where the operator must judge media or compare files, the page should privilege:

* image visibility
* comparison clarity
* immediate context
* decisive action placement

Instead, the product frequently privileges:

* metadata
* status wrappers
* labels
* banners
* descriptive framing
* secondary chips

That is the wrong tradeoff.

This is the sharpest UX drift in:

* **Duplicate Review**
* parts of **Library**
* indirectly **Integrity Checks** when file detail overflows and reduces readable workspace

In plain English: on the screens where the images should win, the chrome wins.

---

### 12. Dense technical content is not being constrained well enough

On technical/admin pages, long paths, logs, IDs, and error payloads are allowed to dictate layout too often.

This produces:

* horizontal overflow
* broken alignment
* panels that feel stretched by content
* a rough, uncontained working surface

You pointed this out correctly in **Integrity Checks** and it also appears in some **Admin** detail/log views.

That means the current layout system is not imposing enough discipline on:

* overflow handling
* text wrapping/truncation
* fixed versus flexible panel behavior
* scroll ownership

That is a structural issue, not just “bad sample data.”

---

## The recurring drift, reduced to a blunt list

If I compress the whole audit into the fewest possible truths, they are these:

### Primary drift

* **Too much page starts before the page actually starts**

### Structural drift

* headers are oversized and overloaded
* control placement is inconsistent
* page hierarchy has too many stacked bands
* cards are overused as layout containers
* supporting information is over-promoted

### Workflow drift

* work surfaces start too low
* browse/queue views are not dense enough
* visual review screens do not prioritize the visuals
* page/section/item action scopes are blurred

### Technical drift

* long technical content is not properly contained
* repeated “help” framing crowds operational use

---

## What this means before any solutioning

The product does **not** mainly suffer from color, typography, or isolated messy pages.

It suffers from a **layout contract problem**:

* no strict shell discipline
* no stable action zones
* no strong rules for when summary/info bands are allowed
* no consistent threshold for when a page should become a workflow surface versus a dashboard surface

That is why starting with **#8 page shell/layout system** is correct.

Next step should be **step 3 only: propose a canonical page shell with no more than 2–3 variants**.

## Recurring layout drift across the product

Below is the **cross-page drift only**. No shell contract yet, no implementation plan yet.

---

### 1. Top-of-page inflation is the core structural problem

This is the biggest recurring issue across the product.

Most pages spend too much vertical space before the operator reaches the real work surface. That inflation usually comes from some combination of:

* large hero headers
* explanatory intro copy
* tab strips
* KPI or summary cards
* notices/banners
* secondary control bars

The result is predictable:

* the real task starts below the fold
* the page feels slower than it is
* operators must scroll before they can even orient themselves to the job

This is visible on:

* **Home**
* **Import**
* **Organize**
* **Library**
* **Duplicate Review** almost everywhere
* **Integrity Checks**
* most **Admin** tabs

This is not just “a bit roomy.” It is a systemic shell problem.

---

### 2. Headers are trying to do too many jobs

Across the product, the page header often acts as all of these at once:

* title
* mission statement
* status summary
* workflow explanation
* CTA container
* navigation preface
* state display

That is bad discipline for an operator UI.

A header should usually do only a small number of things:

* identify the page
* optionally show compact context/state
* optionally expose page-level actions

Instead, many pages use the header as a landing-page billboard. That is why the product often reads like a guided brochure rather than a working console.

Strong examples:

* **Home**
* **Import**
* **Library**
* **Duplicate Review**
* **Integrity Checks**
* **Admin workspace**

---

### 3. Control placement is inconsistent and fragmented

The product does not yet have a stable action hierarchy.

Controls appear in too many different places:

* inside hero headers
* in subheaders below tabs
* on the left of one control row and the right of another
* inside cards
* at the bottom of a comparison section
* embedded in local detail panes

That causes two problems:

* operators cannot build muscle memory
* the page feels noisier because the eye has to keep hunting for the “real” action point

Recurring examples:

* **Import**: CTAs in header, live state below, setup lower down
* **Duplicate Review**: filters, group navigation, human review actions, movement actions, selection actions all separated
* **Integrity Checks**: scan actions in hero, queue filters lower, detail actions in panel
* **Admin**: tab-level actions vary widely from section to section

This drift is exactly why issue **#9** exists, but the root cause starts in the shell.

---

### 4. Workflow pages are not giving priority to the work surface

Your most important operator workflows are:

* Organize
* Duplicate Review
* Integrity Checks
* parts of Admin Activity / File History

These pages should foreground the **primary working surface**:

* the current step
* the current comparison
* the queue and selected item
* the input form and current output

Instead, many pages foreground surrounding explanation and supporting state first.

The clearest failure is **Duplicate Review**:

* the recommendation, tabs, filters, review state, notices, and group navigation all appear before the visual comparison really takes hold
* the image comparison itself does not dominate the page strongly enough
* supporting metadata is consuming premium space that should belong to visual judgement

That same pattern appears in **Organize**:

* intro + progress + workspace staging pushes the actual step surface down

And in **Integrity Checks**:

* scan hero + summary + KPI band delay the actual queue/detail workspace

This is not cosmetic drift. It directly harms task completion.

---

### 5. Supporting information is routinely over-promoted

The product often gives too much visual weight to information that is real but secondary.

Recurring examples:

* summary stats
* helper copy
* workflow reminders
* chip badges
* section framing cards
* state labels
* “what this helps with / when to use it / try questions like” blocks

These things are not useless. The problem is **rank**.

They often appear:

* too high on the page
* too large
* too boxed-off
* too repeated across sibling screens

This is especially visible in:

* **Admin**
* **Duplicate Review**
* **Integrity Checks**
* **Library** header state chips

The product keeps explaining itself instead of getting on with the job.

---

### 6. The UI overuses cards as layout scaffolding

Cards are being used for too many roles:

* grouping
* navigation
* summaries
* workflow framing
* item display
* tool launchers
* detail containers
* state containers

When everything becomes a bordered rounded rectangle, hierarchy weakens. The screen turns into a pile of compartments rather than a controlled workspace.

You can see this on:

* **Home**
* **Admin Overview**
* **Ready for Bin**
* **Recycle Bin**
* **System Health**
* **Library Rules**
* **File History**
* **Performance Lab**

This creates two specific forms of drift:

* **visual fragmentation**
* **wasted padding**

The product often feels boxed rather than structured.

---

### 7. Browse/list workflows are not optimized for scan efficiency

Several pages are fundamentally browse, queue, or list workflows, but they are rendered with too much per-item ceremony.

Examples:

* **Ready for Bin**
* **Recycle Bin**
* **Integrity Queue**
* **Admin Activity**
* parts of **Library**

The core issue is that these pages often prefer:

* large cards
* oversized item blocks
* repeated labels
* verbose per-item metadata
* large side-by-side visual containers

when the task really needs:

* fast scanning
* clear sort/filter model
* compact row/card density
* obvious primary action per item
* tighter alignment

This is why some pages feel much heavier than the underlying task actually is.

---

### 8. There is weak separation between page-level, section-level, and item-level controls

A mature admin UI usually distinguishes:

* **page-level** controls: global to the screen
* **section-level** controls: affect one region
* **item-level** controls: affect a row/card/group/file

Your current layouts often blur these boundaries.

Examples:

* duplicate review state chips vs group navigation vs review decisions
* recycle-bin mode toggles vs item restore actions
* integrity scan controls vs queue filters vs file actions
* admin tab navigation vs in-panel tool actions

This causes accidental competition:

* page-level actions look like section utilities
* item-level actions float like page controls
* operators cannot quickly infer “what scope does this affect?”

That is a shell and rhythm problem, not just a component problem.

---

### 9. Repeated explanatory blocks create cross-page sameness without real consistency

A lot of pages use a repeated pattern like:

* what this helps with
* when to use it
* try questions like

On paper that sounds consistent. In practice it is over-applied.

Why this drifts:

* it makes many pages start with the same educational overhead
* it consumes prime space even on pages used repeatedly by the same operator
* it gives a false sense of consistency while the actual work areas remain inconsistent

This is especially visible across the **Admin** tabs.

So the product has consistency in the wrong layer:

* **same explanation framing**
* **different real workspace structures**

That is backwards.

---

### 10. Tabbed pages often duplicate hierarchy instead of simplifying it

Tabs are supposed to reduce complexity by segmenting modes.

But on several pages, the tab system sits underneath:

* a hero header
* a secondary explanatory section
* local title/subtitle
* summary cards

So the tabs do not reduce hierarchy. They add another layer to it.

Most visible in:

* **Duplicate Review**
* **Admin**

This is why those pages feel stacked rather than composed.

---

### 11. Visual workflows are not behaving like visual workflows

Where the operator must judge media or compare files, the page should privilege:

* image visibility
* comparison clarity
* immediate context
* decisive action placement

Instead, the product frequently privileges:

* metadata
* status wrappers
* labels
* banners
* descriptive framing
* secondary chips

That is the wrong tradeoff.

This is the sharpest UX drift in:

* **Duplicate Review**
* parts of **Library**
* indirectly **Integrity Checks** when file detail overflows and reduces readable workspace

In plain English: on the screens where the images should win, the chrome wins.

---

### 12. Dense technical content is not being constrained well enough

On technical/admin pages, long paths, logs, IDs, and error payloads are allowed to dictate layout too often.

This produces:

* horizontal overflow
* broken alignment
* panels that feel stretched by content
* a rough, uncontained working surface

You pointed this out correctly in **Integrity Checks** and it also appears in some **Admin** detail/log views.

That means the current layout system is not imposing enough discipline on:

* overflow handling
* text wrapping/truncation
* fixed versus flexible panel behavior
* scroll ownership

That is a structural issue, not just “bad sample data.”

---

## The recurring drift, reduced to a blunt list

If I compress the whole audit into the fewest possible truths, they are these:

### Primary drift

* **Too much page starts before the page actually starts**

### Structural drift

* headers are oversized and overloaded
* control placement is inconsistent
* page hierarchy has too many stacked bands
* cards are overused as layout containers
* supporting information is over-promoted

### Workflow drift

* work surfaces start too low
* browse/queue views are not dense enough
* visual review screens do not prioritize the visuals
* page/section/item action scopes are blurred

### Technical drift

* long technical content is not properly contained
* repeated “help” framing crowds operational use

---

## What this means before any solutioning

The product does **not** mainly suffer from color, typography, or isolated messy pages.

It suffers from a **layout contract problem**:

* no strict shell discipline
* no stable action zones
* no strong rules for when summary/info bands are allowed
* no consistent threshold for when a page should become a workflow surface versus a dashboard surface

That is why starting with **#8 page shell/layout system** is correct.

Next step should be **step 3 only: propose a canonical page shell with no more than 2–3 variants**.
