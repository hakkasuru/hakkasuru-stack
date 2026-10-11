# Review diff

Check the whole diff before raising the MR. Tiers 2 and 3 only.

## Against the brief and plan

- Every acceptance criterion in the brief is met, and you can point to the change and the check that shows it.
- No planned unit was skipped.
- Nothing in the diff falls outside the plan's scope. Unplanned changes get removed, or explained in the MR description.

## Correctness and cleanup

Invoke Claude Code's built-in `/code-review` and `/simplify` skills with the Skill tool, pointed at the run's branch. Pass an explicit target when the session isn't inside the worktree.

Fix each finding, or decline it with a stated reason. Declined findings go in the final report.

## Smallest diff

Read and apply [../../principle-laziness-protocol/SKILL.md](../../principle-laziness-protocol/SKILL.md) to the diff: remove pass-throughs, duplicated decisions, and anything the change doesn't need.

## Repeated findings

A finding that comes up a second time in this run gets a structural fix, per [../../principle-encode-lessons-in-structure/SKILL.md](../../principle-encode-lessons-in-structure/SKILL.md): a lint, a check, or a script, not another manual fix. If the structural fix is out of the task's scope, propose it in the final report instead.
