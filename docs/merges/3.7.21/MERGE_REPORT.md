# Cursor Merge Report — 3.7.21

> **You decide what ships.** Fill feature decisions before implementation. Scripts inventory files only.

## Metadata

| Field | Value |
|-------|-------|
| Cursor version | 3.7.21 |
| VS Code base | 1.105.1 _(confirm after extraction)_ |
| VS Code commit | _(from `cursor/extracted/3.7.21/COMPONENT_MANIFEST.json`)_ |
| Branch | `Cursor-merge-3.7.21` |
| Started | 2026-06-08 |
| Completed | _(pending)_ |
| Status | `in_progress` |

## User goals (fill first)

- **Goals:** _(what to achieve this merge)_
- **Out of scope:** _(what to ignore regardless of changelog)_
- **Notes:**

## Changelog (paste from cursor.com/changelog)

_Paste release notes for Cursor 3.7.21 here._

-

## Manifest diff (optional inventory)

```powershell
.\scripts\cursor-merge\start-merge.ps1 -Version 3.7.21 -InstallerPath cursor\CursorSetup-x64-3.7.21.exe

.\scripts\cursor-merge\diff-manifests.ps1 `
  -Old cursor\extracted\3.7.19\COMPONENT_MANIFEST.json `
  -New cursor\extracted\3.7.21\COMPONENT_MANIFEST.json `
  -OutputPath docs\merges\3.7.21\manifest-diff.txt
```

_Summary:_

_(pending)_

## Feature decisions

| Item | Cursor path | Void target (if any) | Decision | Rationale | Approach (if adapt) |
|------|-------------|----------------------|----------|-----------|---------------------|
| _(example)_ | | | `defer` | Awaiting changelog review | |

See [FEATURES.md](../../FEATURES.md) **Cursor component reference** for Void code hints — not a mandatory merge list.

## Implementation

_(only for `implement` / `adapt` rows above)_

## Validation

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

- [ ] Every item of interest has an explicit decision
- [ ] All `implement` / `adapt` items implemented and validated
- [ ] All `ignore` / `defer` items documented
- [ ] [FEATURES.md](../../FEATURES.md) updated
- [ ] PR opened: `Cursor-merge-3.7.21` → `main`

**Conclusion:** _(pending)_
