# Cursor Merge Report — {VERSION}

> **You decide what ships.** This report records your choices per feature. Scripts only help inventory Cursor files — they do not select what to merge.

**Workflow graph:** [CURSOR_MERGE_WORKFLOW.md](../CURSOR_MERGE_WORKFLOW.md) | **Build:** [BUILD.md](../BUILD.md) | **Features:** [FEATURES.md](../FEATURES.md)

## Metadata

| Field | Value |
|-------|-------|
| Cursor version | {VERSION} |
| VS Code base | _(from manifest `source.vscodeVersion`)_ |
| VS Code commit | _(from manifest `source.vscodeCommit`)_ |
| Branch | `Cursor-merge-{VERSION}` |
| Started | YYYY-MM-DD |
| Completed | _(fill on sign-off)_ |
| Status | `in_progress` |

## User goals (fill first)

_What do you want from this Cursor release? What is explicitly out of scope?_

- **Goals:**
- **Out of scope:**
- **Notes:**

## Changelog (paste from cursor.com/changelog)

_Paste release notes for Cursor {VERSION} here._

-

## Manifest diff (optional inventory)

_Lists file/component deltas only — not merge recommendations._

```powershell
.\scripts\cursor-merge\diff-manifests.ps1 `
  -Old cursor\extracted\{PREVIOUS_VERSION}\COMPONENT_MANIFEST.json `
  -New cursor\extracted\{VERSION}\COMPONENT_MANIFEST.json `
  -OutputPath docs\merges\{VERSION}\manifest-diff.txt
```

_Summary:_

_(paste or summarize manifest-diff.txt)_

## Feature decisions

_For each changelog item or component you care about, record **your** decision before implementing._

| Item | Cursor path | Void target (if any) | Decision | Rationale | Approach (if adapt) |
|------|-------------|----------------------|----------|-----------|---------------------|
| | | | `defer` | | |

**Decision:** `implement` | `adapt` | `ignore` | `defer`

- `implement` — port into Void (TypeScript re-implementation)
- `adapt` — port the idea with Void-specific changes (describe in Approach)
- `ignore` — do not port this release
- `defer` — revisit later

Only `implement` and `adapt` rows proceed to implementation.

## Implementation

_Only for items marked `implement` or `adapt`._

### _(feature name)_

- **Decision:** implement | adapt
- **Void files:**
- **Notes:**

## Validation

_Validate only what you decided to ship._

### Build

- [ ] `npm run watch` — 0 errors
- [ ] `npm run buildreact` — if UI touched
- [ ] `scripts\code.bat` — app launches

### Manual QA

| Check | Applies to | Pass | Notes |
|-------|------------|------|-------|
| Chat sidebar (Ctrl+L) | regression | | |
| Quick Edit (Ctrl+K) | regression | | |
| Autocomplete | regression | | |
| Apply / diffs | regression | | |
| Agent tools | regression | | |
| MCP | regression | | |
| Settings | regression | | |
| _(decided feature)_ | implement/adapt | | |

## Sign-off

- [ ] Every changelog/component of interest has an explicit decision
- [ ] All `implement` / `adapt` items implemented and validated
- [ ] All `ignore` / `defer` items documented with rationale
- [ ] [FEATURES.md](../FEATURES.md) updated for what actually shipped
- [ ] PR opened: `Cursor-merge-{VERSION}` → `main`

**Conclusion:** _(what was implemented, adapted, ignored, deferred)_
