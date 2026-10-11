# Plan

Turn the brief into a numbered list of units at the depth the tier asks for. Tier 0 skips this runbook.

## Depth by tier

- **Tier 1.** A few bullets. They go into the MR description later.
- **Tiers 2 and 3.** What and how: each step names the change, its check, and the files it touches.
- **Tier 3.** Group the units into stacked MRs, each mergeable on its own, for example `MR 1: units 1-4`. Each MR builds on the one below it.

## Tier 3 context first

Before planning a tier 3 task, read [../../how/SKILL.md](../../how/SKILL.md) and [../../why/SKILL.md](../../why/SKILL.md) and follow them on the area the brief touches: `how` for how it works now, `why` for the forces that shaped it. Plan from what they find.

## Units

A unit is one change that ends in a check that can fail. If you can't name a check that would fail when the change is wrong, the step is two units.

Number the units. Each one states:

- the change
- its check: the command or observation that fails when the change is wrong
- the files it touches

If the plan needs more units than `caps.units.<tier>` from `tune.py caps`, that is an escalation trigger. Raise the tier before writing any code, and redo this runbook at the new tier's depth.

## Bug fixes

For a bug, unit 1 reproduces it with a failing test, where that's feasible. The fix unit then makes that test pass.

## Principles

- Read and apply [../../principle-laziness-protocol/SKILL.md](../../principle-laziness-protocol/SKILL.md): the smallest change that solves the problem, deletion before addition, no new layers.
- For bulk or repetitive edits, read and apply [../../principle-build-the-lever/SKILL.md](../../principle-build-the-lever/SKILL.md). The codemod or script is a unit, with its own check.
