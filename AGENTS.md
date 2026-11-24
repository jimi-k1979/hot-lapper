# AGENTS.md

## Project

**Hot Lapper** is an original cockpit-view, single-seater racing game in Python. It is influenced by Psion's *Chequered Flag* for the ZX Spectrum but is not a port of it. The design is being charted in [Hot Lapper: charting the MVP spec](https://github.com/jimi-k1979/pyCheq/issues/1). Use the domain vocabulary in `GLOSSARY.md`.

### Decisions already made

- **Original, not a port.** The game keeps the genre and feel but uses a new name, new circuits, new cars, new art, new text and new tuning numbers. Nothing is extracted from `cheqflag.sna`; it may only be played in Fuse to get a feel for the genre.
- **Gameplay scope (MVP).** A solo race against the clock with no opponents. There is a three-car roster: a robust automatic, a balanced manual and a fragile, fast manual. There are three circuits stored as data: two wholly original and one based on a real-world circuit. Lap records are kept per circuit only. Sound is minimal and synthesised. There is no demo mode.
- **Presentation.** A small fixed-resolution, limited-palette canvas scaled up to the window, a pseudo-3D cockpit view, keyboard-only input and a simple interface.
- **Stack.** Python 3.13, Clean Architecture, Linux first. No work is done specifically for other platforms.
- **Learning test bed.** The user is learning advanced Python through this project and must understand all of the code. Use advanced features only where they earn their place.
- **Code style.** Code speaks for itself, with sparse comments. Explanations of Python features belong in `docs/learning/`, not in the source.
- **YAGNI.** Never build for an imagined future. A fuller follow-on game is a separate project and out of scope here, as are user-defined circuit mods.

## Git workflow

`main` must always be clean and working. Nothing is built directly on it.

- **Feature branch:** each feature gets its own branch off `main`, named `feature/<feature-slug>`.
- **Ticket branches:** each ticket in that feature is worked on its own branch off the feature branch, named `ticket/<issue-number>-<slug>`.
- **Ticket PRs:** each ticket branch is merged into its feature branch through a pull request. The PR targets the feature branch, not `main`, and names its ticket (`Closes #<n>`). GitHub only auto-closes issues on merges into `main`, so close the ticket by hand once its PR is merged.
- **Feature PR:** when every ticket is merged, the feature branch is merged into `main` through one final pull request.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on jimi-k1979/pyCheq via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
