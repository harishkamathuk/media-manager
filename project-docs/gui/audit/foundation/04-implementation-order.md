# Recommended implementation order

## 1. Do **#8 first**

**#8 Define compact admin-oriented page shell and layout system**

This must go first because it sets the **contract** the other two issues depend on.

Without #8:

* #9 becomes random CTA cleanup without agreed action zones
* #10 becomes spacing polish on top of unstable structure
* every page fix will drift into local improvisation again

## What #8 should establish

#8 should **not** try to redesign every page.
It should define the reusable structural rules:

* the **base page container**
* the **three allowed shell variants**

  * standard admin
  * workflow
  * browse/list
* the allowed page anatomy:

  * header
  * optional controls row
  * primary work area
  * optional secondary/supporting area
* rules for:

  * max width / full width behavior
  * vertical rhythm between zones
  * where tabs sit
  * where toolbars sit
  * what counts as primary work area
  * what is banned from headers

## Pages to use as proof points in #8

Do not try to convert the whole app under #8.
Use a **small representative slice** to prove the shell system:

* **Home** → standard admin shell
* **Organize** or **Import** → workflow shell
* **Library** → browse/list shell

That is enough to prove the system without opening the floodgates.

## Why this is first

Because #8 is the **structural governor** for the milestone.
If you do not lock this first, the later issues will keep leaking.

---

## 2. Do **#9 second**

**#9 Remove CTAs from page headers and standardize action placement**

This should happen only after #8 defines the legal action zones.

Once #8 is in place, #9 becomes much cleaner:

* remove header-embedded CTAs
* move page actions into the controls row
* separate page-level, section-level, and item-level actions
* standardize where batch actions live
* standardize where workflow actions live

## What #9 should cover

This issue should be about **action hierarchy and placement only**.

It should answer:

* what actions belong in the page controls row
* what actions belong in section headers
* what actions belong inside rows/cards/detail panes
* which actions should never live in the page header

It should **not** become:

* shell redesign
* spacing cleanup
* card density cleanup
* content model rewrite

## Best pages to validate #9

This issue should be validated on the pages with the worst control sprawl:

* **Import**
* **Duplicate Review – Review duplicates**
* **Integrity Checks**
* maybe **Admin Activity**

## Why this is second

Because once you know the shell anatomy, action placement becomes a straightforward discipline problem.

Before that, it is guesswork.

---

## 3. Do **#10 third**

**#10 Standardize spacing, page rhythm, and cross-page alignment**

This comes last because spacing should follow structure, not invent it.

If you do #10 too early, you end up “making inconsistent things evenly spaced,” which is wasted effort.

## What #10 should cover

Once #8 and #9 are done, #10 becomes a proper cleanup/consolidation issue:

* vertical spacing between page zones
* internal spacing in headers/toolbars/sections
* consistent alignment lines
* title-to-toolbar spacing
* toolbar-to-results spacing
* section-to-section rhythm
* grid/card spacing normalization
* responsive sanity across common laptop widths

## What #10 should not cover

It should not reopen:

* which shell a page uses
* where actions belong
* whether a hero exists
* whether a tab layout is valid

Those decisions should already be settled.

## Best pages to validate #10

Use pages where rhythm inconsistency is most visible:

* **Home**
* **Library**
* **Integrity Checks**
* **Admin Overview**
* **Duplicate Review – Ready for Bin / Recycle Bin**

## Why this is third

Because this is the **normalization pass**, not the design-definition pass.

---

# The sequence in one line

## **#8 structure → #9 actions → #10 rhythm**

That is the right order.

Anything else is backwards.

---

# What each issue is really for

To stop scope bleed, here is the clean interpretation of the issues you already have.

## #8 = shell contract

Defines:

* allowed page shell variants
* page anatomy
* structural layout primitives
* banned header patterns

Does **not** solve every page.

---

## #9 = action placement contract

Defines:

* page vs section vs item action zones
* no CTAs in headers
* workflow/batch action placement rules

Does **not** do spacing cleanup.

---

## #10 = rhythm and alignment contract

Defines:

* consistent spacing tokens/usage
* alignment rules
* cross-page page-start rhythm
* card/list spacing normalization

Does **not** redesign shells or action scope.

---

# What I would not do

I would **not**:

* create more foundation issues right now
* split these into six more “AI neatness” issues
* try to fix Duplicate Review first in isolation before #8
* let #8 become a whole-app rewrite
* let #9 become a component cleanup bucket
* let #10 become a vague “make it consistent” issue

That would just recreate the same problem in a different shape.

---

# Practical execution recommendation

## Issue order

1. **#8** — define and prove the shell system with 2–3 representative pages
2. **#9** — move and standardize actions using the #8 shell zones
3. **#10** — normalize spacing/rhythm once the first two are stable

## Proof pages for each

* **#8:** Home, Organize/Import, Library
* **#9:** Duplicate Review review flow, Import, Integrity Checks
* **#10:** Home, Library, Integrity, Admin Overview, Duplicate Review queue pages

That gives you evidence without turning each issue into a monster.

---

# Blunt close

Your instinct is correct: the original issue slicing was premature.

But the fix is **not** to throw the issues away.
The fix is to **reinterpret them properly** and force them into a disciplined order:

* **#8 sets the rules**
* **#9 applies action discipline**
* **#10 cleans and normalizes**

