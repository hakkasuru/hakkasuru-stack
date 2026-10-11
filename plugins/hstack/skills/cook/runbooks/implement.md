# Implement

Execute the plan one unit at a time, proving each unit before starting the next. At tier 0 there is no written plan: the single unit is the fix and its check.

## Where

Work only in the run's worktree, on the branch this run created. Never edit the user's main checkout.

## One unit at a time

For each unit:

1. Make the change.
2. Run its check.
3. Read the real result, per [../../principle-prove-it-works/SKILL.md](../../principle-prove-it-works/SKILL.md). A check that wasn't run, or output that wasn't read, isn't a pass.
4. Commit (below), then start the next unit.

For a bug, unit 1 is a failing test that reproduces it, where feasible. Watch it fail before writing the fix.

## Finding the check

Use the first of these that works for the unit:

1. An existing targeted test.
2. The repo's own check commands, found in CLAUDE.md, package scripts, a Makefile, or CI config.
3. The project's `verify-<app>` skill, if `create-verification-skill` generated one.
4. Claude Code's built-in `/run` skill, to see the behaviour in the real app.

If none works, the unit is unverified. Say so in the final report, and treat it as a risk trigger: the tier's floor becomes 2.

## Attempts

Each unit gets up to `caps.attempts` edit-and-verify cycles, from `tune.py caps`. A unit that uses them all is stuck, which is an escalation trigger. After each unit, update the unit and attempt counts in the todo list. The ledger records them as `attempts` and `stuck_units`.

## Slow checks

Run long test suites with the Bash tool and `run_in_background: true`. Their duration never counts against anything. Keep working on what doesn't depend on the result.

## Commits

- Commit only related changes together. Never put unrelated changes in one commit.
- One commit per unit is the default.
- Fix rounds add new commits. Never amend earlier ones.
- Write commit messages through [../../hermes/SKILL.md](../../hermes/SKILL.md).

## Escalation triggers to watch

After each unit, check for:

- more files or modules than Gauge expected
- unexpected callers, or another repo
- a stuck unit
- a risk trigger that wasn't visible at Gauge

Any one raises the tier. Keep the work done so far.

## Tier 3 delegation

At tier 3, units may go to `general-purpose` subagents with `model: sonnet`. Give each one the unit, its check, its attempt allowance, and the worktree path. Review each delegate's diff yourself before committing: you own the result.

## Fix rounds

When `babysit` reports a failure caused by the change, the unit is that failure. Use `babysit`'s diagnosis as the starting point, fix it, run the failing check locally where possible, and commit the fix as a new commit.
