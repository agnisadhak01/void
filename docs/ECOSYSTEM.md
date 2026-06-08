# Void Ecosystem

Production map of repositories, build pipelines, and distribution. Companion to [INDEX.md](INDEX.md).

## Ecosystem entity graph

```mermaid
erDiagram
  VOID_SOURCE ||--o{ VOID_BUILDER : "cloned during CI"
  VOID_BUILDER ||--o{ PATCHES : "applies at build time"
  VOID_BUILDER ||--|| BINARIES_REPO : "publishes artifacts"
  VOID_BUILDER ||--|| VERSIONS_REPO : "publishes version JSON"
  VOID_DESKTOP ||--|| VERSIONS_REPO : "checks for updates"
  VOID_DESKTOP ||--|| BINARIES_REPO : "downloads installers"
  CURSOR_INSTALLER ||--o| MERGE_REPORT : "reference only"
  VOID_SOURCE ||--o{ MERGE_REPORT : "implementation target"

  VOID_SOURCE {
    string path "agnisadhak01/void"
    string branch "main | Cursor-merge-*"
    string ai_code "src/vs/workbench/contrib/void/"
  }
  VOID_BUILDER {
    string path "voideditor/void-builder"
    string base "VSCodium fork"
    string workflows "stable-macos | stable-linux | stable-windows"
  }
  PATCHES {
    string purpose "telemetry off, update URLs"
    string location "void-builder/patches/"
  }
  BINARIES_REPO {
    string path "voideditor/binaries"
    string artifacts "dmg zip exe AppImage"
  }
  VERSIONS_REPO {
    string path "voideditor/versions"
    string role "update manifest text/JSON"
  }
  VOID_DESKTOP {
    string product "Void.exe / Void.app"
    string updateUrl "raw.githubusercontent.com/voideditor/versions"
  }
  CURSOR_INSTALLER {
    string path "cursor/*.exe gitignored"
    string use "inventory reference only"
  }
  MERGE_REPORT {
    string path "docs/merges/{version}/"
    string decisions "implement|adapt|ignore|defer"
  }
```

## Repository topology

```mermaid
graph TB
  subgraph upstream_archived["Upstream (archived)"]
    VE_VOID[voideditor/void]
  end

  subgraph fork["This workspace"]
    AG_VOID[agnisadhak01/void — X:\Void]
    AG_BRANCH[Cursor-merge-3.7.21]
  end

  subgraph builder["Release pipeline"]
    VE_BUILDER[voideditor/void-builder — X:\void-builder]
    VE_BIN[voideditor/binaries]
    VE_VER[voideditor/versions]
  end

  subgraph microsoft["Microsoft"]
    VSCODE[microsoft/vscode]
  end

  VSCODE --> VE_VOID
  VE_VOID --> AG_VOID
  AG_VOID --> AG_BRANCH
  VE_BUILDER -->|clone void@commit| AG_VOID
  VE_BUILDER --> VE_BIN
  VE_BUILDER --> VE_VER
  AG_VOID -.->|local gulp only| LOCAL[VSCode-win32-x64]
```

## Git remotes (Void fork)

| Remote | URL | Notes |
|--------|-----|-------|
| `origin` | `https://github.com/agnisadhak01/void.git` | Push target for this fork |
| `upstream` | `https://github.com/voideditor/void.git` | Archived; read-only reference |

## Build pipeline comparison

```mermaid
flowchart TB
  subgraph local["Local development — X:\\Void"]
    L1[npm install]
    L2[npm run buildreact]
    L3[npm run watch OR npm run compile]
    L4{Goal?}
    L5[scripts/code.bat — Dev Mode]
    L6[npm run gulp vscode-win32-x64]
    L7[VSCode-win32-x64/Void.exe]

    L1 --> L2 --> L3 --> L4
    L4 -->|edit & test| L5
    L4 -->|portable folder| L6 --> L7
  end

  subgraph ci["Production CI — void-builder"]
    C1[GitHub Actions workflow_dispatch]
    C2[Clone voideditor/void @ commit]
    C3[Apply VSCodium patches]
    C4[OS build script stable-*.sh / yml]
    C5[Sign / package assets]
    C6[Release → voideditor/binaries]
    C7[Update → voideditor/versions]

    C1 --> C2 --> C3 --> C4 --> C5 --> C6 --> C7
  end

  local -.->|same source| ci
```

| Dimension | Local gulp | void-builder CI |
|-----------|------------|-----------------|
| **Trigger** | Manual on dev machine | GitHub Actions |
| **Patches** | None (raw fork source) | VSCodium patches (telemetry, update URLs) |
| **Output** | `../VSCode-win32-x64/` folder | Platform installers on `binaries` release |
| **Auto-update** | No | Yes via `versions` repo |
| **Use when** | Dev, merge QA, quick test | Public releases, website downloads |

Details: [BUILD.md](BUILD.md).

## void-builder internals

Fork of [VSCodium](https://github.com/VSCodium/vscodium). Void-specific edits are marked with caps-sensitive `Void` and `voideditor` in that repo.

```mermaid
flowchart LR
  subgraph void_builder_repo["void-builder/"]
    WF[".github/workflows/"]
    PATCH["patches/*.patch"]
    PREP[prepare_vscode.sh]
    BUILD_SH[build.sh / stable-*.sh]
  end

  WF -->|stable-windows.yml| WIN[Windows job]
  WF -->|stable-macos.yml| MAC[macOS job]
  WF -->|stable-linux.yml| LIN[Linux job]

  WIN --> PREP
  MAC --> PREP
  LIN --> PREP
  PREP --> PATCH
  PATCH --> BUILD_SH
  BUILD_SH --> REL[binaries release]
  BUILD_SH --> VER[versions commit]
```

### Key environment variables (CI)

| Variable | Typical value | Role |
|----------|---------------|------|
| `ASSETS_REPOSITORY` | `{owner}/binaries` | Release artifact destination |
| `VERSIONS_REPOSITORY` | `{owner}/versions` | Update manifest destination |
| `void_commit` | git SHA | Pin Void source for reproducible build |
| `void_release` | release number | Custom release counter |

### Customizing for your own distribution

1. Fork `voideditor/void-builder`.
2. Search-replace `voideditor` → your org (binaries + versions repos).
3. Search-replace `Void` → your product name in workflows and scripts.
4. Run workflows from your fork; ensure `void` source remote points to your fork.

## Auto-update flow

```mermaid
sequenceDiagram
  participant App as Void Desktop
  participant Ver as voideditor/versions
  participant Bin as voideditor/binaries

  App->>Ver: GET update manifest (product.updateUrl)
  Ver-->>App: latest version + metadata
  alt newer version available
    App->>Bin: download installer/asset
    Bin-->>App: .exe / .dmg / .zip
    App->>App: apply update
  end
```

Patches in `void-builder/patches/` redirect VS Code's built-in update endpoints to Void URLs (`prepare_vscode.sh` sets `updateUrl` and `downloadUrl`).

## Cursor merge relationship

Cursor is **not** part of the release pipeline. It is a **reference source** for feature ports.

```mermaid
graph LR
  CURSOR[Cursor installer] -->|extract| MANIFEST[COMPONENT_MANIFEST.json]
  MANIFEST -->|human decisions| REPORT[MERGE_REPORT.md]
  REPORT -->|implement/adapt| VOID_SRC[Void source]
  VOID_SRC -->|local or CI| SHIP[Desktop app]
```

See [CURSOR_MERGE_WORKFLOW.md](CURSOR_MERGE_WORKFLOW.md).

## Rebasing strategy

| Repo | Rebase onto | Find changes via |
|------|-------------|------------------|
| `void/` | `microsoft/vscode` | Search `Void` in source |
| `void-builder/` | VSCodium | Search `Void`, `voideditor` |

Align VS Code and VSCodium versions when rebasing both repos.

## Related

- [BUILD.md](BUILD.md) — local build commands and Windows toolchain
- [FEATURES.md](FEATURES.md) — what Void implements
- [INDEX.md](INDEX.md) — documentation map
