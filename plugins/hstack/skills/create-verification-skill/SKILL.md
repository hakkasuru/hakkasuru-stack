---
name: create-verification-skill
description: "Generate a project-local verify-<app> skill that launches this repo's app, drives it the way a user does, and captures evidence, then seed its feature map and prove it end to end. Works for web, CLI/TUI, desktop, API, or mobile."
disable-model-invocation: true
---

# Create a verification skill

Every serious project needs a scripted way to drive the real app and prove behavior: launch it, exercise a feature the way a user would, and capture evidence. This skill generates that as a project-local Claude Code skill (`.claude/skills/verify-<app>/`) tailored to the repo. You write the generator's output for the next agent, not for a human: it will be read cold, mid-task, by a Claude session that has never seen the app.

## 1. Interview the repo, not the user

Answer these from the codebase (CLAUDE.md, README, package manifests, Makefiles, CI config, existing tests) and only ask the user what you cannot observe:

- **Surface:** what does a user actually touch? A web UI, a CLI/TUI, a desktop app, an API, a mobile app, a library? A repo can have several; pick the primary one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, README quickstart, CLAUDE.md). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent interact with it programmatically? Existing harnesses first — Playwright/Cypress specs, expect scripts, PTY helpers, curl-able endpoints, a debug port. Then browser tooling already available to Claude in this environment (a Playwright or Chrome DevTools MCP server, Claude in Chrome). Only then pick a generic recipe: Playwright/CDP scripts for web and Electron, a tmux/PTY harness for CLI/TUI, plain HTTP for services. The generated skill must not depend on an MCP server the project doesn't declare (e.g. in `.mcp.json`); if it uses one, say so in Launch.
- **Observe:** what evidence can be captured? Screenshots, ARIA snapshots, terminal transcripts, response bodies, logs, exit codes, DB state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill: refusing to double-drive a shared instance beats corrupting the user's session.

If the checkout doesn't build or start as-is, fix that first (or report it precisely) before generating; a skill written against a broken base teaches wrong steps. When an irrelevant missing asset blocks startup (a static dir the API never serves, a sample config), the generated skill may create it, clearly marked as verification scaffolding, and remove it in cleanup.

## 2. Generate the skill

Write `.claude/skills/verify-<app>/SKILL.md` with YAML frontmatter and these sections, each grounded in what the interview actually found (no placeholders left).

Frontmatter: `name: verify-<app>` and a `description` that names the app, the surface, and when to reach for it ("Use when verifying a change to <app>'s <surface> works in the real app, not just in tests"). Without frontmatter the skill never registers; without a concrete description Claude never reaches for it.

- **Launch:** the exact command that starts the app for verification, and how to tell it's ready (a log line, a port answering, a prompt). For a long-lived server or UI, tell the reader to start it with the Bash tool's `run_in_background` and wait on readiness with a bounded poll (e.g. `until curl -sf <url>; do sleep 1; done` under a timeout), never a fixed sleep. Include teardown. For a short-lived CLI or TUI there is no server to keep alive: launch means build the binary (or install deps) once, then start each drive in its own isolated PTY or tmux session.
- **Doctor:** one read-only check that answers "is this instance worth driving?" — process up, right version/build, port owned by us, auth valid. An agent runs this first whenever anything looks off.
- **Drive:** the harness recipe with real selectors/commands from this repo, not examples. Prefer stable handles (ARIA roles and names, data attributes, prompt strings, route paths) over coordinates and tab order. Commands must be runnable non-interactively through the Bash tool: no prompts waiting on a TTY unless the recipe drives them through tmux/expect.
- **Evidence:** what to capture for a proof and where it goes. State the proof standards: exercise the real user path, not internal setters or test-only endpoints; capture the action and the resulting state, not just the final screen; verify side effects (files written, rows inserted, messages sent) alongside what's visible; mocks only where a production boundary already isolates the external system. When the safe path is a dry-run or test mode, verify what it actually skips by observing (files, network, git refs) rather than trusting its name: some dry-runs still touch the network or open a browser. Screenshots are only proof once read back: tell the reader to open captured images with the Read tool and confirm they show what the proof claims.
- **Cleanup:** how to tear down instances the run created. Never kill by process name; kill what you started (record PIDs, or stop the background task you launched). Cleanup removes instances and scratch state, never the evidence: proof artifacts survive the teardown, in a location the skill names (gitignored, or outside the repo).
- **Helpers:** any script the skill ships lives in the skill directory, is executable, and its invocation is shown in the skill body. A helper the reader has to reverse-engineer is not a helper.

## 3. Seed the feature map

Inventory first: list every user-facing area from the sources that define the surface — route table, command registry, menu definitions, feature folders — and note which sources you read.

Create `.claude/skills/verify-<app>/features/README.md` plus one file per seeded feature (aim for the top 3-5 to start). Follow the shape in [`references/feature-map-example/`](references/feature-map-example/), with a README index and one file per feature. Each file answers, from the user's point of view: what the feature is, how to reach it, how to drive it with the harness, and what observable end state proves it works. The four H2s are `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. The map is the repo's maintained verification source; a proof that drives one convenient entry point is incomplete when the map lists others.

Write the rest of the inventory down; anything left only in chat is lost when the session ends. Every unseeded user-facing area goes under `## Not yet mapped` at the end of `features/README.md`, one row each: area, concrete route or source path, any partial coverage in other feature files, notes for the future file. An area deliberately kept inside another feature file (e.g. a step with lasting side effects, driven only within a larger flow) gets a short paragraph naming its host file instead of a row. The section states its inventory sources and the date checked; maintenance re-reads exactly those sources. Step 3 isn't done until this section exists, even if it only says nothing is left unmapped. Unmapped is a reportable status, distinct from verified and verified-unreachable: an unmapped area was never driven and is never reported as covered.

Link the map from the generated SKILL.md so a reader knows to open `features/README.md` before driving.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive ONE mapped feature (one is enough; the map exists so later runs can cover the rest), capture evidence, clean up. After cleanup, confirm the evidence still exists at the named location — a cleanup that eats the proof fails this step. Fix what fails, and run the generated cleanup after every failed iteration too, so broken attempts don't strand processes, background tasks, and ports. A generated skill that was never executed is a draft, not a deliverable.

## 5. Hand it over

Report what was generated, which feature was proven, where its evidence is, and the `Not yet mapped` areas next to the seeded ones, so the user sees how much of the map is left. Offer to add a one-line pointer to the project's CLAUDE.md (e.g. "To verify a change in the running app, use the `verify-<app>` skill") so future sessions find it; don't add it unasked.

Point the user at `/hstack:maintain-verification-skill` for keeping the map honest as the app changes. Suggest a cadence only if they ask.
