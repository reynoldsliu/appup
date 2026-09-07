# appup — plan

Mac app inventory + update helper. CLI first, macOS Shortcut wrapper next, menu bar app last (only if the CLI proves its worth).

**Principles**: list-then-confirm (never unattended upgrades), single Python file, stdlib only.

## v1 — CLI (`appup`)

One Python script, no dependencies.

### `appup list`
Categorized inventory, merged from:

| Category | Source | Outdated check |
|---|---|---|
| Homebrew formulae | `brew list --formula --versions` | `brew outdated --json` |
| Homebrew casks | `brew list --cask --versions` | `brew outdated --cask --json` |
| App Store | `mas list` | `mas outdated` |
| npm globals | `npm ls -g --json` | `npm outdated -g --json` |
| pipx | `pipx list --json` | none (pipx exposes no latest info) — `pipx upgrade-all` covers it |
| Manual .app | `system_profiler SPApplicationsDataType -json`, minus paths owned by brew casks + mas | none (no registry) — mark "self-managed" |

Each source is one function returning `[{name, version, latest, category}]`. A source's tool missing (no npm, no pipx) → skip silently.

### `appup outdated`
Same data, filtered to items with pending updates. This IS the security alert for v1:
- pending update → ⚠️ outdated
- major-version gap or in a small hardcoded EOL list → 🚨 flagged
- manual .app with no update path → listed so you know to check it by hand

### `appup upgrade`
Prints the exact commands it will run (`brew upgrade`, `mas upgrade`, `npm update -g`, `pipx upgrade-all`), asks y/n once, runs them. Per-item selection can come later if ever needed.

## v2 — Shortcut
macOS Shortcuts app: "Run Shell Script" action calling `appup outdated`, show result in a notification/alert. Optionally a nightly launchd LaunchAgent doing the same. No new code beyond a plist.

## v3 — Menu bar app (maybe)
Only if v1/v2 get daily use. Cheapest path: xbar/SwiftBar plugin — a shell script that prints menu items — reusing `appup` output verbatim. A real Swift app is the last resort.

## Explicitly skipped
- CVE/OSV lookups — weak coverage for desktop apps; revisit in v2+ for npm/pipx if wanted
- Unattended auto-upgrade — cask upgrades kill running apps, some prompt for passwords
- Updating manual .apps — most are Sparkle-based and update themselves; we only surface them
- cargo/gem/go sources — same pattern, add when actually needed
