# appup

One command to see every app on your Mac — grouped by how it was installed — and to know which ones are out of date.

macOS spreads your software across five or six package managers that don't know about each other. `appup` asks all of them, merges the answers, and tells you what needs attention. It is read-only by default: nothing on your system changes unless you run `upgrade` and explicitly confirm.

## Features

- **Inventory** — every app, categorized by install method: Homebrew formulae and casks, Mac App Store, npm globals, pipx tools, and hand-installed `.app` bundles
- **Outdated report** — what has a pending update, with severity markers for major-version gaps and end-of-life software
- **One-confirmation upgrades** — per category or all at once, always shown before run
- **Manual-app rescue** — matches hand-installed apps against Homebrew's cask catalog (a local file, no network) and can hand them over to Homebrew for updating
- **zsh tab completion**, multi-category filters, and a built-in selftest
- Single Python file, standard library only, no dependencies

## Sample output

```
$ appup outdated

== brew formula ==
  aom  3.14.1 -> 3.15.0  ⚠️ outdated
  ca-certificates  2026-07-16 -> 2026-08-13  ⚠️ outdated

== manual .app ==
  Steam  6.1 -> 6.2  ⚠️ outdated
```

Add `--json` to `list`/`outdated` for machine-readable output (no prompts — safe for scripts and cron).

## Tests

```bash
./appup selftest      # unit assertions over the parsing logic (runs in CI)
python3 test_cli.py   # pty integration test: needs a real Mac with manual .apps installed
```

## Requirements

- macOS with Python 3.9+ (the system `python3` from Xcode Command Line Tools is fine)
- Whatever package managers you actually use — each one found adds a category; missing ones are skipped silently:

| Tool | Adds |
|---|---|
| `brew` | Homebrew formulae and casks, plus the catalog used for manual-app matching |
| `mas` | Mac App Store apps (`brew install mas`) |
| `npm` | globally installed npm packages |
| `pipx` | Python CLI tools |

## Install

Put `appup` in a directory that only your user account can write to. `~/.local/bin` is the standard choice — unlike `/usr/local/bin` it is not shared with other software or admin processes, so nothing else on the system can swap the file out from under you:

```bash
mkdir -p ~/.local/bin && install -m 755 appup ~/.local/bin/appup
```

If `~/.local/bin` is not already on your PATH, add it:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && exec zsh
```

`install -m 755` copies the file with owner-only write permission. If you prefer a symlink into your clone so that `git pull` updates it in place, `ln -s "$PWD/appup" ~/.local/bin/appup` works too — just know the live command then changes whenever the clone does.

## Quick start

```bash
appup outdated        # what needs attention?
appup upgrade brew    # apply Homebrew updates, touch nothing else
appup list manual     # what did I install by hand?
```

## Commands

| Command | What it does | Changes your system? |
|---|---|---|
| `appup list [category]` | Full inventory grouped by install method | No |
| `appup outdated [category]` | Only the apps needing attention, with severity markers | No |
| `appup upgrade [category]` | Prints the upgrade commands, asks to confirm, then runs them | Yes, after you type `y` |
| `appup help` | Full built-in help: commands, categories, examples | No |
| `appup completion` | Prints the zsh tab-completion script | No |
| `appup selftest` | Runs the built-in assertions over the parsing logic | No |
| `appup` | Same as `appup help` | No |

Markers in output: ⚠️ a newer version exists · 🚨 major-version gap or end-of-life software.

### Categories

Every command takes an optional category filter; combine several with commas:

| Category | Covers |
|---|---|
| `brew` | Homebrew formulae **and** casks |
| `formula` | Homebrew formulae only |
| `cask` | Homebrew casks only |
| `store` | Mac App Store apps (needs `mas`) |
| `npm` | npm global packages |
| `pipx` | pipx-installed Python tools |
| `manual` | .apps installed by hand from a .dmg or .zip |

```bash
appup outdated npm
appup list brew,npm
appup upgrade formula
```

A typo in the category prints the valid list instead of guessing.

## Manual apps: checking and updating

Hand-installed apps have no version registry, so plain `appup outdated` skips them. Two commands deal with them:

**`appup outdated manual`** lists them all, and first asks:

```
Check manual .apps against Homebrew's cask catalog (local file, exact name matches only)? [y/N]
```

Answering `y` compares each app against the cask catalog Homebrew already keeps on your disk (`~/Library/Caches/Homebrew/api/cask.jws.json` — no network request is made). Apps with a newer version in the catalog show an arrow like everything else. In piped or scheduled runs the prompt reads EOF and counts as "no", so nothing ever blocks.

**`appup upgrade manual`** shows the matched, outdated apps and asks which to include — press Enter for all, or type a few names (`coconutbattery snipaste`). It then offers one command: `brew install --cask --force <apps...>`. If you confirm, Homebrew downloads each app from its official source, verifies its checksum, replaces the old copy in `/Applications`, and **manages it from then on** — the app moves to the `cask` category and future updates arrive via `appup upgrade brew`. Quit the affected apps before confirming.

Matching is deliberately strict, because replacing the wrong app would be worse than doing nothing:

- Only **exact display-name** matches count — no fuzzy matching, ever
- The cask's `.app` filename must also match the installed bundle. This is what stops MacPaw's "Gemini" (a duplicate-file finder) from being offered as an update to Google's "Gemini" — same display name, different app
- An installed version **newer** than the catalog's is left alone (casks sometimes lag)
- No match simply means "update this one by hand" — Docker, VS Code, and zoom.us fall in this bucket on a typical machine because their cask display names differ

## Tab completion (zsh)

```bash
echo 'eval "$(appup completion)"' >> ~/.zshrc && exec zsh
```

Then `appup <Tab>` suggests commands, and after `list`, `outdated`, or `upgrade`, Tab suggests a category. Multi-category filters (`brew,npm`) are typed by hand — completion offers single categories to keep the menu clean.

The script self-initializes zsh's completion system if your `.zshrc` hasn't (that's the `compinit` guard in its first line — without it, `compdef` fails silently and Tab falls back to completing filenames). Two requirements: `appup` must be on your PATH under exactly that name, and you need a new shell (`exec zsh`) after adding the line.

## Updating, disabling, uninstalling

**Update appup itself.** It's one file — replace it and you're done. From a git clone: `git pull`, then re-run the `install -m 755` line above (or nothing, if you chose the symlink). There is no state, cache, or config of its own to migrate; new versions take effect on the next run.

**Restart?** Nothing to restart — `appup` is not a daemon and runs only when you invoke it. The only thing that ever needs a restart is your shell (`exec zsh`), and only after changing `.zshrc` (PATH or completion lines).

**Disable temporarily.** Don't run it. If you only want Tab completion gone, comment out the `eval "$(appup completion)"` line in `~/.zshrc` and open a new shell.

**Uninstall completely.**

```bash
rm ~/.local/bin/appup
```

Then delete the `eval "$(appup completion)"` and (if you added it only for appup) the PATH line from `~/.zshrc`. That's the entire footprint — appup writes no other files anywhere.

## Security model

What `appup` does and deliberately does not do:

- **Read-only by default.** Only `upgrade` changes anything, always shows the exact commands first, and always requires an interactive `y`.
- **No network access.** appup itself never opens a connection. Version data comes from local tools and Homebrew's already-downloaded catalog file. Downloads during upgrades are performed by the package managers themselves — Homebrew verifies checksums against its formulae; appup never downloads or executes anything from the internet.
- **No shell evaluation.** Every external command runs as an argument list (`subprocess.run` without `shell=True`), so crafted app names can't inject shell commands.
- **Bounded subprocesses.** Every query has a 300-second timeout, so a wedged package manager can't hang a scheduled run forever.
- **Strict manual-app matching.** Exact name plus bundle-filename verification before any app is ever offered for replacement (see above).
- **Prompts only at a terminal.** Piped and scheduled runs never block on, or auto-answer, a question.
- **Minimal footprint.** One file, no dependencies to audit, no config files, nothing written to your system.
- What it inherits, not fixes: `appup upgrade` trusts brew/mas/npm/pipx and their registries. If a registry serves a malicious package, appup installs it as faithfully as running those tools yourself would.

## Troubleshooting

**Tab shows filenames instead of commands.** The completion script isn't loaded in this shell. Check the `eval` line exists in `~/.zshrc`, that `appup` (not `./appup`) is how you're invoking it, and open a new shell. Current versions of the script initialize `compinit` themselves; if you installed the line before that fix, it works now without changes — just `exec zsh`.

**"unknown category"** — the valid list is printed with the error; note it's `store`, not `mas`, and `manual`, not `app`.

**App Store section missing.** Install `mas` (`brew install mas`); the section appears on the next run.

**The catalog check finds nothing / seems stale.** The catalog file updates whenever Homebrew does; run `brew update` to refresh it.

**`appup list` takes a few seconds.** Most of that is `system_profiler` scanning `/Applications`. Normal.

**Date-versioned packages get a spurious 🚨.** `ca-certificates 2024-12-31 -> 2026-07-16` parses as a "major gap" because 2026 > 2024. The update is real; the marker is just louder than it deserves.

## Extending

Each install source is one small function returning `[{name, version, latest, category}]`, combined in `all_items()`. Adding cargo, gem, or go is one more function in the same shape plus one line in `all_items()` — about eight lines.

Two test layers, both dependency-free — run them after any change:

```bash
appup selftest && python3 test_cli.py
```

`selftest` covers the pure logic (parsers, version compare, catalog matching); [test_cli.py](test_cli.py) runs the CLI in a real pseudo-terminal, verifies every prompt actually appears, and answers `n` to anything that would change the system.
