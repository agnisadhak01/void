# Cursor Merge Report — 3.7.21

> **You decide what ships.** Fill feature decisions before implementation. Scripts inventory files only.

## Metadata

| Field | Value |
|-------|-------|
| Cursor version | 3.7.21 |
| VS Code base | 1.105.1 |
| VS Code commit | d5c0e77a0214208f36b56d42e8e787de88d02ea4 |
| Product rebrand | **Pulse** (`product.json`) |
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
| MOD-000 Product rebrand | product.json | product.json | `implement` | Custom editor identity: Pulse | See `cursor/patches/3.7.21/mods.yaml` |
| _(example)_ | | | `defer` | Awaiting changelog review | |

See [FEATURES.md](../../FEATURES.md) **Cursor component reference** for Void code hints — not a mandatory merge list.

## Implementation

- **MOD-000:** `product.json` rebranded to Pulse (`nameShort`, `dataFolderName` `.pulse-editor`, `urlProtocol` `pulse`, win32 identifiers).

Cursor reference environment (2026-06-10):

- `cursor/extracted/3.7.21/` extracted via `-FromInstalled`
- `scripts/cursor-dev/verify-extraction.ps1` passes
- Mod specs: `cursor/patches/3.7.21/mods.yaml`

## Validation

Build toolchain documented in [BUILD.md](../../BUILD.md). Ecosystem/CI: [ECOSYSTEM.md](../../ECOSYSTEM.md).

**Environment status (2026-06-08):**

| Step | Status |
|------|--------|
| VS 2022 Build Tools + Windows SDK | Installed |
| Node 20.18.2 (NVM) + npm 11 | Installed |
| `npm install` | Passed |
| `npm run buildreact` | Passed |
| `npm run compile` | Passed (0 errors) |
| `npm run gulp vscode-win32-x64` | Passed (prior Void branding) |
| Cursor 3.7.21 extraction | Passed — `cursor/extracted/3.7.21/` |
| `verify-extraction.ps1` | Passed |
| `.\scripts\start-dev.ps1` | Passed (2026-06-10) — watch + launch in ~2 min |

### Build

- [x] `.\scripts\start-dev.ps1` — watch 0 errors + Void launches
- [x] `npm run buildreact` — passed (included in start-dev)
- [x] Dev instance launches — `scripts\code.bat` via start-dev
- [x] _(optional)_ packaged smoke test — `Void.exe` launches

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
