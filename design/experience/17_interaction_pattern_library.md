# SHUNYA Canonical Interaction Pattern Library

> **Canonical Reference — Phase X2B**
> This document is the permanent library of reusable interaction patterns. Every future workflow in SHUNYA must be assembled from these patterns rather than invented independently.
>
> The Interaction Language defines the grammar (primitives + composition rules).
> This Pattern Library defines the reusable sentences built from that grammar.

---

## Preamble: Sentences from Grammar

The Interaction Language provides 21 primitives and 27 component primitives — the atomic units of interaction.

This Pattern Library composes those primitives into reusable patterns — the common interaction sequences that appear across every SHUNYA workflow.

A frontend engineer should be able to construct any SHUNYA workflow using only:
1. Human Principles
2. Presence Canon
3. Experience Canon
4. Interaction Language
5. Design System Foundation
6. **This Pattern Library**

No new interaction behaviour should ever be invented at the application level.

---

## 1. Pattern Definition Standard

### 1.1 Pattern Template

Every pattern in this library follows this template:

```yaml
Name: [Canonical pattern name]
Purpose: [Single sentence describing what this pattern accomplishes]
ApplicableSituations: [When to use this pattern]
RequiredPrimitives: [List of interaction primitives from the Interaction Language]
CompositionSequence: [Ordered steps showing how primitives combine]
EntryConditions: [What must be true before the pattern can begin]
ExitConditions: [What is true when the pattern completes]
AlternativePaths: [Variations of this pattern for different contexts]
FailurePaths: [What happens when a step fails]
AccessibilityBehaviour: [Keyboard and screen reader expectations]
MotionBehaviour: [Animation expectations during the pattern]
AttentionBehaviour: [How the pattern interacts with attention states]
ConfidenceBehaviour: [How confidence is displayed during the pattern]
ValidCompositionExamples: [One or more concrete compositions from primitives]
InvalidCompositionExamples: [What not to do]
```

### 1.2 Composition Rules

| Rule | Description |
|------|-------------|
| **Patterns compose patterns** | A pattern may call other patterns as sub-steps. |
| **Patterns compose primitives** | A pattern may call primitives directly. |
| **Patterns never bypass primitives** | Every pattern step must trace to one or more interaction primitives. |
| **No cyclic composition** | Pattern A may not depend on Pattern B which depends on Pattern A. |
| **Deterministic execution** | The same inputs always produce the same sequence. |
| **Inheritance** | Patterns inherit accessibility, motion, and attention behaviour from their constituent primitives. Overrides must be documented. |

---

## 2. Discovery Patterns

### 2.1 Search

| Field | Value |
|-------|-------|
| **Purpose** | Find a specific object or set of objects by query |
| **Applicable Situations** | User knows what they are looking for; need to locate it by name, ID, or attribute |
| **Required Primitives** | Focus, Inspect, Navigate, Suggest, Dismiss |
| **Composition Sequence** | 1. Focus (search input) → 2. Type query (Focus persists) → 3. Inspect (preview results) → 4. Select (choose result) → 5. Navigate (open result) OR Dismiss (clear search) |
| **Entry Conditions** | Search input is visible and focusable |
| **Exit Conditions** | User has either navigated to an object or dismissed the search |
| **Alternative Paths** | **AI-assisted search**: Suggest fires with query completions between steps 2-3. **No results**: Empty state shown after step 2. User may Suggest (create new object) or Dismiss. |
| **Failure Paths** | Network error during step 3: Show cached results with offline indicator. User may retry or dismiss. |
| **Accessibility Behaviour** | Search input has `role="searchbox"`. Results are `role="listbox"` with `aria-activedescendant` on focused item. Escape closes. Enter activates selection. |
| **Motion Behaviour** | Results appear/disappear with CrossFade (200ms). No animation on initial input (content appears instantly). |
| **Attention Behaviour** | Search operates in Silent state. No suggestions until user pauses >500ms. |
| **Confidence Behaviour** | AI-assisted completions show confidence bar. Regular search results do not carry confidence. |
| **Valid Composition** | Focus(search) → Type(query) → Inspect(result) → Select(result) → Navigate(object) |
| **Invalid Composition** | Navigate directly to a guess without going through Search. Opening a random object without user selection. |

### 2.2 Browse

| Field | Value |
|-------|-------|
| **Purpose** | Explore available objects in a workspace without a specific target |
| **Applicable Situations** | User wants to see what exists; open-ended exploration |
| **Required Primitives** | Focus, Inspect, Preview, Navigate, Expand, Collapse |
| **Composition Sequence** | 1. Focus (workspace content) → 2. Inspect (scan visible items) → 3. Preview (hover for summary) → 4. Expand (view detail) → 5. Navigate (open) OR Collapse (return to list) |
| **Entry Conditions** | Workspace is displaying a list or grid of objects |
| **Exit Conditions** | User navigates to an object or leaves the workspace |
| **Alternative Paths** | Filtered browse: Insert Filter step before step 2. Sorted browse: Insert Sort step. |
| **Failure Paths** | Empty workspace: Show empty state with Suggest (create first object). |
| **Accessibility Behaviour** | List is `role="list"` with `role="listitem"` children. Arrow keys navigate items. Enter opens. |
| **Motion Behaviour** | Items appear with Stagger (50ms each). Preview expands with CrossFade (200ms). |
| **Attention Behaviour** | Browse operates in Silent state. AI does not suggest during scanning mode. When user pauses >3s on an item, Suggest may fire. |
| **Valid Composition** | Focus(list) → Inspect(item[3]) → Preview(item[3]) → Expand(item[3] detail) → Navigate(item[3]) |
| **Invalid Composition** | Navigating to every item to see what it is. Forcing AI suggestions during rapid scanning. |

### 2.3 Explore

| Field | Value |
|-------|-------|
| **Purpose** | Discover relationships and connections between objects |
| **Applicable Situations** | User wants to understand how objects are connected; relationship mapping |
| **Required Primitives** | Focus, Inspect, Navigate, Suggest, Expand, Collapse |
| **Composition Sequence** | 1. Focus (relationship graph) → 2. Inspect (node) → 3. Expand (show connections) → 4. Inspect (connected node) → 5. Navigate (to connected object) OR Collapse (back to previous) |
| **Entry Conditions** | Relationship graph or relationship panel is visible |
| **Exit Conditions** | User navigates to an object or closes the relationship view |
| **Alternative Paths** | Graph explore: Nodes animate as user pans. Breadcrumb explore: Follow relationship chain through breadcrumbs. |
| **Failure Paths** | No relationships: Empty state with Suggest (link to other objects). |
| **Accessibility Behaviour** | Graph is `role="tree"` with nodes as `role="treeitem"`. Arrow keys navigate graph hierarchy. |
| **Motion Behaviour** | Node selection uses SlideIn (300ms) for detail panel. Graph pans are smooth (scroll-behavior). |
| **Attention Behaviour** | Explore operates in Attentive state. AI may Suggest significant connections when user pauses on a node. |
| **Valid Composition** | Focus(graph) → Inspect(node_A) → Expand(connections) → Inspect(node_B) → Navigate(node_B) |
| **Invalid Composition** | Opening every connected object in a new tab. Ignoring relationship context when navigating. |

### 2.4 Inspect

| Field | Value |
|-------|-------|
| **Purpose** | Temporarily examine an object without committing to navigate |
| **Applicable Situations** | User wants a quick summary before deciding whether to open fully |
| **Required Primitives** | Focus, Inspect, Dismiss, Preview |
| **Composition Sequence** | 1. Focus (item) → 2. Preview (show summary popover) → 3. Inspect (read summary) → 4. Navigate (open) OR Dismiss (move to next item) |
| **Entry Conditions** | An item is focusable and previewable |
| **Exit Conditions** | User navigates to the item or moves focus away |
| **Alternative Paths** | **Long-press inspect**: On touch, long-press triggers Preview instead of hover. |
| **Failure Paths** | Preview takes >2s to load: Show skeleton placeholder, content appears when ready. |
| **Accessibility Behaviour** | Preview has `role="tooltip"` or `role="dialog"` (for rich previews). Escape closes. Tab moves to next focusable. |
| **Motion Behaviour** | Preview appears with Appear (200ms). Disappears with Disappear (150ms). |
| **Attention Behaviour** | Inspect is user-initiated. System remains in current attention state. |
| **Valid Composition** | Focus(card) → Preview(card_summary) → Inspect(summary) → Dismiss (Escape) |
| **Invalid Composition** | Opening every object to see its summary. Making preview the same size as the full object view. |

### 2.5 Preview

| Field | Value |
|-------|-------|
| **Purpose** | Show a miniature or summary version of content without full open |
| **Applicable Situations** | User needs to identify content before committing to view it fully |
| **Required Primitives** | Focus, Preview, Dismiss |
| **Composition Sequence** | 1. Focus (trigger element) → 2. Preview (show miniature) → 3. Dismiss (move away) OR Navigate (open fully) |
| **Entry Conditions** | Trigger element is present and hoverable/focusable |
| **Exit Conditions** | User navigates away from the trigger or preview times out |
| **Alternative Paths** | Thumbnail preview (documents), card preview (objects), snippet preview (knowledge items). |
| **Failure Paths** | Preview content not available: Show placeholder icon + "Preview not available." |
| **Accessibility Behaviour** | Preview region has `aria-label` describing the previewed content. Escape closes. |
| **Motion Behaviour** | Preview appears with Appear (200ms). Disappears with Disappear (150ms) on focus leave. |
| **Attention Behaviour** | Preview is user-initiated. No system attention change. |
| **Valid Composition** | Focus(document_icon) → Preview(document_thumbnail) → Dismiss (mouse leaves) |
| **Invalid Composition** | Preview blocking the content behind it. Preview animating on every hover without delay. |

### 2.6 Compare

| Field | Value |
|-------|-------|
| **Purpose** | Place two or more items side by side for evaluation |
| **Applicable Situations** | User needs to choose between options, understand differences, or evaluate trade-offs |
| **Required Primitives** | Select, Compare, Uncompare, Focus, Inspect, Dismiss |
| **Composition Sequence** | 1. Select (item A) → 2. Select (item B) → 3. Compare (side-by-side view) → 4. Inspect (differences) → 5. Focus (preferred item) → 6. Navigate (to preferred) OR Dismiss (cancel compare) |
| **Entry Conditions** | At least two selectable items exist in the current view |
| **Exit Conditions** | User selects an item to act on or cancels the comparison |
| **Alternative Paths** | **Multi-compare**: Select 3+ items → Compare in table view. **Timeline compare**: Compare versions of the same object at different times. |
| **Failure Paths** | Items are incompatible for comparison: Explain why with specific differences. |
| **Accessibility Behaviour** | Comparison view is `role="region"` with `aria-label="Comparison"`. Each column is `role="columnheader"`. Arrow keys navigate cells. |
| **Motion Behaviour** | Compare view opens with SlideIn (300ms). Differences highlight with Reveal (200ms, gold highlight that fades). |
| **Attention Behaviour** | Compare switches to Attentive state. AI may Suggest which item better matches criteria. |
| **Confidence Behaviour** | If AI suggests a preferred option, confidence bar is shown per option. |
| **Valid Composition** | Select(card_A) → Select(card_B) → Compare(view) → Inspect(diff) → Select(card_B) → Navigate(card_B) |
| **Invalid Composition** | Comparing without selecting. Comparing 20+ items. Suggesting a winner without showing confidence. |

### 2.7 Filter

| Field | Value |
|-------|-------|
| **Purpose** | Reduce a set of items to those matching specific criteria |
| **Applicable Situations** | Large result sets need narrowing; user has specific attribute requirements |
| **Required Primitives** | Focus, Select, Dismiss, Suggest |
| **Composition Sequence** | 1. Focus (filter control) → 2. Select (filter criteria) → 3. Set applies (list updates) → 4. Inspect (results) → 5. Dismiss (remove filter) OR Keep |
| **Entry Conditions** | A list or grid with filterable items is displayed |
| **Exit Conditions** | Filter is applied or cleared |
| **Alternative Paths** | **Quick filter**: Type to filter (combines Search + Filter). **Faceted filter**: Multiple filter dimensions stack. |
| **Failure Paths** | Filter yields zero results: Show "No results match your filters" with Suggest (clear filters). |
| **Accessibility Behaviour** | Filter controls are `role="group"` with `aria-label="Filters"`. Active filters are `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Filter application uses CrossFade (200ms) on the item list. Filter controls animate with Appear (200ms). |
| **Attention Behaviour** | Filter operates in Silent state. No AI suggestions during active filtering. |
| **Valid Composition** | Focus(filter_dropdown) → Select("Status: Active") → Inspect(filtered_list) |
| **Invalid Composition** | Filtering by every possible value just to browse. Hiding the filter count. |

### 2.8 Sort

| Field | Value |
|-------|-------|
| **Purpose** | Reorder items by a specified attribute |
| **Applicable Situations** | User needs items in a specific order (alphabetical, chronological, by priority) |
| **Required Primitives** | Focus, Select, Dismiss |
| **Composition Sequence** | 1. Focus (sort control) → 2. Select (sort criterion) → 3. Select (ascending/descending) → 4. Inspect (reordered list) |
| **Entry Conditions** | A list or table with sortable columns is displayed |
| **Exit Conditions** | Sort is applied |
| **Alternative Paths** | **Multi-sort**: Primary sort + secondary sort. **Column sort**: Click column header to sort by that column. |
| **Failure Paths** | Sort has no visible effect (all items equal for that criterion): Show "Items already in this order." |
| **Accessibility Behaviour** | Sortable columns are `role="columnheader"` with `aria-sort` attribute. Clicking toggles sort direction. |
| **Motion Behaviour** | Items animate to new positions using Expand/Collapse (300ms) with spatial continuity. |
| **Attention Behaviour** | Sort operates in Silent state. |
| **Valid Composition** | Focus(sort_menu) → Select("Date") → Select("Descending") → Inspect(list) |
| **Invalid Composition** | Sorting without indicating direction. Resetting the sort without user intent. |

### 2.9 Navigate

| Field | Value |
|-------|-------|
| **Purpose** | Move from one object or workspace to another |
| **Applicable Situations** | Every object-to-object or workspace-to-workspace transition |
| **Required Primitives** | Focus, Navigate, Return |
| **Composition Sequence** | 1. Focus (destination link) → 2. Navigate (to destination) → 3. Focus (destination content) → 4. Return (back to origin) |
| **Entry Conditions** | A navigable link or action is present |
| **Exit Conditions** | User has arrived at the destination or returned to origin |
| **Alternative Paths** | **Workspace navigate**: Switch workspace via workspace switcher. **Object navigate**: Open object from search, relationship, or link. **History navigate**: Back/forward through object history. |
| **Failure Paths** | Destination unavailable: Show "Object not found" with Suggest (search for similar). |
| **Accessibility Behaviour** | Navigation links are `role="link"` with `aria-label`. Focus moves to destination heading on arrival. Skip-links available. |
| **Motion Behaviour** | Workspace switch: SlideIn (400ms). Object navigate: Fade/zoom (300ms). History back: Reverse animation. |
| **Attention Behaviour** | Navigate preserves current attention state. If user was Scanning, new workspace starts in Scanning. |
| **Valid Composition** | Focus(relationship_link) → Navigate(related_object) → Focus(object_header) → Return(Escape or back gesture) |
| **Invalid Composition** | Opening in a new tab (internal navigation). Navigating without preserving the return path. |

### 2.10 Discover

| Field | Value |
|-------|-------|
| **Purpose** | Surface unexpected but relevant objects or connections the user may have missed |
| **Applicable Situations** | User has been away for a period; new objects or relationships have emerged |
| **Required Primitives** | Suggest, Preview, Inspect, Navigate, Dismiss |
| **Composition Sequence** | 1. Suggest (AI surfaces "You might want to see…") → 2. Preview (show summary) → 3. Inspect (user reviews) → 4. Navigate (to discovered item) OR Dismiss |
| **Entry Conditions** | System has detected a noteworthy item the user has not seen |
| **Exit Conditions** | User either acts on or dismisses the discovery |
| **Alternative Paths** | **Periodic discover**: After absence, show "Since your last visit" summary. **Pattern discover**: AI notices a pattern the user might have missed. |
| **Failure Paths** | No discoveries: Stay silent. No suggestion fired. |
| **Accessibility Behaviour** | Discovery suggestion is `role="status"` with `aria-live="polite"`. Focus remains on current content. |
| **Motion Behaviour** | Discovery appears as part of the AI Resident content with Reveal (300ms). No separate animation. |
| **Attention Behaviour** | Discovery fires only in Suggestive state (user is available). Never in Silent or Focused state. Confidence must be >0.80. |
| **Confidence Behaviour** | Discovery suggestion carries confidence bar. Minimum 0.80 to surface. |
| **Valid Composition** | Suggest(discovery) → Preview(summary) → Inspect(details) → Navigate(object) |
| **Invalid Composition** | Discovery triggering during focused work. Discovery without confidence indicator. Auto-navigating to the discovered item. |

---

## 3. Creation Patterns

### 3.1 Create

| Field | Value |
|-------|-------|
| **Purpose** | Create a new object in the system |
| **Applicable Situations** | User needs to add a new entity to the organizational knowledge |
| **Required Primitives** | Focus, Select, Confirm, Dismiss, Navigate |
| **Composition Sequence** | 1. Focus (create button) → 2. Select (object type) → 3. Fill (form fields) → 4. Confirm (create) → 5. Navigate (to new object) OR Dismiss (cancel) |
| **Entry Conditions** | User has authority to create objects in the current workspace |
| **Exit Conditions** | New object exists in the system, or creation was cancelled |
| **Alternative Paths** | **Quick create**: Minimal form (name only), then user can edit. **Template create**: Start from a template. **Duplicate create**: Clone an existing object (see Duplicate). |
| **Failure Paths** | Validation error: Show specific error inline. Highlight the offending field. Network error: Save draft locally, retry on reconnect. |
| **Accessibility Behaviour** | Form has `role="form"` with `aria-label`. Fields have `aria-required`. Submit is `role="button"`. Errors use `aria-describedby`. |
| **Motion Behaviour** | Create form opens with SlideIn (300ms) as a panel or dialog. On confirm, form collapses and new object appears with Reveal (300ms). |
| **Attention Behaviour** | Create switches to Focused state. No interruptions until creation completes or is cancelled. |
| **Confidence Behaviour** | AI may Suggest field values during form fill. Suggestions show confidence. |
| **Valid Composition** | Focus(create_btn) → Select("Decision") → Fill(name, description) → Confirm(submit) → Navigate(new_decision) |
| **Invalid Composition** | Creating an object without any fields filled. Requiring unnecessary fields for creation. |

### 3.2 Draft

| Field | Value |
|-------|-------|
| **Purpose** | Create a preliminary version of content for later completion |
| **Applicable Situations** | User wants to capture ideas quickly without committing to a complete object |
| **Required Primitives** | Focus, Select, Confirm, Dismiss, Defer |
| **Composition Sequence** | 1. Focus (draft button) → 2. Fill (minimal content) → 3. Confirm (save draft) → 4. Defer (return later) |
| **Entry Conditions** | User has an idea to capture but does not have complete information |
| **Exit Conditions** | Draft is saved for later completion |
| **Alternative Paths** | **AI draft**: User gives a brief description → AI generates draft content → User reviews and edits. |
| **Failure Paths** | Save fails: Auto-save to local storage, sync when online. |
| **Accessibility Behaviour** | Same as Create, with additional `aria-label="Draft"` indicators. |
| **Motion Behaviour** | Draft save is instant (no animation — duration-instant). |
| **Attention Behaviour** | Drafting respects current attention state. AI may Suggest completions if user pauses >5s. |
| **Valid Composition** | Focus(draft_btn) → Fill(title + note) → Confirm(save) → Defer(later) |
| **Invalid Composition** | Requiring all fields for a draft. Discarding drafts without warning. |

### 3.3 Capture

| Field | Value |
|-------|-------|
| **Purpose** | Quickly record information from an external source into SHUNYA |
| **Applicable Situations** | User has information (clipboard, file, camera, voice memo) to import |
| **Required Primitives** | Focus, Select, Confirm, Suggest, Dismiss |
| **Composition Sequence** | 1. Focus (capture button) → 2. Select (capture source) → 3. AI processes input → 4. Preview (review captured content) → 5. Confirm (save) OR Dismiss |
| **Entry Conditions** | User has external content to import |
| **Exit Conditions** | Content is captured into the system or discarded |
| **Alternative Paths** | **Clipboard capture**: Paste text directly. **File capture**: Upload and auto-extract. **OCR capture**: Image to text. |
| **Failure Paths** | Unprocessable content: Explain what was not captured. Let user manually correct. |
| **Accessibility Behaviour** | Capture feedback is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Capture processing shows a skeleton pulse (1500ms max), then content appears with Reveal (200ms). |
| **Attention Behaviour** | During capture processing, switches to Silent state. When complete, transitions to Suggestive (one suggestion: "Review captured content"). |
| **Confidence Behaviour** | AI's interpretation of captured content shows confidence per extracted field. |
| **Valid Composition** | Focus(capture) → Select("Clipboard") → Preview(extracted_text) → Confirm(save) |
| **Invalid Composition** | Silently capturing without user preview. Discarding low-confidence extractions without informing user. |

### 3.4 Import

| Field | Value |
|-------|-------|
| **Purpose** | Bring structured data from external systems into SHUNYA |
| **Applicable Situations** | Bulk data migration, integration with external tools |
| **Required Primitives** | Focus, Select, Confirm, Suggest, Dismiss |
| **Composition Sequence** | 1. Focus (import button) → 2. Select (source format) → 3. Select (file/connection) → 4. Preview (mapped fields) → 5. Confirm (import) → 6. Suggest (review results) |
| **Entry Conditions** | User has data to import in a supported format |
| **Exit Conditions** | Data is imported and user has reviewed the results |
| **Alternative Paths** | **Incremental import**: Import only new/changed records. **Full import**: Replace all existing data. |
| **Failure Paths** | Mapping errors: Show unmapped fields with Suggest (manual mapping). Partial import: Import what succeeded, report failures. |
| **Accessibility Behaviour** | Import progress is `role="progressbar"` with `aria-valuenow`. Completion is `role="status"`. |
| **Motion Behaviour** | Import progress uses linear progress bar (no animation, width changes instantly). Results appear with Reveal (300ms). |
| **Attention Behaviour** | Import runs in background (Silent state). On completion, switches to Suggestive ("Import complete. Review X records."). |
| **Confidence Behaviour** | Import confidence per record: green (matched), amber (partial match), red (unmatched). |
| **Valid Composition** | Focus(import) → Select("CSV") → Select(file) → Preview(field_map) → Confirm(execute) → Suggest(review) |
| **Invalid Composition** | Importing without mapping preview. Overwriting existing data without confirmation. |

### 3.5 Duplicate

| Field | Value |
|-------|-------|
| **Purpose** | Create a copy of an existing object as a starting point for a new one |
| **Applicable Situations** | User wants to create a similar object based on an existing one |
| **Required Primitives** | Focus, Select, Confirm, Dismiss, Navigate |
| **Composition Sequence** | 1. Focus (duplicate action) → 2. Select (object to clone) → 3. Confirm (duplicate) → 4. Navigate (to new copy) |
| **Entry Conditions** | An existing object is selected |
| **Exit Conditions** | A new copy exists and user is viewing it |
| **Alternative Paths** | **Shallow duplicate**: Copy all fields except relationships. **Deep duplicate**: Copy everything including relationships. |
| **Failure Paths** | Duplicate name conflict: Append " (copy)" automatically. Let user rename immediately. |
| **Accessibility Behaviour** | Duplicate action is a `role="button"` with `aria-label="Duplicate [object name]"`. |
| **Motion Behaviour** | New copy appears with Reveal (300ms). No separate loading state. |
| **Attention Behaviour** | Duplicate respects current attention state. |
| **Valid Composition** | Focus(object) → Select("Duplicate") → Confirm(duplicate) → Navigate(new_object) |
| **Invalid Composition** | Duplicating without naming the copy. Creating a duplicate that the user cannot immediately identify as a copy. |

### 3.6 Transform

| Field | Value |
|-------|-------|
| **Purpose** | Change an object from one type to another while preserving relevant data |
| **Applicable Situations** | An object was created as the wrong type and needs conversion |
| **Required Primitives** | Focus, Select, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Focus (transform action) → 2. Select (target type) → 3. Explain (what will be preserved/lost) → 4. Confirm (transform) |
| **Entry Conditions** | Object is of a type that can be transformed to another type |
| **Exit Conditions** | Object has been transformed or transformation was cancelled |
| **Alternative Paths** | **Auto-transform**: AI detects mismatch and suggests transformation. |
| **Failure Paths** | Data loss inevitable: Show exactly what will be lost. Require explicit confirmation. |
| **Accessibility Behaviour** | Transform warning is `role="alertdialog"` with `aria-describedby` explaining data impact. |
| **Motion Behaviour** | Transform confirmation opens as Dialog (300ms). On confirm, object re-renders with Reveal (300ms). |
| **Attention Behaviour** | Transform switches to Focused state. No interruptions during data migration. |
| **Confidence Behaviour** | AI's transformation mapping shows confidence per field. |
| **Valid Composition** | Focus(object) → Select("Transform to Project") → Explain(preserved_fields) → Confirm(transform) |
| **Invalid Composition** | Transforming without warning about data loss. Transforming without user confirming. |

### 3.7 Merge

| Field | Value |
|-------|-------|
| **Purpose** | Combine two or more objects into a single unified object |
| **Applicable Situations** | Duplicate objects exist; related objects should be consolidated |
| **Required Primitives** | Focus, Select, Compare, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Select (primary object) → 2. Select (object to merge) → 3. Compare (field-by-field) → 4. Select (which value to keep per field) → 5. Confirm (merge) |
| **Entry Conditions** | Two or more objects of a mergeable type are selected |
| **Exit Conditions** | Objects are merged into one, or merge was cancelled |
| **Alternative Paths** | **Auto-merge**: AI suggests the best value for each field. User can override per field. **Bulk merge**: Merge 3+ objects at once. |
| **Failure Paths** | Irreconcilable differences: Flag conflicting fields for manual resolution. |
| **Accessibility Behaviour** | Merge comparison is `role="region"` with `aria-label="Merge comparison"`. Each field row has `role="row"`. |
| **Motion Behaviour** | Merge comparison opens with SlideIn (300ms). Field resolution shows Reveal (200ms). On confirm, merged object appears with CrossFade (300ms). |
| **Attention Behaviour** | Merge switches to Focused state. |
| **Confidence Behaviour** | AI's field suggestions show confidence. User override removes confidence (human decision). |
| **Valid Composition** | Select(primary) → Select(duplicate) → Compare(fields) → Select(keep_field_A from primary, keep_field_B from duplicate) → Confirm(merge) |
| **Invalid Composition** | Merging without showing the user what each object contributes. Auto-merging without per-field review. |

### 3.8 Split

| Field | Value |
|-------|-------|
| **Purpose** | Divide one object into two or more separate objects |
| **Applicable Situations** | An object contains distinct concerns that should be separate entities |
| **Required Primitives** | Focus, Select, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Focus (split action) → 2. Select (what to move to new object) → 3. Explain (result preview) → 4. Confirm (split) |
| **Entry Conditions** | Object contains separable sub-units |
| **Exit Conditions** | Two or more objects exist where one was, or split was cancelled |
| **Alternative Paths** | **AI-suggested split**: AI detects separable concerns and proposes split boundaries. |
| **Failure Paths** | Cannot split (atomic object): Explain why the object cannot be divided. |
| **Accessibility Behaviour** | Split selection is `role="listbox"` with multi-select. Preview is `role="region"` with `aria-live="polite"`. |
| **Motion Behaviour** | Split preview shows with CrossFade (200ms). On split, original object and new objects appear with Reveal (300ms). |
| **Attention Behaviour** | Split switches to Focused state. |
| **Valid Composition** | Focus(object) → Select(sections_to_extract) → Explain(result_preview) → Confirm(split) |
| **Invalid Composition** | Splitting without showing the user the result preview. Forcing a split without allowing adjustment of boundaries. |

### 3.9 Link

| Field | Value |
|-------|-------|
| **Purpose** | Establish a relationship between two objects |
| **Applicable Situations** | Two objects are related and that relationship should be recorded |
| **Required Primitives** | Focus, Search, Select, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (link action) → 2. Search (for target object) → 3. Select (target object) → 4. Select (relationship type) → 5. Confirm (create link) |
| **Entry Conditions** | An object is active and the user wants to connect it to another |
| **Exit Conditions** | Relationship exists between the two objects, or linking was cancelled |
| **Alternative Paths** | **Quick link**: Type or paste object ID directly. **Smart link**: AI suggests likely relationships based on context. |
| **Failure Paths** | Circular relationship: Warn and block. Duplicate relationship: Show existing relationship and offer to update it. |
| **Accessibility Behaviour** | Link search is `role="combobox"` with `aria-expanded`. Results are `role="listbox"`. |
| **Motion Behaviour** | Link panel opens with SlideIn (300ms). Confirmation shows toast (4s). |
| **Attention Behaviour** | Linking respects current attention state. |
| **Valid Composition** | Focus(link_btn) → Search("Q3 Budget") → Select(result) → Select("depends_on") → Confirm(link) |
| **Invalid Composition** | Creating duplicate links. Linking without specifying relationship type. Allowing self-links. |

### 3.10 Unlink

| Field | Value |
|-------|-------|
| **Purpose** | Remove a relationship between two objects |
| **Applicable Situations** | A relationship is no longer valid |
| **Required Primitives** | Focus, Select, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Focus (relationship) → 2. Select (unlink action) → 3. Explain (what will be affected) → 4. Confirm (unlink) |
| **Entry Conditions** | A relationship exists between two objects |
| **Exit Conditions** | Relationship is removed, or unlinking was cancelled |
| **Alternative Paths** | **Soft unlink**: Mark relationship as deprecated (still visible in history). **Hard unlink**: Permanently remove. |
| **Failure Paths** | Relationship required by dependent objects: Explain dependencies and block or cascade. |
| **Accessibility Behaviour** | Unlink confirmation is `role="alertdialog"` with `aria-describedby`. |
| **Motion Behaviour** | Unlink shows a brief Reveal (200ms) of the relationship being removed, then CrossFade (200ms) to updated state. |
| **Attention Behaviour** | Unlink respects current attention state. |
| **Valid Composition** | Focus(relationship) → Select("Unlink") → Explain(effects) → Confirm(unlink) |
| **Invalid Composition** | Unlinking without warning about downstream effects. Silent unlinking without user confirmation. |

---

## 4. Decision Patterns

### 4.1 Review

| Field | Value |
|-------|-------|
| **Purpose** | Examine an object or proposal before making a decision |
| **Applicable Situations** | An object is in a pending state awaiting evaluation |
| **Required Primitives** | Focus, Inspect, Expand, Collapse, Suggest, Explain, Navigate |
| **Composition Sequence** | 1. Navigate (to pending object) → 2. Inspect (executive summary) → 3. Expand (evidence section) → 4. Inspect (evidence items) → 5. Suggest (AI surfaces relevant context) → 6. Explain (AI reasoning on demand) → 7. Decision (approve/reject/request changes) |
| **Entry Conditions** | An object is in a review-required state; user has authority to review |
| **Exit Conditions** | User has made a decision on the object or deferred it |
| **Alternative Paths** | **Quick review**: Read summary only → Decide. **Deep review**: Expand all evidence, inspect relationships, call AI analysis. **Collaborative review**: Multiple reviewers each provide input. |
| **Failure Paths** | Missing evidence: Show what is missing. Defer review until evidence is complete. |
| **Accessibility Behaviour** | Review sections are `role="region"` with clear `aria-label`. Evidence items are `role="listitem"`. |
| **Motion Behaviour** | Summary always visible (never animates). Evidence sections Expand/Collapse (300ms). AI suggestions appear with Reveal (200ms). |
| **Attention Behaviour** | Review operates in Focused state. No interruptions. AI waits for user to open AI panel before suggesting. |
| **Confidence Behaviour** | Executive summary shows overall confidence. Each evidence item shows individual confidence. AI suggestions show confidence. |
| **Valid Composition** | Navigate(pending_decision) → Inspect(summary) → Expand(evidence) → Inspect(evidence[1]) → Suggest(AI_analysis) → Explain(why) → Approve |
| **Invalid Composition** | Making a decision without reviewing any evidence. AI making the decision without user confirmation. |

### 4.2 Approve

| Field | Value |
|-------|-------|
| **Purpose** | Formally accept a proposal, decision, or object |
| **Applicable Situations** | User has authority to approve and has completed review |
| **Required Primitives** | Focus, Confirm, Explain, Dismiss, Suggest |
| **Composition Sequence** | 1. Focus (approve button) → 2. Suggest (AI shows post-approval effects) → 3. Explain (what happens after approval) → 4. Confirm (approve) |
| **Entry Conditions** | User has reviewed the object and has approval authority |
| **Exit Conditions** | Object status changed to approved, or approval cancelled |
| **Alternative Paths** | **Conditional approve**: Approve with conditions that must be met. **Delegated approve**: Auto-approved if criteria met (user configures policy). |
| **Failure Paths** | Authority check fails: Explain why user cannot approve. Suggest (escalate to appropriate authority). |
| **Accessibility Behaviour** | Approve button is `role="button"` with high-contrast styling. Confirmation is `role="alertdialog"`. |
| **Motion Behaviour** | Approval processes with a brief progress indicator (linear, no animation). On completion, object re-renders with CrossFade (300ms). Toast confirms (4s). |
| **Attention Behaviour** | Approval switches to Focused state. |
| **Confidence Behaviour** | AI may show confidence in the approval recommendation. Post-approval effects show confidence. |
| **Valid Composition** | Focus(approve_btn) → Suggest(effects) → Explain(post_approval) → Confirm(approval) |
| **Invalid Composition** | Approving without showing post-approval effects. One-click approval for irreversible decisions. |

### 4.3 Reject

| Field | Value |
|-------|-------|
| **Purpose** | Formally decline a proposal, decision, or object |
| **Applicable Situations** | User has determined the proposal should not proceed |
| **Required Primitives** | Focus, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (reject button) → 2. Explain (consequences of rejection) → 3. Fill (reason for rejection) → 4. Confirm (reject) |
| **Entry Conditions** | User has reviewed and decided against approval |
| **Exit Conditions** | Object is rejected with documented reason, or rejection cancelled |
| **Alternative Paths** | **Soft reject**: Send back for revision instead of final rejection. |
| **Failure Paths** | Reject without reason: Require a reason field. |
| **Accessibility Behaviour** | Reject reason is `aria-required="true"`. Confirmation is `role="alertdialog"`. |
| **Motion Behaviour** | Rejection panel opens with Dialog (300ms). On confirm, state updates with CrossFade (300ms). |
| **Attention Behaviour** | Rejection respects current attention state. |
| **Valid Composition** | Focus(reject_btn) → Explain(consequences) → Fill(reason) → Confirm(reject) |
| **Invalid Composition** | Rejecting without providing a reason. Making rejection feel punitive rather than informative. |

### 4.4 Recommend

| Field | Value |
|-------|-------|
| **Purpose** | Surface an AI-generated or human-generated suggestion for consideration |
| **Applicable Situations** | A choice exists and guidance would help the decision-maker |
| **Required Primitives** | Suggest, Explain, Focus, Select, Dismiss |
| **Composition Sequence** | 1. Suggest (recommendation appears) → 2. Explain (reasoning behind recommendation) → 3. Focus (user considers) → 4. Select (accept recommendation) OR Dismiss OR Suggest (alternative) |
| **Entry Conditions** | A decision point has been reached and the system or a user has a recommendation |
| **Exit Conditions** | User has accepted, dismissed, or requested an alternative recommendation |
| **Alternative Paths** | **AI recommend**: System analyzes data and suggests. **Peer recommend**: Another user's recommendation. **Comparison recommend**: Compare multiple recommendations. |
| **Failure Paths** | Recommendation confidence too low: Show with low-confidence UI. User may still view it. |
| **Accessibility Behaviour** | Recommendation is `role="status"` with `aria-live="polite"`. Source is `role="link"`. |
| **Motion Behaviour** | Recommendation appears with Reveal (300ms) in the AI Resident panel. Confidence bar updates with width transition (300ms). |
| **Attention Behaviour** | Recommendation fires in Suggestive state (user available, not focused). Never in Silent or Focused. |
| **Confidence Behaviour** | Every recommendation shows: confidence bar, source count, and top sources. |
| **Valid Composition** | Suggest(recommendation) → Explain(reasoning) → Focus(options) → Select(accept) |
| **Invalid Composition** | Recommending without confidence indicator. Making the recommendation appear to be a command. |

### 4.5 Escalate

| Field | Value |
|-------|-------|
| **Purpose** | Move a decision or issue to a higher authority |
| **Applicable Situations** | Current user lacks authority, expertise, or comfort to decide |
| **Required Primitives** | Focus, Select, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (escalate action) → 2. Select (target authority) → 3. Explain (context summary) → 4. Confirm (escalate) |
| **Entry Conditions** | Current user cannot or should not make the final decision |
| **Exit Conditions** | The decision has been transferred to the target, or escalation cancelled |
| **Alternative Paths** | **Auto-escalate**: System detects authority boundary and auto-escalates. **Multi-escalate**: Escalate to multiple authorities. |
| **Failure Paths** | Target unavailable: Queue escalation, notify when target is available. |
| **Accessibility Behaviour** | Escalation form is `role="form"` with context autofilled. Confirmation is `role="alertdialog"`. |
| **Motion Behaviour** | Escalation opens with SlideIn (300ms). Confirmation shows toast (4s). |
| **Attention Behaviour** | Escalation switches briefly to Focused, then returns to previous state when complete. |
| **Valid Composition** | Focus(escalate) → Select("CFO") → Explain(context_summary) → Confirm(escalate) |
| **Invalid Composition** | Escalating without context. Escalating trivial decisions. |

### 4.6 Delegate

| Field | Value |
|-------|-------|
| **Purpose** | Assign responsibility for a decision or action to another person |
| **Applicable Situations** | User wants someone else to handle a decision or task |
| **Required Primitives** | Focus, Select, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (delegate action) → 2. Select (assignee) → 3. Explain (expectations + deadline) → 4. Confirm (delegate) |
| **Entry Conditions** | Current user has authority to delegate |
| **Exit Conditions** | Responsibility is transferred, or delegation cancelled |
| **Alternative Paths** | **AI suggest delegate**: AI suggests optimal assignee based on workload and expertise. |
| **Failure Paths** | Assignee overloaded: Warn and suggest alternative. |
| **Accessibility Behaviour** | Assignee selector is `role="combobox"` with search. |
| **Motion Behaviour** | Delegate panel opens with SlideIn (300ms). Assignment shows toast (4s). |
| **Attention Behaviour** | Delegation respects current attention state. |
| **Valid Composition** | Focus(delegate) → Select(person) → Explain(expectations) → Confirm(delegate) |
| **Invalid Composition** | Delegating without the assignee's awareness. Delegating to someone without authority. |

### 4.7 Assign

| Field | Value |
|-------|-------|
| **Purpose** | Allocate a task or object to a specific person |
| **Applicable Situations** | A task needs an owner |
| **Required Primitives** | Focus, Select, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (assign action) → 2. Select (assignee) → 3. Confirm (assign) |
| **Entry Conditions** | An unassigned task or object exists |
| **Exit Conditions** | Task has an owner, or assignment cancelled |
| **Alternative Paths** | **Self-assign**: Quick assignment to self. **Round-robin**: System assigns to next available person. |
| **Failure Paths** | Assignee at capacity: Warn and confirm override. |
| **Accessibility Behaviour** | Assignee selector is `role="combobox"`. |
| **Motion Behaviour** | Assignment updates with CrossFade (200ms). |
| **Attention Behaviour** | Assignment respects current attention state. |
| **Valid Composition** | Focus(task) → Select(member) → Confirm(assign) |
| **Invalid Composition** | Assigning without notifying the assignee. Overloading a single person. |

### 4.8 Confirm

| Field | Value |
|-------|-------|
| **Purpose** | Require explicit user acknowledgment before an irreversible action |
| **Applicable Situations** | Any action that cannot be undone or has significant consequences |
| **Required Primitives** | Focus, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Focus (action) → 2. Explain (consequences) → 3. Confirm (yes, proceed) OR Dismiss (no, cancel) |
| **Entry Conditions** | User has initiated an action with significant consequences |
| **Exit Conditions** | Action is executed or cancelled |
| **Alternative Paths** | **Conditional confirm**: "Proceed with these conditions." **Timed confirm**: Auto-confirm after delay for non-critical actions. |
| **Failure Paths** | User repeatedly confirms the same action: Detect loop and block. |
| **Accessibility Behaviour** | Confirmation dialog is `role="alertdialog"` with `aria-describedby`. Focus is trapped. Escape cancels. |
| **Motion Behaviour** | Dialog opens with Dialog(300ms). On confirm, action executes with appropriate animation. On cancel, dialog closes with Disappear(150ms). |
| **Attention Behaviour** | Confirm switches to Focused state. |
| **Valid Composition** | Focus(delete_btn) → Explain("This action cannot be undone") → Confirm("Delete") |
| **Invalid Composition** | Confirming reversible actions (saving, editing). Asking for confirmation when undo is available. |

### 4.9 Undo

| Field | Value |
|-------|-------|
| **Purpose** | Reverse the last user action |
| **Applicable Situations** | Any reversible action the user wants to revert |
| **Required Primitives** | Focus, Undo, Redo, Confirm, Explain |
| **Composition Sequence** | 1. Focus (undo action) → 2. Undo (reverse last action) → 3. Explain (what was undone) → 4. Confirm (user acknowledges) OR Redo (reapply if undesired) |
| **Entry Conditions** | An undoable action exists in the session history |
| **Exit Conditions** | Action is undone, or user chose to keep it (redo) |
| **Alternative Paths** | **Multi-undo**: Undo N actions at once (show list). **Timeline undo**: Select specific point in history to revert to. |
| **Failure Paths** | Action cannot be undone: Explain why (external side effects). Offer to create a compensating action. |
| **Accessibility Behaviour** | Undo is `role="button"` with shortcut Ctrl+Z. Undo toast is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Undo reverses the original action's animation. If object was created (Reveal), undo uses Disappear (150ms). |
| **Attention Behaviour** | Undo fires in any state. Toast appears briefly regardless of attention state. |
| **Valid Composition** | Focus(undo) → Undo() → Explain(object_removed) → Redo() (if desired) |
| **Invalid Composition** | Undoing without showing what was undone. Undoing with side effects the user cannot see. |

### 4.10 Resolve

| Field | Value |
|-------|-------|
| **Purpose** | Complete a decision process and move to execution |
| **Applicable Situations** | All review steps are complete and the decision is finalized |
| **Required Primitives** | Focus, Confirm, Explain, Suggest, Navigate |
| **Composition Sequence** | 1. Focus (resolve action) → 2. Suggest (AI summarizes what will happen next) → 3. Explain (execution plan) → 4. Confirm (resolve) → 5. Navigate (to execution view) |
| **Entry Conditions** | Decision has been made (approved/rejected) |
| **Exit Conditions** | Decision is marked as resolved and execution begins |
| **Alternative Paths** | **Auto-resolve**: Auto-resolve when all approvers have responded. |
| **Failure Paths** | Unresolved dependencies: Show blocking items. Cannot resolve until dependencies are met. |
| **Accessibility Behaviour** | Resolution summary is `role="region"` with `aria-live="polite"`. |
| **Motion Behaviour** | Resolution shows a completion animation: object transitions to completed state with CrossFade (300ms). |
| **Attention Behaviour** | Resolution switches to Focused briefly, then returns to Scanning when execution view opens. |
| **Valid Composition** | Focus(resolve) → Suggest(next_steps) → Explain(execution) → Confirm(resolve) → Navigate(execution_view) |
| **Invalid Composition** | Resolving without showing the user what happens next. Marking as resolved while dependencies are pending. |

---

## 5. Knowledge Patterns

### 5.1 Explain

| Field | Value |
|-------|-------|
| **Purpose** | Reveal the reasoning or context behind an assertion or object |
| **Applicable Situations** | User sees an AI assertion or object state and wants to understand why |
| **Required Primitives** | Explain, Unexplain, Focus, Inspect, Suggest |
| **Composition Sequence** | 1. Focus (assertion) → 2. Explain (show reasoning) → 3. Inspect (review reasoning) → 4. Suggest (AI offers deeper analysis) → 5. Unexplain (collapse) OR Keep |
| **Entry Conditions** | An explainable assertion or state is visible |
| **Exit Conditions** | User has reviewed the explanation or dismissed it |
| **Alternative Paths** | **Depth-adjusted explain**: Show explanation at user's preferred depth (executive/professional/technical/full evidence). **Multi-source explain**: Show all evidence sources. |
| **Failure Paths** | No explanation available: "This assertion was made before explanation tracking was enabled." |
| **Accessibility Behaviour** | Explanation panel is `role="region"` with `aria-live="polite"`. Each source is `role="link"`. |
| **Motion Behaviour** | Explanation expands with Expand (300ms). Sources appear with Stagger (50ms). Unexplain uses Collapse (200ms). |
| **Attention Behaviour** | Explanation is user-initiated (Focus). System does not change attention state. |
| **Confidence Behaviour** | Explanation shows per-source confidence and aggregate confidence. |
| **Valid Composition** | Focus(confidence_bar) → Explain(breakdown) → Inspect(reasoning_steps) → Unexplain(Escape) |
| **Invalid Composition** | Showing an explanation that is longer than the original assertion. Explaining without showing source links. |

### 5.2 Summarize

| Field | Value |
|-------|-------|
| **Purpose** | Condense information into its essential points |
| **Applicable Situations** | User needs the key points from a larger body of information |
| **Required Primitives** | Suggest, Explain, Focus, Inspect, Expand, Collapse |
| **Composition Sequence** | 1. Suggest (summary appears) → 2. Inspect (read summary) → 3. Expand (view full content) OR Collapse (return to summary) OR Explain (why this summary) |
| **Entry Conditions** | Content that can be summarized is available |
| **Exit Conditions** | User has read the summary and either expanded or moved on |
| **Alternative Paths** | **Auto-summarize**: Summary appears by default on object open. **On-demand summarize**: User requests summary. **Levels of summarization**: One-line, brief, detailed. |
| **Failure Paths** | Summary confidence low: Show "Low confidence summary" with source limitations. |
| **Accessibility Behaviour** | Summary is `role="region"` with `aria-label="Summary"`. Expand is `role="button"`. |
| **Motion Behaviour** | Summary appears with Reveal (200ms). Expand/Collapse uses Expand/Collapse (300ms/200ms). |
| **Attention Behaviour** | Summary is the default view in Suggestive state. When user expands, switches to Focused. |
| **Confidence Behaviour** | Summary shows overall confidence. |
| **Valid Composition** | Suggest(summary) → Inspect(summary) → Expand(full_document) → Collapse(back_to_summary) |
| **Invalid Composition** | Showing an empty summary ("No summary available") without explaining why. Making the summary longer than the original content. |

### 5.3 Teach

| Field | Value |
|-------|-------|
| **Purpose** | Educate the user about a concept, pattern, or process within SHUNYA |
| **Applicable Situations** | User needs to understand a new capability or concept |
| **Required Primitives** | Suggest, Explain, Focus, Navigate, Preview |
| **Composition Sequence** | 1. Suggest (AI offers to teach) → 2. Explain (concept) → 3. Preview (example) → 4. Navigate (to relevant object for practice) |
| **Entry Conditions** | User has encountered a concept they may not fully understand |
| **Exit Conditions** | User has been taught or declined the teaching |
| **Alternative Paths** | **Contextual teach**: Triggered by user action that suggests lack of understanding. **On-demand teach**: User asks "How do I...?" |
| **Failure Paths** | Teaching rejected: Do not offer again for this concept. |
| **Accessibility Behaviour** | Teaching content is `role="region"` with clear headings. Examples are `role="figure"`. |
| **Motion Behaviour** | Teaching material appears with Reveal (300ms). Examples use Preview. |
| **Attention Behaviour** | Teaching offered in Suggestive state. When user accepts, switches to Focused. |
| **Valid Composition** | Suggest(teach_opportunity) → Explain(concept) → Preview(example) → Navigate(practice_object) |
| **Invalid Composition** | Teaching without user invitation (proactive popup tutorials). Teaching basic interactions the user can discover naturally. |

### 5.4 Learn

| Field | Value |
|-------|-------|
| **Purpose** | Allow the system to acquire knowledge from user actions or corrections |
| **Applicable Situations** | User corrects AI, provides new information, or demonstrates a preference |
| **Required Primitives** | Suggest, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. User corrects or provides data → 2. Suggest (AI: "I learned something new") → 3. Explain (what was learned) → 4. Confirm (user acknowledges) OR Dismiss |
| **Entry Conditions** | New information is available that the system did not previously know |
| **Exit Conditions** | System has acknowledged the learning or user dismissed it |
| **Alternative Paths** | **Implicit learn**: System learns without announcing it (user corrections, usage patterns). **Explicit learn**: User explicitly teaches the system. |
| **Failure Paths** | Learning conflicts with existing knowledge: Explain the conflict and ask user to resolve. |
| **Accessibility Behaviour** | Learning acknowledgment is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Learning acknowledgment is minimal — a toast (4s) or inline text update. No celebratory animation. |
| **Attention Behaviour** | Learning acknowledgment fires briefly regardless of attention state. Never blocks or interrupts. |
| **Confidence Behaviour** | Learned information starts with human confidence (1.0) and decays over time without reinforcement. |
| **Valid Composition** | Suggest(new_knowledge) → Explain(what_changed) → Confirm(acknowledge) |
| **Invalid Composition** | Learning without informing the user. Announcing trivial learning events. |

### 5.5 Recall

| Field | Value |
|-------|-------|
| **Purpose** | Surface previously learned or stored information relevant to the current context |
| **Applicable Situations** | User is working on something related to past knowledge |
| **Required Primitives** | Suggest, Explain, Preview, Inspect, Dismiss |
| **Composition Sequence** | 1. Suggest (AI recalls relevant information) → 2. Preview (show summary) → 3. Inspect (review details) → 4. Explain (context relevance) → 5. Dismiss OR Navigate |
| **Entry Conditions** | System has stored knowledge relevant to the current context |
| **Exit Conditions** | User has reviewed or dismissed the recalled information |
| **Alternative Paths** | **Contextual recall**: Triggered by current workspace/object. **Query recall**: "Do we have anything on X?" |
| **Failure Paths** | Nothing relevant to recall: Stay silent. |
| **Accessibility Behaviour** | Recalled information is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Recalled information appears in AI Resident with Reveal (200ms). |
| **Attention Behaviour** | Recall fires in Suggestive state. Never in Silent or Focused. |
| **Confidence Behaviour** | Recalled information shows confidence based on age and source quality. |
| **Valid Composition** | Suggest(recall) → Preview(summary) → Inspect(details) → Explain(relevance) → Dismiss |
| **Invalid Composition** | Recalling irrelevant information. Recalling the same thing multiple times in one session. |

### 5.6 Trace

| Field | Value |
|-------|-------|
| **Purpose** | Follow the provenance chain of a fact, decision, or object back to its origin |
| **Applicable Situations** | User needs to verify the source of information or understand how a conclusion was reached |
| **Required Primitives** | Focus, Navigate, Explain, Inspect, Expand, Collapse |
| **Composition Sequence** | 1. Focus (fact or decision) → 2. Explain (show provenance chain) → 3. Inspect (review each source) → 4. Expand (show full source detail) → 5. Navigate (to original source) |
| **Entry Conditions** | A fact, decision, or object with recorded provenance exists |
| **Exit Conditions** | User has traced to the original source or stopped at an intermediate step |
| **Alternative Paths** | **Visual trace**: Graph view of provenance chain. **List trace**: Linear list of sources. |
| **Failure Paths** | Provenance gap: Show "Source unknown" for that step. |
| **Accessibility Behaviour** | Provenance chain is `role="list"`. Each step is `role="listitem"` with `aria-label`. |
| **Motion Behaviour** | Provenance chain expands with Expand (300ms). Each step appears with Stagger (50ms). Navigating to source uses Navigate (300ms). |
| **Attention Behaviour** | Tracing switches to Focused state. |
| **Confidence Behaviour** | Each provenance step shows its own confidence. Overall trace confidence is the minimum of all steps. |
| **Valid Composition** | Focus(decision) → Explain(provenance) → Inspect(source[1]) → Expand(source[1]_detail) → Navigate(source[1]) |
| **Invalid Composition** | Hiding provenance gaps. Showing provenance without confidence per step. |

### 5.7 Investigate

| Field | Value |
|-------|-------|
| **Purpose** | Deeply explore a specific question, anomaly, or area of interest |
| **Applicable Situations** | Something unexpected or noteworthy requires deeper understanding |
| **Required Primitives** | Focus, Search, Inspect, Expand, Navigate, Suggest, Explain |
| **Composition Sequence** | 1. Focus (anomaly or question) → 2. Suggest (AI proposes investigation path) → 3. Search (for related data) → 4. Inspect (findings) → 5. Expand (deep dive) → 6. Explain (AI analysis) → 7. Navigate (to source) OR Conclude |
| **Entry Conditions** | User has identified something worth investigating |
| **Exit Conditions** | User has concluded the investigation or reached a dead end |
| **Alternative Paths** | **Guided investigation**: AI leads the investigation, user confirms each step. **Free investigation**: User explores independently, AI provides context on demand. |
| **Failure Paths** | Investigation yields no results: "Investigation complete. No relevant data found." |
| **Accessibility Behaviour** | Investigation workspace is `role="region"` with `aria-label="Investigation"`. |
| **Motion Behaviour** | Investigation steps appear with Reveal (200ms). Findings load with progressive rendering (no spinner). |
| **Attention Behaviour** | Investigation switches to Focused state. AI defers to user's pace. |
| **Confidence Behaviour** | AI analysis during investigation shows confidence per finding. |
| **Valid Composition** | Focus(anomaly) → Suggest(path) → Search(datasets) → Inspect(correlation) → Explain(analysis) → Navigate(source) |
| **Invalid Composition** | Investigating without a clear question. Drawing conclusions from low-confidence data without flagging it. |

### 5.8 Reference

| Field | Value |
|-------|-------|
| **Purpose** | Consult a known source of information for verification or context |
| **Applicable Situations** | User needs to check facts, policies, or historical data |
| **Required Primitives** | Focus, Search, Inspect, Preview, Navigate, Dismiss |
| **Composition Sequence** | 1. Focus (reference action) → 2. Search (for specific reference) → 3. Preview (match summary) → 4. Inspect (read reference) → 5. Navigate (to full reference) OR Dismiss |
| **Entry Conditions** | A reference source exists that is relevant to the current context |
| **Exit Conditions** | User has consulted the reference or moved on |
| **Alternative Paths** | **Contextual reference**: Automatically suggested based on current object. **Manual reference**: User navigates to knowledge base directly. |
| **Failure Paths** | Reference not found: "No reference matches your query." Suggest alternative searches. |
| **Accessibility Behaviour** | Reference sources are `role="link"`. Search is `role="search"`. |
| **Motion Behaviour** | Reference opens in KnowledgeSurface tab with SlideIn (300ms) or same-tab navigation. |
| **Attention Behaviour** | Reference consultation respects current attention state. |
| **Valid Composition** | Focus(reference_link) → Search("policy v2.1") → Preview(match) → Inspect(details) → Navigate(full_document) |
| **Invalid Composition** | Referencing without citing the version or date. Treating all references as equally authoritative. |

### 5.9 Compare Evidence

| Field | Value |
|-------|-------|
| **Purpose** | Evaluate multiple pieces of evidence side by side |
| **Applicable Situations** | Conflicting evidence exists; user needs to assess relative quality |
| **Required Primitives** | Select, Compare, Uncompare, Focus, Inspect, Suggest, Explain |
| **Composition Sequence** | 1. Select (evidence A) → 2. Select (evidence B) → 3. Compare (side-by-side) → 4. Inspect (differences) → 5. Suggest (AI assesses relative quality) → 6. Explain (reasoning) → 7. Uncompare OR Select (preferred) |
| **Entry Conditions** | Two or more evidence items are available for comparison |
| **Exit Conditions** | User has evaluated the evidence or cancelled the comparison |
| **Alternative Paths** | **Timeline comparison**: Same evidence type at different times. **Source comparison**: Different sources for same claim. |
| **Failure Paths** | Evidence incomparable: Explain dimension mismatch. |
| **Accessibility Behaviour** | Comparison view is `role="region"` with `aria-label="Evidence comparison"`. |
| **Motion Behaviour** | Comparison opens with SlideIn (300ms). Differences use Reveal (200ms). |
| **Attention Behaviour** | Evidence comparison switches to Focused state. |
| **Confidence Behaviour** | Each evidence item shows its confidence. AI's quality assessment shows confidence. |
| **Valid Composition** | Select(evidence[1]) → Select(evidence[2]) → Compare(view) → Inspect(conflict) → Suggest(assessment) → Select(evidence[1]) |
| **Invalid Composition** | Comparing evidence of completely different types without warning. AI dismissing evidence without showing reasoning. |

### 5.10 Build Context

| Field | Value |
|-------|-------|
| **Purpose** | Assemble relevant background information around a topic or object |
| **Applicable Situations** | User needs comprehensive understanding before making a decision |
| **Required Primitives** | Focus, Suggest, Explain, Navigate, Expand, Collapse, Search |
| **Composition Sequence** | 1. Focus (topic/object) → 2. Suggest (AI assembles context automatically) → 3. Explain (why these items are relevant) → 4. Expand (view an item) → 5. Navigate (to item for detail) → 6. Collapse (return to context) |
| **Entry Conditions** | A topic or object with related context is selected |
| **Exit Conditions** | User has reviewed the context or dismissed it |
| **Alternative Paths** | **Depth-adjustable context**: Show more or fewer related items. **Timeline context**: Show context organized by time. |
| **Failure Paths** | No context available: "This object has no related context yet." |
| **Accessibility Behaviour** | Context items are `role="list"`. Each is `role="listitem"` with `aria-label`. |
| **Motion Behaviour** | Context surfaces with Reveal (200ms) in the knowledge section. Items appear with Stagger (50ms). |
| **Attention Behaviour** | Context is built in Silent state (behind the scenes). Presented when user opens the knowledge section. |
| **Confidence Behaviour** | Context relevance shows confidence per item. |
| **Valid Composition** | Focus(object) → Suggest(context) → Explain(relevance) → Expand(item[2]) → Navigate(item[2]) → Collapse(back) |
| **Invalid Composition** | Building context the user did not ask for. Including irrelevant items in the context. |

---

## 6. Collaboration Patterns

### 6.1 Comment

| Field | Value |
|-------|-------|
| **Purpose** | Add a note or observation to an object for other users |
| **Applicable Situations** | User wants to share feedback, ask a question, or leave a note |
| **Required Primitives** | Focus, Confirm, Dismiss, Suggest |
| **Composition Sequence** | 1. Focus (comment field) → 2. Fill (comment text) → 3. Confirm (post) → 4. Suggest (notify relevant users) |
| **Entry Conditions** | User has something to say about the current object |
| **Exit Conditions** | Comment is posted and relevant parties are notified |
| **Alternative Paths** | **Inline comment**: Comment on a specific section or field. **Thread reply**: Reply to an existing comment. |
| **Failure Paths** | Comment too long: Show character count and limit. Network error: Save draft. |
| **Accessibility Behaviour** | Comment field is `role="textbox"`. Post button is `role="button"`. New comments are `aria-live="polite"`. |
| **Motion Behaviour** | New comment appears with Reveal (200ms). Threaded replies appear with Stagger (50ms per reply). |
| **Attention Behaviour** | Commenting switches to Focused state. Notification to others is deferred (queued). |
| **Valid Composition** | Focus(comment_field) → Fill(text) → Confirm(post) → Suggest(notification) |
| **Invalid Composition** | Posting empty comments. Allowing @mentions without autocomplete. |

### 6.2 Discuss

| Field | Value |
|-------|-------|
| **Purpose** | Conduct a threaded conversation around a topic or object |
| **Applicable Situations** | Multiple users need to collaborate on a decision or issue |
| **Required Primitives** | Focus, Suggest, Expand, Collapse, Navigate |
| **Composition Sequence** | 1. Focus (discussion thread) → 2. Expand (view full thread) → 3. Suggest (new reply or reaction) → 4. Fill (reply) → 5. Confirm (post) |
| **Entry Conditions** | An open discussion thread exists or user creates one |
| **Exit Conditions** | User posts a reply or closes the discussion |
| **Alternative Paths** | **Resolve discussion**: Mark discussion as resolved. **AI summarize discussion**: AI summarizes the key points and decisions. |
| **Failure Paths** | Thread too long: Paginate or collapse old messages. |
| **Accessibility Behaviour** | Thread is `role="list"`. Messages are `role="listitem"`. Reply is `role="textbox"`. |
| **Motion Behaviour** | Thread expands with Expand (300ms). New messages appear with Reveal (200ms). |
| **Attention Behaviour** | Discussion operates in Focused state when user is participating. Silently notifies when new messages arrive. |
| **Valid Composition** | Focus(thread) → Expand(full) → Suggest(reply) → Fill(text) → Confirm(post) |
| **Invalid Composition** | Discussing in a chat-like persistent window. Allowing discussions to block the object workspace. |

### 6.3 Mention

| Field | Value |
|-------|-------|
| **Purpose** | Direct another user's attention to a specific object, comment, or action |
| **Applicable Situations** | User needs to involve a specific person |
| **Required Primitives** | Focus, Select, Confirm, Suggest |
| **Composition Sequence** | 1. Focus (mention trigger) → 2. Select (user to mention) → 3. Confirm (add mention) → 4. Suggest (notify mentioned user) |
| **Entry Conditions** | User is composing a comment, description, or discussion post |
| **Exit Conditions** | Mention is added to the text |
| **Alternative Paths** | **Auto-mention**: System suggests relevant people based on context. **Group mention**: Mention a team or role. |
| **Failure Paths** | User not found: Show no results. |
| **Accessibility Behaviour** | Mention autocomplete is `role="listbox"` with `aria-activedescendant`. |
| **Motion Behaviour** | Mention panel appears with Appear (200ms) as user types @. |
| **Attention Behaviour** | Mention respects current attention state. |
| **Valid Composition** | Focus(comment) → Type("@") → Select(user) → Confirm(mention) → Suggest(notify) |
| **Invalid Composition** | Mentioning without autocomplete. Mentioning users not relevant to the context. |

### 6.4 Share

| Field | Value |
|-------|-------|
| **Purpose** | Grant another user access to view or interact with an object |
| **Applicable Situations** | User wants to collaborate by giving access to a specific object |
| **Required Primitives** | Focus, Select, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Focus (share action) → 2. Select (user or group) → 3. Select (access level) → 4. Explain (what the recipient will see) → 5. Confirm (share) |
| **Entry Conditions** | User has access to an object they want to share |
| **Exit Conditions** | Access is granted or sharing cancelled |
| **Alternative Paths** | **Link share**: Generate a shareable link. **Public share**: Make object publicly accessible (if permitted). |
| **Failure Paths** | Recipient lacks base access: Show "User cannot access this workspace." |
| **Accessibility Behaviour** | Share dialog is `role="dialog"` with `aria-label="Share"`. Access levels are `role="radio"`. |
| **Motion Behaviour** | Share dialog opens with Dialog (300ms). Confirmation shows toast (4s). |
| **Attention Behaviour** | Sharing respects current attention state. |
| **Valid Composition** | Focus(share) → Select("Jane Smith") → Select("Editor") → Explain(permissions) → Confirm(share) |
| **Invalid Composition** | Sharing without specifying access level. Sharing sensitive information without warning. |

### 6.5 Request Input

| Field | Value |
|-------|-------|
| **Purpose** | Solicit feedback, approval, or information from another user |
| **Applicable Situations** | User needs someone else's expertise or authority |
| **Required Primitives** | Focus, Select, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Focus (request action) → 2. Select (recipient) → 3. Fill (request details) → 4. Explain (context) → 5. Confirm (send request) |
| **Entry Conditions** | User needs input they cannot provide themselves |
| **Exit Conditions** | Request is sent, or cancelled |
| **Alternative Paths** | **AI-drafted request**: User provides brief → AI generates full request. **Structured request**: Form-based with specific fields. |
| **Failure Paths** | Recipient unavailable: Notify when recipient is available. |
| **Accessibility Behaviour** | Request form is `role="form"`. Send is `role="button"`. |
| **Motion Behaviour** | Request opens with SlideIn (300ms). Confirmation shows toast (4s). |
| **Attention Behaviour** | Request switches to Focused. |
| **Valid Composition** | Focus(request) → Select("CFO") → Fill("Please review budget increase") → Explain(context) → Confirm(send) |
| **Invalid Composition** | Requesting input without providing context. Requesting input from someone without relevant expertise. |

### 6.6 Resolve Conflict

| Field | Value |
|-------|-------|
| **Purpose** | Reconcile conflicting information, opinions, or decisions |
| **Applicable Situations** | Two or more sources or users disagree |
| **Required Primitives** | Focus, Compare, Suggest, Explain, Select, Confirm |
| **Composition Sequence** | 1. Focus (conflict) → 2. Compare (positions) → 3. Suggest (resolution options) → 4. Explain (pros/cons) → 5. Select (resolution) → 6. Confirm (apply) |
| **Entry Conditions** | A conflict has been identified |
| **Exit Conditions** | Conflict is resolved or escalated |
| **Alternative Paths** | **AI mediation**: AI suggests resolution with rationale. **Human escalation**: Escalate to a decision-maker. |
| **Failure Paths** | Irreconcilable: Escalate to highest authority. |
| **Accessibility Behaviour** | Conflict view is `role="region"` with `aria-label="Conflict resolution"`. |
| **Motion Behaviour** | Conflict appears with Reveal (300ms) in the AI Resident. Resolution applies with CrossFade (300ms). |
| **Attention Behaviour** | Conflict resolution switches to Focused. |
| **Confidence Behaviour** | Each position shows its evidence confidence. AI's suggestion shows confidence. |
| **Valid Composition** | Focus(conflict) → Compare(position_A, position_B) → Suggest(resolution) → Explain(rationale) → Select(A's position) → Confirm(resolve) |
| **Invalid Composition** | Resolving without showing both positions. AI resolving without human confirmation. |

### 6.7 Transfer Ownership

| Field | Value |
|-------|-------|
| **Purpose** | Change the owner of an object to another user |
| **Applicable Situations** | User is leaving a role, or another user is better suited to own the object |
| **Required Primitives** | Focus, Select, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (transfer action) → 2. Select (new owner) → 3. Explain (current state + pending actions) → 4. Confirm (transfer) |
| **Entry Conditions** | Current user is the owner of the object |
| **Exit Conditions** | Ownership is transferred or cancelled |
| **Alternative Paths** | **Bulk transfer**: Transfer multiple objects. **Auto-transfer**: On user departure, auto-transfer owned objects. |
| **Failure Paths** | New owner not accepting transfers: Show "User has transfers paused." |
| **Accessibility Behaviour** | Transfer form is `role="form"`. Confirmation is `role="alertdialog"`. |
| **Motion Behaviour** | Transfer opens with Dialog (300ms). On confirm, ownership badge updates with Reveal (200ms). |
| **Attention Behaviour** | Transfer switches to Focused. |
| **Valid Composition** | Focus(transfer) → Select("Mark Chen") → Explain(pending_tasks) → Confirm(transfer) |
| **Invalid Composition** | Transferring without informing the new owner. Transferring without documenting pending responsibilities. |

### 6.8 Observe

| Field | Value |
|-------|-------|
| **Purpose** | Watch an object or workspace for changes without actively participating |
| **Applicable Situations** | User wants to stay informed but is not directly responsible |
| **Required Primitives** | Focus, Select, Confirm, Dismiss, Suggest |
| **Composition Sequence** | 1. Focus (observe action) → 2. Select (object or workspace) → 3. Confirm (start observing) → 4. Suggest (notify on changes) |
| **Entry Conditions** | User wants to monitor an object without being responsible |
| **Exit Conditions** | User is observing the selected items |
| **Alternative Paths** | **Silent observe**: Observe without notifications (check periodically). **Active observe**: Receive change summaries. |
| **Failure Paths** | Already observing: Show "You are already observing this object." |
| **Accessibility Behaviour** | Observe toggle is `role="switch"` with `aria-checked`. |
| **Motion Behaviour** | Observe toggles with a brief Switch animation (150ms). |
| **Attention Behaviour** | Observation changes are delivered as summaries, not interrupts. |
| **Valid Composition** | Focus(object) → Select("Observe") → Confirm(start) → Suggest(summaries) |
| **Invalid Composition** | Observing without the object owner's awareness. |

### 6.9 Follow

| Field | Value |
|-------|-------|
| **Purpose** | Receive updates about an object's activity |
| **Applicable Situations** | User wants to be notified when an object changes |
| **Required Primitives** | Focus, Select, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (follow action) → 2. Select (notification preferences) → 3. Confirm (start following) |
| **Entry Conditions** | User wants change notifications for an object |
| **Exit Conditions** | User is following the object |
| **Alternative Paths** | **Smart follow**: AI determines optimal notification frequency. **Custom follow**: User sets specific triggers. |
| **Failure Paths** | Already following: Offer to update notification preferences. |
| **Accessibility Behaviour** | Follow toggle is `role="switch"` with `aria-checked`. |
| **Motion Behaviour** | Follow toggles with Switch (150ms). |
| **Attention Behaviour** | Follow notifications are summarized and delivered at natural attention points. |
| **Valid Composition** | Focus(object) → Select("Follow") → Confirm(start) → Dismiss |
| **Invalid Composition** | Following without offering notification preference configuration. |

### 6.10 Subscribe

| Field | Value |
|-------|-------|
| **Purpose** | Receive regular updates about a workspace, topic, or object type |
| **Applicable Situations** | User wants ongoing awareness without manual checking |
| **Required Primitives** | Focus, Select, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (subscribe action) → 2. Select (topic/workspace) → 3. Select (frequency) → 4. Confirm (subscribe) |
| **Entry Conditions** | User wants periodic updates |
| **Exit Conditions** | Subscription is active or cancelled |
| **Alternative Paths** | **Digest subscribe**: Receive periodic summaries. **Real-time subscribe**: Receive notifications on each change. |
| **Failure Paths** | Already subscribed: Update existing subscription. |
| **Accessibility Behaviour** | Subscribe form is `role="form"`. Frequency is `role="radiogroup"`. |
| **Motion Behaviour** | Subscribe panel opens with Appear (200ms). Confirmation shows toast (4s). |
| **Attention Behaviour** | Subscription deliveries are summarized and delivered at natural attention points. |
| **Valid Composition** | Focus(workspace) → Select("Subscribe") → Select("Weekly digest") → Confirm(subscribe) |
| **Invalid Composition** | Subscribing users to topics without confirmation. Delivering subscriptions at inappropriate times. |

---

## 7. AI Collaboration Patterns

### 7.1 AI Suggests

| Field | Value |
|-------|-------|
| **Purpose** | AI surfaces a recommendation for the user to consider |
| **Applicable Situations** | AI has identified an opportunity or issue with sufficient confidence |
| **Required Primitives** | Suggest, Explain, Focus, Select, Dismiss |
| **Composition Sequence** | 1. Suggest (AI generates recommendation) → 2. Explain (show reasoning on demand) → 3. Focus (user reviews) → 4. Select (accept) OR Dismiss OR Defer |
| **Entry Conditions** | Confidence > threshold (0.80 for proactive, any for on-demand) |
| **Exit Conditions** | User has accepted, dismissed, or deferred the suggestion |
| **Alternative Paths** | **Proactive suggest**: AI surfaces suggestion without user request. **On-demand suggest**: User asks for suggestions. |
| **Failure Paths** | No suggestions available: "I don't have any suggestions right now." |
| **Accessibility Behaviour** | Suggestion is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Suggestion appears in AI Resident with Reveal (200ms). Explanation expands with Expand (300ms). |
| **Attention Behaviour** | Proactive suggestion: Available only in Suggestive state. On-demand suggestion: Available in any state. |
| **Confidence Behaviour** | Always shown. Suggestion without confidence is not a valid state. |
| **Valid Composition** | Suggest(proposal) → Explain(why) → Focus(user) → Select(accept) |
| **Invalid Composition** | Suggesting without confidence. Suggesting the same thing after user dismissal. Auto-executing suggestions. |

### 7.2 Human Decides

| Field | Value |
|-------|-------|
| **Purpose** | The human makes the final decision after AI has provided input |
| **Applicable Situations** | Every decision point — AI never decides, always advises |
| **Required Primitives** | Focus, Select, Confirm, Explain, Suggest |
| **Composition Sequence** | 1. Suggest (AI presents options + analysis) → 2. Explain (reasoning per option) → 3. Focus (user evaluates) → 4. Select (user chooses) → 5. Confirm (user confirms choice) |
| **Entry Conditions** | A decision point has been reached |
| **Exit Conditions** | User has made and confirmed a decision |
| **Alternative Paths** | **Informed decide**: AI provides full analysis, user decides. **Quick decide**: User decides without AI input (always allowed). |
| **Failure Paths** | User defers: Save state, return to decision point later. |
| **Accessibility Behaviour** | Decision options are `role="listbox"`. Confirm is `role="button"`. |
| **Motion Behaviour** | AI analysis appears with Reveal (200ms). User selection updates with Select animation (200ms). Confirm shows brief progress. |
| **Attention Behaviour** | Decision point switches to Focused state. AI waits silently until user asks for analysis. |
| **Confidence Behaviour** | AI analysis per option shows confidence. User's choice does not carry confidence (human authority). |
| **Valid Composition** | Suggest(options) → Explain(analysis) → Focus(user) → Select(option_B) → Confirm(choice) |
| **Invalid Composition** | AI making a decision without user confirmation. AI hiding options that it considers inferior. |

### 7.3 AI Explains

| Field | Value |
|-------|-------|
| **Purpose** | AI reveals its reasoning, sources, and confidence for any assertion |
| **Applicable Situations** | Any AI assertion the user wants to understand better |
| **Required Primitives** | Explain, Unexplain, Focus, Inspect, Suggest |
| **Composition Sequence** | 1. Focus (AI assertion) → 2. Explain (show reasoning) → 3. Inspect (read explanation) → 4. Suggest (AI offers deeper analysis) → 5. Unexplain OR Keep |
| **Entry Conditions** | An AI assertion with explanation capability is visible |
| **Exit Conditions** | User has read the explanation or collapsed it |
| **Alternative Paths** | **Depth toggle**: Executive → Professional → Technical → Full evidence. **Source drill-down**: Click a source to open it. |
| **Failure Paths** | No explanation available: "Explanation tracking was not available when this assertion was made." |
| **Accessibility Behaviour** | Explanation is `role="region"` with `aria-live="polite"`. Sources are `role="link"`. |
| **Motion Behaviour** | Explanation expands with Expand (300ms). Depth toggle uses CrossFade (200ms). |
| **Attention Behaviour** | Explanation is user-initiated. System does not change state. |
| **Confidence Behaviour** | Per-source confidence shown. Overall confidence shown. |
| **Valid Composition** | Focus(assertion) → Explain(reasoning) → Inspect(sources) → Unexplain(Escape) |
| **Invalid Composition** | Explaining with more text than the original assertion. Showing explanation without sources. |

### 7.4 Human Questions

| Field | Value |
|-------|-------|
| **Purpose** | User asks AI for information, analysis, or recommendations |
| **Applicable Situations** | User wants to learn more or get AI's perspective |
| **Required Primitives** | Focus, Suggest, Explain, Search, Dismiss |
| **Composition Sequence** | 1. Focus (question input) → 2. Fill (question) → 3. Search (AI retrieves information) → 4. Suggest (AI formulates response) → 5. Explain (show reasoning on demand) → 6. Inspect (read response) |
| **Entry Conditions** | User has a question for the system |
| **Exit Conditions** | User has received an answer or dismissed the interaction |
| **Alternative Paths** | **Typed question**: User types a question. **Voice question**: User asks verbally (where supported). |
| **Failure Paths** | AI cannot answer: "I cannot answer that question. Here is what I do know about this topic." |
| **Accessibility Behaviour** | Question input is `role="textbox"` with `aria-label="Ask AI"`. |
| **Motion Behaviour** | Response appears fully formed after a deliberate pause (500-800ms). No typing or thinking indicators. |
| **Attention Behaviour** | Question/answer switches to Conversational state. |
| **Confidence Behaviour** | Every claim in the response carries confidence. Overall response confidence shown. |
| **Valid Composition** | Focus(question_input) → Fill("What evidence supports this?") → Suggest(response) → Explain(sources) → Inspect(response) |
| **Invalid Composition** | AI responding with false certainty. Showing "thinking" or "typing" indicators. |

### 7.5 AI Learns

| Field | Value |
|-------|-------|
| **Purpose** | AI updates its understanding based on user input or corrections |
| **Applicable Situations** | User corrects AI, provides new information, or demonstrates a preference |
| **Required Primitives** | Suggest, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. User provides correction → 2. Suggest (AI acknowledges) → 3. Explain (what was learned) → 4. Confirm (user acknowledges) OR Dismiss |
| **Entry Conditions** | User has provided information that conflicts with or adds to AI's knowledge |
| **Exit Conditions** | AI has recorded the learning or user dismissed it |
| **Alternative Paths** | **Implicit learn**: AI learns without announcement (usage patterns). **Explicit learn**: User says "Remember this" or corrects an assertion. |
| **Failure Paths** | Learning conflicts with policy: "I cannot learn this because it contradicts organizational policy." |
| **Accessibility Behaviour** | Learning acknowledgment is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | AI acknowledgment is minimal — inline text update or toast (4s). |
| **Attention Behaviour** | Learning acknowledgment is brief. Does not interrupt unless user is in Focused state. |
| **Confidence Behaviour** | Learned information starts at human confidence (1.0), decays over time. |
| **Valid Composition** | Suggest(correction_acknowledgment) → Explain(what_updated) → Confirm(ok) |
| **Invalid Composition** | Learning without user awareness. Debating the user's correction. |

### 7.6 AI Waits

| Field | Value |
|-------|-------|
| **Purpose** | AI deliberately does nothing — waiting is a valid action |
| **Applicable Situations** | User is focused, reading, or has not invited AI input |
| **Required Primitives** | _(none — this is the absence of primitives)_ |
| **Composition Sequence** | No sequence. AI observes but does not act. |
| **Entry Conditions** | User is in Silent, Focused, or Scanning state |
| **Exit Conditions** | User transitions to Available state, or confidence threshold is crossed |
| **Alternative Paths** | **Patient wait**: Wait indefinitely until user engages. **Timed wait**: Wait for a condition (confidence increase, state change). |
| **Failure Paths** | N/A — waiting cannot fail |
| **Accessibility Behaviour** | No ARIA changes during waiting. System is silent. |
| **Motion Behaviour** | No motion during waiting. Gold dot is steady (no animation). |
| **Attention Behaviour** | Waiting is the default behaviour in Silent, Focused, and Scanning states. |
| **Valid Composition** | _(no primitives)_ → AI waits |
| **Invalid Composition** | Suggesting, notifying, or interrupting during a wait state. |

### 7.7 AI Escalates

| Field | Value |
|-------|-------|
| **Purpose** | AI determines it cannot handle a request and routes it to a human |
| **Applicable Situations** | Request exceeds AI's capability, authority, or confidence threshold |
| **Required Primitives** | Suggest, Explain, Navigate, Confirm, Dismiss |
| **Composition Sequence** | 1. Suggest (AI: "I need to escalate this") → 2. Explain (why escalation is needed) → 3. Select (target) → 4. Confirm (escalate) |
| **Entry Conditions** | AI has determined it cannot or should not handle the request |
| **Exit Conditions** | Request is escalated to a human or user cancelled |
| **Alternative Paths** | **Auto-escalate**: AI routes to appropriate person without user action. **Suggested escalate**: AI recommends escalation, user confirms. |
| **Failure Paths** | No appropriate human available: Queue escalation, notify when available. |
| **Accessibility Behaviour** | Escalation is `role="dialog"` with `aria-label="Escalation"`. |
| **Motion Behaviour** | Escalation notice appears in AI Resident with Reveal (200ms). |
| **Attention Behaviour** | AI escalates in Suggestive or Conversational state only. |
| **Confidence Behaviour** | AI shows confidence in its determination that escalation is needed. |
| **Valid Composition** | Suggest(escalation_needed) → Explain(why) → Select(person) → Confirm(escalate) |
| **Invalid Composition** | Escalating without explaining why. Escalating to the wrong person. |

### 7.8 AI Requests Clarification

| Field | Value |
|-------|-------|
| **Purpose** | AI asks the user for more information when the request is ambiguous |
| **Applicable Situations** | User's input is ambiguous, incomplete, or has multiple interpretations |
| **Required Primitives** | Suggest, Explain, Focus, Select, Dismiss |
| **Composition Sequence** | 1. Suggest (AI: "I need clarification") → 2. Explain (what is ambiguous) → 3. Focus (user provides clarification) → 4. Select (user chooses or clarifies) |
| **Entry Conditions** | AI has received input that it cannot unambiguously interpret |
| **Exit Conditions** | User has provided clarification or cancelled the request |
| **Alternative Paths** | **Multiple choice**: AI presents possible interpretations, user selects. **Free text**: User types clarification. |
| **Failure Paths** | User refuses to clarify: "I cannot proceed without clarification. Please refine your request." |
| **Accessibility Behaviour** | Clarification options are `role="listbox"`. Free text is `role="textbox"`. |
| **Motion Behaviour** | Clarification request appears with Reveal (200ms) in the AI Resident. |
| **Attention Behaviour** | Clarification switches to Conversational state. |
| **Confidence Behaviour** | AI shows confidence in each possible interpretation. |
| **Valid Composition** | Suggest(clarification_request) → Explain(ambiguity) → Select(option_B) |
| **Invalid Composition** | Requesting clarification for perfectly clear input. Making assumptions instead of asking. |

### 7.9 AI Observes

| Field | Value |
|-------|-------|
| **Purpose** | AI monitors activity silently without taking action |
| **Applicable Situations** | User is working independently; AI is present but not participating |
| **Required Primitives** | _(none — passive observation)_ |
| **Composition Sequence** | No sequence. AI observes and stores information for potential future use. |
| **Entry Conditions** | User is engaged in activity within the workspace |
| **Exit Conditions** | AI detects a condition that warrants moving to another state (Suggesting, etc.) |
| **Alternative Paths** | **Focused observe**: User is in focused mode, AI observes without expectations. **Background observe**: AI performs background analysis while user works. |
| **Failure Paths** | N/A |
| **Accessibility Behaviour** | No ARIA changes during observation. |
| **Motion Behaviour** | Gold dot is steady (no animation) when AI is present but not active. |
| **Attention Behaviour** | AI Observes is the default behaviour alongside user activity. AI does not change attention state. |
| **Valid Composition** | _(no primitives)_ → AI observes while user works |
| **Invalid Composition** | AI claiming to observe while actually processing (thinking indicator). Announcing observations. |

### 7.10 AI Summarizes

| Field | Value |
|-------|-------|
| **Purpose** | AI condenses information or activity into a concise overview |
| **Applicable Situations** | User returns after absence, completes a phase of work, or requests a summary |
| **Required Primitives** | Suggest, Explain, Focus, Inspect, Dismiss |
| **Composition Sequence** | 1. Suggest (summary appears) → 2. Explain (key points with reasoning) → 3. Inspect (read summary) → 4. Dismiss OR Expand (for detail) |
| **Entry Conditions** | Sufficient activity or information exists to summarize |
| **Exit Conditions** | User has read and acted on the summary or dismissed it |
| **Alternative Paths** | **Periodic summary**: "Since your last visit" on return. **Activity summary**: After completing a task phase. **On-demand summary**: User requests a summary verbally or by clicking. |
| **Failure Paths** | Nothing to summarize: Stay silent. No summary generated. |
| **Accessibility Behaviour** | Summary is `role="region"` with `aria-label="Summary"`. |
| **Motion Behaviour** | Summary appears with Reveal (200ms) in the appropriate surface (Home workspace, AI Resident, or Executive Summary). |
| **Attention Behaviour** | Proactive summary appears in Suggestive state. On-demand summary available in any state. |
| **Confidence Behaviour** | Summary shows overall confidence. Low-confidence summaries are flagged. |
| **Valid Composition** | Suggest(summary) → Explain(key_points) → Inspect(details) → Dismiss |
| **Invalid Composition** | Summarizing when nothing has changed. Summarizing with low confidence without flagging it. |

---

## 8. Error & Recovery Patterns

### 8.1 Recover

| Field | Value |
|-------|-------|
| **Purpose** | Restore normal operation after a failure |
| **Applicable Situations** | Any system or user error has occurred |
| **Required Primitives** | Suggest, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. Suggest (error notification) → 2. Explain (what happened) → 3. Suggest (recovery option) → 4. Confirm (execute recovery) OR Dismiss |
| **Entry Conditions** | An error has occurred that can be recovered from |
| **Exit Conditions** | System is recovered or error is accepted |
| **Alternative Paths** | **Auto-recover**: System recovers silently and notifies after. **Manual recover**: User initiates recovery with guidance. |
| **Failure Paths** | Recovery fails: Show "Recovery was unsuccessful. Please contact support." |
| **Accessibility Behaviour** | Error notification is `role="alert"` with `aria-live="assertive"`. Recovery options are `role="button"`. |
| **Motion Behaviour** | Error appears inline (not as a popup) in the affected context. Recovery confirmation is brief. |
| **Attention Behaviour** | Error notification switches to Alerting state for critical errors. Non-critical errors are `aria-live="polite"`. |
| **Valid Composition** | Suggest(error) → Explain(what_happened) → Suggest(recovery) → Confirm(recover) |
| **Invalid Composition** | Showing error codes to non-admin users. Blaming the user for system errors. |

### 8.2 Retry

| Field | Value |
|-------|-------|
| **Purpose** | Attempt a failed operation again |
| **Applicable Situations** | A transient failure (network, timeout) that may succeed on retry |
| **Required Primitives** | Focus, Confirm, Dismiss, Suggest |
| **Composition Sequence** | 1. Suggest (failure notification) → 2. Explain (transient nature) → 3. Focus (retry button) → 4. Confirm (retry) OR Dismiss |
| **Entry Conditions** | An operation failed due to a potentially transient error |
| **Exit Conditions** | Operation succeeded on retry or user gave up |
| **Alternative Paths** | **Auto-retry**: System retries automatically with exponential backoff. **Manual retry**: User clicks retry. |
| **Failure Paths** | Retry also fails: Escalate to Recover pattern. |
| **Accessibility Behaviour** | Retry button is `role="button"` with `aria-label="Retry"`. |
| **Motion Behaviour** | Retry attempt shows a brief pulse on the retry button (no full-page spinner). |
| **Attention Behaviour** | Retry notification is polite. Does not force user to retry. |
| **Valid Composition** | Suggest(failure) → Explain("This might be a temporary issue") → Confirm(retry) |
| **Invalid Composition** | Auto-retrying without user knowledge. Retrying indefinitely without user consent. |

### 8.3 Rollback

| Field | Value |
|-------|-------|
| **Purpose** | Revert a set of changes to a previous known-good state |
| **Applicable Situations** | Changes have caused problems and need to be undone |
| **Required Primitives** | Focus, Explain, Confirm, Dismiss |
| **Composition Sequence** | 1. Focus (rollback action) → 2. Explain (what will be reverted) → 3. Select (rollback point) → 4. Confirm (execute rollback) |
| **Entry Conditions** | A previous stable state exists that can be restored |
| **Exit Conditions** | System is restored to the rollback point, or rollback cancelled |
| **Alternative Paths** | **Point-in-time rollback**: Revert to a specific timestamp. **Step rollback**: Undo one change at a time. |
| **Failure Paths** | Rollback conflicts with newer changes: Show conflicts and require resolution. |
| **Accessibility Behaviour** | Rollback confirmation is `role="alertdialog"` with `aria-describedby`. |
| **Motion Behaviour** | Rollback applies changes in reverse order (each step 200ms). Final state crossfades (300ms). |
| **Attention Behaviour** | Rollback switches to Focused state. |
| **Valid Composition** | Focus(rollback) → Explain(effects) → Select(point) → Confirm(rollback) |
| **Invalid Composition** | Rolling back without showing what will be affected. Allowing rollback without confirmation. |

### 8.4 Resume

| Field | Value |
|-------|-------|
| **Purpose** | Continue a paused or interrupted workflow from where it stopped |
| **Applicable Situations** | User was in the middle of a workflow and was interrupted |
| **Required Primitives** | Focus, Suggest, Inspect, Navigate, Dismiss |
| **Composition Sequence** | 1. Suggest (resume prompt) → 2. Inspect (show last state) → 3. Navigate (to where user was) OR Dismiss (start fresh) |
| **Entry Conditions** | An interrupted workflow exists with saved state |
| **Exit Conditions** | User resumes the workflow or starts fresh |
| **Alternative Paths** | **Auto-resume**: System restores exact state on workspace open. **Manual resume**: User clicks "Resume where I left off." |
| **Failure Paths** | State corrupted: Show "Could not restore previous state. Starting fresh." |
| **Accessibility Behaviour** | Resume prompt is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | State restoration uses workspace-enter (400ms) to the exact position. |
| **Attention Behaviour** | Resume prompt appears in Suggestive state. User can ignore it. |
| **Valid Composition** | Suggest(resume) → Inspect(last_state) → Navigate(previous_position) |
| **Invalid Composition** | Resuming without showing what state will be restored. Auto-resuming to a stale state without user awareness. |

### 8.5 Cancel

| Field | Value |
|-------|-------|
| **Purpose** | Stop a pending or in-progress operation |
| **Applicable Situations** | User started an operation and wants to abort it |
| **Required Primitives** | Focus, Confirm, Explain, Dismiss |
| **Composition Sequence** | 1. Focus (cancel action) → 2. Explain (what will be discarded) → 3. Confirm (cancel) OR Dismiss (continue) |
| **Entry Conditions** | An in-progress or pending operation exists |
| **Exit Conditions** | Operation is cancelled or continues |
| **Alternative Paths** | **Cleanup cancel**: Cancel with automatic cleanup of partial changes. **Force cancel**: Cancel immediately, partial changes may remain. |
| **Failure Paths** | Cannot cancel: Operation is past the point of no return. Explain why. |
| **Accessibility Behaviour** | Cancel is `role="button"`. Confirmation is `role="alertdialog"` for destructive cancellations. |
| **Motion Behaviour** | Cancellation is instant for pending operations. In-progress operations show a brief progress completion (200ms). |
| **Attention Behaviour** | Cancel respects current attention state. |
| **Valid Composition** | Focus(cancel) → Explain("Draft will be discarded") → Confirm(cancel) |
| **Invalid Composition** | Cancelling without warning about data loss. Making cancel difficult to find or use. |

### 8.6 Repair

| Field | Value |
|-------|-------|
| **Purpose** | Fix a data inconsistency or integrity issue |
| **Applicable Situations** | Data has become inconsistent or corrupted |
| **Required Primitives** | Focus, Explain, Suggest, Confirm, Dismiss |
| **Composition Sequence** | 1. Suggest (issue detected) → 2. Explain (what is wrong) → 3. Suggest (repair options) → 4. Select (repair method) → 5. Confirm (execute repair) |
| **Entry Conditions** | An inconsistency has been detected in the data |
| **Exit Conditions** | Data is repaired or accepted as-is |
| **Alternative Paths** | **Auto-repair**: System repairs silently with log entry. **Guided repair**: User walks through repair steps. |
| **Failure Paths** | Repair impossible: Explain why and offer to escalate. |
| **Accessibility Behaviour** | Repair notification is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Repair progress is shown (linear indicator, width changes instantly). On completion, data re-renders (CrossFade 300ms). |
| **Attention Behaviour** | Repair notification is polite for non-critical issues. Critical inconsistencies switch to Alerting. |
| **Valid Composition** | Suggest(issue) → Explain(problem) → Suggest(repair_options) → Select(auto_repair) → Confirm(repair) |
| **Invalid Composition** | Repairing without user knowledge. Repairing critical data without audit trail. |

### 8.7 Clarify

| Field | Value |
|-------|-------|
| **Purpose** | Resolve ambiguity in user input or system state |
| **Applicable Situations** | User's intent is unclear; multiple interpretations exist |
| **Required Primitives** | Suggest, Explain, Focus, Select, Dismiss |
| **Composition Sequence** | 1. Suggest (ambiguity notice) → 2. Explain (what is ambiguous) → 3. Focus (user reviews options) → 4. Select (user chooses) OR Fill (user clarifies) |
| **Entry Conditions** | An ambiguous situation has been detected |
| **Exit Conditions** | Ambiguity is resolved or the operation is cancelled |
| **Alternative Paths** | **Structured clarify**: Multiple choice options. **Free-form clarify**: User types clarification. |
| **Failure Paths** | User cannot clarify: "I cannot proceed without resolving this ambiguity." |
| **Accessibility Behaviour** | Clarification options are `role="listbox"`. Input is `role="textbox"`. |
| **Motion Behaviour** | Clarification request appears inline with Reveal (200ms). |
| **Attention Behaviour** | Clarification switches to Focused state. |
| **Valid Composition** | Suggest(ambiguous) → Explain(interpretations) → Select(option_B) |
| **Invalid Composition** | Assuming user intent instead of clarifying. Making the clarification process more complex than the original action. |

### 8.8 Resolve Ambiguity

| Field | Value |
|-------|-------|
| **Purpose** | Systematically eliminate ambiguity through multiple clarifications |
| **Applicable Situations** | A single clarification is insufficient; multiple ambiguities exist |
| **Required Primitives** | Suggest, Explain, Focus, Select, Dismiss, Navigate |
| **Composition Sequence** | 1. Suggest (ambiguity chain) → 2. Focus (ambiguity 1) → 3. Select (resolution 1) → 4. Focus (ambiguity 2) → 5. Select (resolution 2) → ... → 6. Navigate (to resolved state) |
| **Entry Conditions** | Multiple ambiguous points need sequential resolution |
| **Exit Conditions** | All ambiguities are resolved or the process is cancelled |
| **Alternative Paths** | **Wizard resolve**: Step-by-step resolution with progress indicator. **Batch resolve**: Resolve all ambiguities in one screen. |
| **Failure Paths** | User cannot resolve any ambiguity: Full cancellation. |
| **Accessibility Behaviour** | Resolution wizard is `role="form"` with progress `role="progressbar"`. |
| **Motion Behaviour** | Each step reveals with CrossFade (200ms). Progress bar updates (width, no animation). |
| **Attention Behaviour** | Resolution switches to Focused state. |
| **Valid Composition** | Suggest(ambiguities) → Focus(q1) → Select(answer1) → Focus(q2) → Select(answer2) → Navigate(resolved_state) |
| **Invalid Composition** | Asking the same question twice. Presenting ambiguities out of logical order. |

### 8.9 Graceful Failure

| Field | Value |
|-------|-------|
| **Purpose** | Fail in a way that preserves user data, context, and trust |
| **Applicable Situations** | Any unavoidable failure |
| **Required Primitives** | Suggest, Explain, Dismiss, Confirm |
| **Composition Sequence** | 1. Suggest (failure notice) → 2. Explain (what was lost and what was preserved) → 3. Confirm (user acknowledges) OR Dismiss |
| **Entry Conditions** | A failure has occurred that cannot be fully recovered from |
| **Exit Conditions** | User has acknowledged the failure and can continue working |
| **Alternative Paths** | **Transparent failure**: Full explanation of what went wrong. **Minimal failure**: Brief notice, user continues. |
| **Failure Paths** | N/A — this is the failure handler. |
| **Accessibility Behaviour** | Failure notification is `role="alert"` with `aria-live="assertive"` for critical failures, `polite` for non-critical. |
| **Motion Behaviour** | Failure notification appears inline in the affected context. No dramatic animations. |
| **Attention Behaviour** | Critical failures switch to Alerting briefly, then return to previous state. Non-critical failures are polite. |
| **Confidence Behaviour** | System shows confidence in its assessment of what was preserved. |
| **Valid Composition** | Suggest(failure) → Explain(saved_state) → Confirm(acknowledge) → Resume(working) |
| **Invalid Composition** | Technical error messages. Blaming the user. Hiding the extent of data loss. |

### 8.10 Background Recovery

| Field | Value |
|-------|-------|
| **Purpose** | Recover from a failure without interrupting the user's workflow |
| **Applicable Situations** | Non-critical failure that can be resolved in the background |
| **Required Primitives** | Suggest, Explain, Dismiss |
| **Composition Sequence** | 1. Suggest (background recovery started) → 2. Explain (what is being recovered) → 3. Dismiss (user continues working) → 4. Suggest (recovery complete) |
| **Entry Conditions** | A non-critical failure has occurred that can be resolved asynchronously |
| **Exit Conditions** | Recovery is complete or failed |
| **Alternative Paths** | **Silent recovery**: Recover without user notification. **Notified recovery**: Brief notification on start and completion. |
| **Failure Paths** | Background recovery fails: Surface to user with Graceful Failure pattern. |
| **Accessibility Behaviour** | Recovery status is `role="status"` with `aria-live="polite"`. |
| **Motion Behaviour** | Recovery runs silently. Completion notification is a brief toast (4s). |
| **Attention Behaviour** | Recovery runs in background (user remains in current state). Completion notification is polite. |
| **Valid Composition** | Suggest(recovery_started) → Explain(scope) → Dismiss(continue) → Suggest(completed) |
| **Invalid Composition** | Claiming background recovery when user interaction is required. Failing silently without the user ever knowing. |

---

## 9. Multi-Object Patterns

### 9.1 Compare Multiple Objects

| Field | Value |
|-------|-------|
| **Purpose** | Analyze differences and similarities across several objects |
| **Applicable Situations** | User needs to make a selection from multiple candidates |
| **Required Primitives** | Select, Compare, Uncompare, Focus, Inspect, Suggest, Explain |
| **Composition Sequence** | 1. Select (objects A, B, C) → 2. Compare (table view) → 3. Inspect (column details) → 4. Suggest (AI highlights key differences) → 5. Explain (AI reasoning) → 6. Select (preferred) → 7. Navigate (to selected) |
| **Entry Conditions** | Multiple objects are available for selection |
| **Exit Conditions** | User has selected one or exited the comparison |
| **Alternative Paths** | **Grid compare**: Visual comparison with cards. **Table compare**: Attribute-by-attribute table. **AI compare**: AI generates comparison narrative. |
| **Failure Paths** | Objects incomparable: Explain why they cannot be compared. |
| **Accessibility Behaviour** | Comparison table is `role="table"` with `role="columnheader"` and `role="row"`. |
| **Motion Behaviour** | Table appears with SlideIn (300ms). Rows appear with Stagger (30ms each). |
| **Attention Behaviour** | Multi-object comparison switches to Focused state. |
| **Confidence Behaviour** | AI comparison suggestions show confidence per attribute. |
| **Valid Composition** | Select(A, B, C) → Compare(table) → Inspect(row) → Suggest(diffs) → Select(B) → Navigate(B) |
| **Invalid Composition** | Comparing unrelated objects. Comparing 10+ objects without offering AI summarization. |

### 9.2 Merge Context

| Field | Value |
|-------|-------|
| **Purpose** | Combine information from multiple objects into a unified view |
| **Applicable Situations** | User needs a comprehensive view that spans multiple objects |
| **Required Primitives** | Select, Navigate, Compare, Suggest, Explain, Expand, Collapse |
| **Composition Sequence** | 1. Select (objects to merge) → 2. Compare (context view) → 3. Suggest (AI identifies overlaps and gaps) → 4. Expand (view combined details) → 5. Navigate (to merged view) |
| **Entry Conditions** | Multiple related objects contain information that should be viewed together |
| **Exit Conditions** | User has the merged context view or cancelled |
| **Alternative Paths** | **Temporal merge**: Combine objects across time. **Relational merge**: Combine related objects. |
| **Failure Paths** | Context conflict: Highlight contradictory information. |
| **Accessibility Behaviour** | Merged context is `role="region"` with `aria-label="Merged context"`. |
| **Motion Behaviour** | Context merges with CrossFade (300ms). Overlaps/gaps highlight with Reveal (200ms). |
| **Attention Behaviour** | Context merge switches to Focused. |
| **Confidence Behaviour** | AI's overlap/gap detection shows confidence. |
| **Valid Composition** | Select(obj_A, obj_B) → Compare(context) → Suggest(overlaps) → Expand(combined) → Navigate(merged) |
| **Invalid Composition** | Merging without showing the source of each piece of information. Overwriting conflicting data without flagging it. |

### 9.3 Cross-Reference

| Field | Value |
|-------|-------|
| **Purpose** | Verify information consistency across multiple sources |
| **Applicable Situations** | User needs to ensure data is consistent across objects |
| **Required Primitives** | Focus, Search, Compare, Suggest, Explain, Navigate |
| **Composition Sequence** | 1. Focus (field or fact) → 2. Search (for same field in other objects) → 3. Compare (values) → 4. Suggest (AI flags inconsistencies) → 5. Explain (detail) → 6. Navigate (to source) |
| **Entry Conditions** | A field or fact exists that should be consistent across objects |
| **Exit Conditions** | User has verified consistency or identified discrepancies |
| **Alternative Paths** | **Auto cross-reference**: System periodically checks consistency. **On-demand cross-reference**: User triggers verification. |
| **Failure Paths** | No references found: "No other objects contain this field." |
| **Accessibility Behaviour** | Cross-reference results are `role="list"` with `aria-label="Cross-reference results"`. |
| **Motion Behaviour** | Results appear with Reveal (200ms). Inconsistencies highlight with subtle pulse (1.5s, then steady). |
| **Attention Behaviour** | Cross-reference switches to Focused. |
| **Confidence Behaviour** | Consistency confidence shown per field pair. |
| **Valid Composition** | Focus(field) → Search(matches) → Compare(values) → Suggest(inconsistency) → Explain(detail) → Navigate(source) |
| **Invalid Composition** | Cross-referencing without source attribution. Flagging inconsistencies without offering to resolve them. |

### 9.4 Relationship Exploration

| Field | Value |
|-------|-------|
| **Purpose** | Navigate the relationship graph to discover connections |
| **Applicable Situations** | User wants to understand how objects are connected |
| **Required Primitives** | Focus, Navigate, Inspect, Expand, Collapse, Suggest |
| **Composition Sequence** | 1. Focus (node) → 2. Expand (show connections) → 3. Inspect (connected node) → 4. Navigate (to connected node) → 5. Suggest (AI suggests notable paths) |
| **Entry Conditions** | A relationship graph or tree is visible |
| **Exit Conditions** | User has explored the desired connections or exited |
| **Alternative Paths** | **Graph exploration**: Free-form graph navigation. **Tree exploration**: Hierarchical navigation. **Path exploration**: Find path between two nodes. |
| **Failure Paths** | No connections: Empty graph. |
| **Accessibility Behaviour** | Graph is `role="tree"`. Nodes are `role="treeitem"` with `aria-expanded`. |
| **Motion Behaviour** | Node expansion uses Expand (300ms). Navigation between nodes uses Navigate (300ms). |
| **Attention Behaviour** | Exploration operates in Attentive state. AI may Suggest when user pauses on a node. |
| **Valid Composition** | Focus(node_A) → Expand(connections) → Inspect(node_B) → Navigate(node_B) → Suggest(path_insight) |
| **Invalid Composition** | Exploring without preserving the breadcrumb trail. Suggesting connections that don't exist. |

### 9.5 Timeline Navigation

| Field | Value |
|-------|-------|
| **Purpose** | Move through an object's chronological history |
| **Applicable Situations** | User needs to understand how an object evolved over time |
| **Required Primitives** | Focus, Inspect, Navigate, Expand, Collapse, Suggest |
| **Composition Sequence** | 1. Focus (timeline) → 2. Inspect (event) → 3. Expand (event details) → 4. Navigate (to a past version) → 5. Suggest (AI highlights trends) |
| **Entry Conditions** | An object with a recorded history exists |
| **Exit Conditions** | User has reviewed the desired events or exited |
| **Alternative Paths** | **Zoom navigation**: Zoom in/out by time scale. **Filter navigation**: Filter events by type. |
| **Failure Paths** | No timeline events: Empty timeline. |
| **Accessibility Behaviour** | Timeline is `role="list"`. Events are `role="listitem"`. |
| **Motion Behaviour** | Events appear with Stagger (50ms). Navigation between time periods uses CrossFade (200ms). |
| **Attention Behaviour** | Timeline navigation switches to Focused. |
| **Confidence Behaviour** | AI trend detection shows confidence. |
| **Valid Composition** | Focus(timeline) → Inspect(event[3]) → Expand(details) → Navigate(version) → Suggest(trend) |
| **Invalid Composition** | Navigating to a version without showing what changed. Hiding events from the timeline. |

### 9.6 Evidence Navigation

| Field | Value |
|-------|-------|
| **Purpose** | Move through a chain of evidence supporting a claim or decision |
| **Applicable Situations** | User needs to understand the evidence trail |
| **Required Primitives** | Focus, Navigate, Inspect, Expand, Collapse, Explain |
| **Composition Sequence** | 1. Focus (evidence chain) → 2. Inspect (piece of evidence) → 3. Expand (source details) → 4. Navigate (to source) → 5. Explain (relevance) |
| **Entry Conditions** | A claim or decision with supporting evidence exists |
| **Exit Conditions** | User has reviewed the evidence chain or exited |
| **Alternative Paths** | **Forward navigation**: From claim to evidence sources. **Backward navigation**: From evidence to claims it supports. |
| **Failure Paths** | Evidence gap: Missing link in the chain. |
| **Accessibility Behaviour** | Evidence chain is `role="list"`. Each evidence item is `role="listitem"`. |
| **Motion Behaviour** | Evidence items appear with Reveal (200ms). Source navigation uses Navigate (300ms). |
| **Attention Behaviour** | Evidence navigation switches to Focused. |
| **Confidence Behaviour** | Per-evidence confidence shown. Chain confidence is minimum of all evidence confidences. |
| **Valid Composition** | Focus(claim) → Inspect(evidence[1]) → Expand(source) → Navigate(source) → Explain(relevance) |
| **Invalid Composition** | Skipping evidence items. Showing evidence without confidence. |

### 9.7 Knowledge Graph Traversal

| Field | Value |
|-------|-------|
| **Purpose** | Navigate the interconnected knowledge graph to discover related concepts |
| **Applicable Situations** | User wants to explore the knowledge structure or find unexpected connections |
| **Required Primitives** | Focus, Navigate, Inspect, Expand, Collapse, Suggest, Explain |
| **Composition Sequence** | 1. Focus (knowledge node) → 2. Expand (related nodes) → 3. Inspect (connected knowledge) → 4. Navigate (to related node) → 5. Suggest (AI: "You might also want to see...") |
| **Entry Conditions** | A knowledge graph or browseable knowledge structure exists |
| **Exit Conditions** | User has explored the desired knowledge or exited |
| **Alternative Paths** | **Semantic traversal**: Follow meaning-based connections. **Tag traversal**: Follow tag-based connections. |
| **Failure Paths** | Dead end: No further connections. |
| **Accessibility Behaviour** | Knowledge graph is `role="tree"`. Nodes are `role="treeitem"`. |
| **Motion Behaviour** | Node expansion uses Expand (300ms). Navigation uses Navigate (300ms). |
| **Attention Behaviour** | Traversal operates in Scanning state. AI may Suggest when user pauses. |
| **Valid Composition** | Focus(knowledge_A) → Expand(related) → Inspect(knowledge_B) → Navigate(knowledge_B) → Suggest(connection) |
| **Invalid Composition** | Suggesting connections the user has already seen. Navigating without preserving the exploration path. |

---

## 10. Pattern Composition Rules

### 10.1 Composition Hierarchy

```
Workflow
  └─ Pattern
       ├─ Pattern (sub-pattern)
       │    └─ Primitive
       └─ Primitive
```

| Rule | Description |
|------|-------------|
| **Patterns compose patterns** | A pattern may use other patterns as steps. E.g., Review may call Explain, Compare, and Navigate as sub-patterns. |
| **Patterns compose primitives** | A pattern may use primitives directly for atomic steps. |
| **Patterns never bypass primitives** | Every pattern step, whether calling another pattern or a primitive, must trace to at least one interaction primitive. |
| **No cyclic composition** | Pattern A may not (directly or transitively) depend on Pattern B which depends on Pattern A. |
| **Deterministic execution** | Given the same inputs and conditions, a pattern always produces the same sequence of primitives and sub-patterns. |
| **Inheritance** | Patterns inherit accessibility, motion, and attention behaviour from their constituent primitives/patterns. Overrides must be explicitly documented. |
| **Pattern entry always requires user intent** | No pattern may begin execution without explicit or strongly implied user intent. AI-initiated patterns require Suggestive or higher attention state. |

### 10.2 Pattern Invocation

```
Review(decision_42)
  ├─ Navigate(decision_42)              // primitive: Navigate
  ├─ Inspect(summary)                   // primitive: Inspect
  ├─ Expand(evidence)                    // primitive: Expand
  ├─ Explain(AI_reasoning)              // primitive: Explain
  └─ Approve()                          // sub-pattern: Approve
       ├─ Focus(approve_btn)            // primitive: Focus
       ├─ Suggest(effects)              // primitive: Suggest
       ├─ Explain(post_approval)        // primitive: Explain
       └─ Confirm(approval)             // primitive: Confirm
```

### 10.3 Pattern Compatibility

| Pattern | Can Contain | Cannot Contain |
|---------|-------------|----------------|
| Search | Browse, Inspect, Preview, Filter, Sort | Create, Merge, Split |
| Create | Draft, Capture, Import, Duplicate | Search, Browse, Compare |
| Review | Explain, Compare, Navigate, Inspect | Create, Merge, Split |
| Approve | Explain, Confirm | Create, Search |
| AI Suggests | Explain, Search | Confirm (AI never confirms) |
| Human Decides | Select, Confirm | Suggest (AI does not decide) |

---

## 11. Pattern Governance

### 11.1 Pattern Lifecycle

```
Proposed → Draft → Reviewed → Published → Deprecated → Removed
```

| Stage | Criteria | Duration |
|-------|----------|----------|
| **Proposed** | Pattern has name, purpose, and uses at least 3 primitives | — |
| **Draft** | Full template completed, reviewed by at least one implementer | — |
| **Reviewed** | Passed architectural review against Interaction Language primitives | — |
| **Published** | Available for use in all SHUNYA applications | Indefinite |
| **Deprecated** | Replaced by a newer pattern or no longer aligns with principles | 2 release cycles |
| **Removed** | Deleted from the library. Migration guide published. | After deprecation period |

### 11.2 How New Patterns Are Proposed

1. Identify a recurring interaction sequence that is not covered by existing patterns.
2. Verify the sequence cannot be composed from existing patterns alone.
3. Complete the Pattern Template for the proposed pattern.
4. Submit for architectural review with evidence of:
   - At least 3 distinct applications across different domains
   - No new primitives required
   - Full template documentation
5. Upon approval, the pattern is published as Draft.
6. After 2 successful implementations, the pattern moves to Published.

### 11.3 How Patterns Evolve

| Action | Process |
|--------|---------|
| **Minor change** (add optional step) | Version bump (e.g., 1.0 → 1.1). No deprecation. |
| **Major change** (change required steps) | New major version. Old version deprecated (2 release cycles). |
| **Split** (one pattern becomes two) | Both new patterns proposed. Old pattern deprecated. |
| **Merge** (two patterns become one) | New pattern proposed that encompasses both. Both old patterns deprecated. |

### 11.4 How Deprecated Patterns Are Handled

- Deprecated patterns remain in the library with a `(deprecated)` label.
- New implementations must not use deprecated patterns.
- Existing implementations using deprecated patterns are not required to migrate immediately.
- Migration guide is provided for each deprecated pattern pointing to the replacement.
- After the deprecation period, the pattern is removed from the library.

### 11.5 Compatibility Maintainance

| Rule | Description |
|------|-------------|
| **Backward compatibility** | Published patterns maintain their template interface across minor versions. |
| **Forward compatibility** | New patterns must not break existing compositions that use older patterns. |
| **Pattern composition stability** | If Pattern A uses Pattern B, and Pattern B is deprecated, Pattern A must be updated before Pattern B is removed. |

### 11.6 How Patterns Inherit Future Improvements

- When a primitive is improved (e.g., better accessibility), all patterns using that primitive automatically inherit the improvement.
- When a sub-pattern is improved, all parent patterns automatically inherit the improvement.
- When a pattern is improved, all future compositions benefit. Existing compositions may optionally adopt.
- The interaction framework enforces automatic inheritance at the primitive level. Pattern-level inheritance is manual.

---

## 12. Validation

### 12.1 Business-Agnostic Verification

Every pattern has been validated against the following domains. The validation confirms that no pattern embeds domain-specific assumptions:

| Domain | Verification Result |
|--------|-------------------|
| CRM | All patterns function with contacts, accounts, leads, opportunities |
| ERP | All patterns function with orders, inventory, suppliers, invoices |
| Healthcare | All patterns function with patients, diagnoses, treatments, providers |
| Education | All patterns function with students, courses, enrollments, grades |
| Finance | All patterns function with accounts, transactions, instruments, portfolios |
| Legal | All patterns function with cases, clients, documents, filings |
| Manufacturing | All patterns function with BOMs, work orders, batches, quality checks |
| Hospitality | All patterns function with bookings, guests, rooms, services |
| Travel | All patterns function with itineraries, bookings, destinations, travelers |
| Government | All patterns function with permits, citizens, services, regulations |
| Knowledge Management | All patterns function with articles, categories, tags, versions |
| Technology | All patterns function with projects, sprints, issues, releases |

**Conclusion:** All patterns are domain-independent. Object type names like "Patient" or "Account" are configuration, not pattern architecture.

### 12.2 Primitive Traceability

Every pattern has been audited to confirm that:

| Rule | Verification |
|------|-------------|
| All pattern steps trace to documented primitives | ✓ 100% of pattern steps in this library trace to one or more of the 21 Interaction Language primitives |
| No pattern invents new primitives | ✓ Zero new primitives were created for this library |
| No pattern bypasses the primitive layer | ✓ Every "pattern composes pattern" chain terminates in primitives |
| Pattern names use standard vocabulary | ✓ All pattern names are from the standard English vocabulary defined in the Interaction Language |

### 12.3 Prototype Interaction Mapping

Every interaction in the Phase X2 prototype maps to one or more documented patterns:

| Prototype Interaction | Pattern |
|----------------------|---------|
| Click workspace icon | Navigate (workspace) |
| Click object in list | Browse → Inspect → Navigate (object) |
| Click search → type → select result | Search → Inspect → Navigate |
| Ctrl+K → type → select command | Search (command mode) → Navigate |
| Hover card for summary | Inspect → Preview |
| Click section tab | Navigate (section) |
| Click relationship in list | Relationship Exploration → Navigate |
| Read executive summary | Review (summary phase) |
| Click "Why?" on confidence | AI Explains |
| AI Resident suggestions | AI Suggests → Human Decides |
| Click approve/reject | Approve / Reject |
| Back button / Ctrl+[ | Navigate (history back) |
| Dark/light toggle | _(theme change — not an interaction pattern)_ |
| Toast notification | NotificationSurface (primitive, not a pattern) |

**No prototype interaction requires an undocumented pattern.**

---

## Canonical Status

This Interaction Pattern Library, together with the Interaction Language (15) and Design System Foundation (16), forms the complete reusable layer between philosophy and production frontend engineering.

Every future SHUNYA workflow must be assembled from these patterns.
No new interaction behaviour should be invented at the application level.
All patterns are business-agnostic and domain-independent.

The canonical path from philosophy to implementation:

```
Human Principles (14)
  → Presence Canon (13)
    → Experience Canon (01-12)
      → Interaction Language (15)
        → Design System Foundation (16)
          → Interaction Pattern Library (17)  ← You are here
            → Production Frontend Implementation
```

---

*Canonical reference — Phase X2B. July 2026.*