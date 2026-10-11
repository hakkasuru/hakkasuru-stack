---
name: cook
description: "Take a task from a prompt, ticket, or link to a merge-ready MR: frame the requirements, gauge the tier, plan, implement, raise the MR, and watch its pipeline. Rigor scales with the task, from a one-line fix to a stacked change."
disable-model-invocation: true
---

# Cook

Cook takes a task from a prompt, a ticket, or a link to a merge-ready PR or MR. How much process it runs depends on the task's tier: a one-line fix goes straight from edit to MR, and a cross-cutting change gets a reviewed plan and a stack of MRs.

Paths below are relative to this skill's directory, shown as `<skill-dir>` in commands. Runbooks live in `runbooks/`. Other hstack skills are read by relative path, because their model invocation is disabled.

## Modes

```
/hstack:cook <prompt | ticket key | issue link | any mix> [--tier N] [--draft]
/hstack:cook --resume
/hstack:cook --tune
/hstack:cook --doctor
```

- `--tier N` forces a tier. A risk-trigger floor still applies.
- `--draft` opens draft PRs or MRs instead of ready ones.
- `--resume` continues the most recent unfinished run in this repo (see Resuming).
- `--tune` suggests effort-cap changes from past runs and applies the ones the user approves (see Tuning).
- `--doctor` checks prerequisites without starting a task (see Doctor).

## Process

```
1 Start → 2 Frame → 3 Gauge → 4 Route → 5 Plan* → 6 Review-plan* → 7 Implement
  → 8 Review-diff* → 9 Raise-mr → 10 Babysit (background, turn ends)
  → 11 Triage result → (fix loop back to 7, at most 2 rounds) → 12 Final report
* depends on the tier
At any checkpoint: escalation trigger → raise the tier, keep the work · unit cap reached → effort checkpoint
```

1. **Start.**
   - `--doctor`: go to Doctor. `--tune`: go to Tuning. Both work outside a git repo.
   - Otherwise, find the repo: `git remote get-url origin`. Not a git repo, or no `origin`: say so and stop.
   - Normalize the remote into `<remote>`: strip `ssh://`, `https://`, `http://`, and a leading `git@`; replace the first `:` with `/` when it separates host and path; drop a trailing `.git`; lowercase the host. So `git@github.com:Hakkasuru/hstack.git` and `https://github.com/Hakkasuru/hstack` both become `github.com/Hakkasuru/hstack`.
   - Load the effective caps: `python3 <skill-dir>/scripts/tune.py caps --repo <remote>`. Note any warnings for the final report. If `python3` is missing or the script fails, use the defaults in the Tiers table and say so in the report.
   - `--resume`: go to Resuming.
   - State the delivery boundary in one line: "I'll push new branches and open MRs for this task. I won't merge or write to tickets."
   - Read [../principle-never-block-on-the-human/SKILL.md](../principle-never-block-on-the-human/SKILL.md). It applies to the whole run.
2. **Frame.** Run [runbooks/frame.md](runbooks/frame.md). Output: the brief.
3. **Gauge.** Run [runbooks/gauge.md](runbooks/gauge.md). Print its one line and continue without waiting.
4. **Route.** Copy the tier's sequence from the Tiers table into the todo list, word for word. A step that doesn't apply stays in the list as `skip: <reason>`. Create the worktree and branch (see Workspace and branches).
5. **Plan** (tiers 1 to 3). Run [runbooks/plan.md](runbooks/plan.md).
6. **Review-plan** (tiers 2 and 3). Run [runbooks/review-plan.md](runbooks/review-plan.md).
7. **Implement.** Run [runbooks/implement.md](runbooks/implement.md).
8. **Review-diff** (tiers 2 and 3). Run [runbooks/review-diff.md](runbooks/review-diff.md).
9. **Raise-mr.** Run [runbooks/raise-mr.md](runbooks/raise-mr.md).
10. **Babysit.** Read [../babysit/SKILL.md](../babysit/SKILL.md) and follow its process with the PR or MR, or the whole stack, as the target. Tell the user what's being watched, the interval, and the time limit, and that closing the session stops the watch (see Babysit and session lifetime). Write a `cook state` block. Then end the turn.
11. **Triage the result.** When the watcher exits, read `babysit`'s diagnosis.
    - Green: go to step 12.
    - Red, and caused by the change (a test, lint, or build the diff broke): go back to step 7 with the diagnosis, push a fix commit to this run's branch, then repeat steps 9 and 10. At most `caps.fix_rounds` fix rounds. Still red after that: go to step 12.
    - Red, and not caused by the change (a flaky job, an infrastructure or network error, a failure that also exists on the default branch): go to step 12. Never re-run jobs.
12. **Final report.** Write it (see Final report), record the run in the ledger (see Tuning), and write a last `cook state` block with `step done`, or `step stopped` when the run stopped with work unfinished.

## Tiers

| Tier | Typical task | Sequence | Unit cap |
|---|---|---|---|
| 0 Trivial | known one-line or very local fix | frame → gauge → implement → raise-mr → babysit | 1 |
| 1 Small | one module, obvious approach | + plan (bullets, into the MR description) | 3 |
| 2 Standard | several files, some design choices | + review-plan, + review-diff | 8 |
| 3 Hard | cross-cutting, ambiguous, multi-repo | + how and why before plan, stacked raise-mr, babysit on the stack | 20 |

The unit caps shown are the defaults. The run uses the effective caps from `tune.py caps`, which may include the user's overrides.

**Risk triggers** set a floor of tier 2: security or auth, data or migrations, a public API, infrastructure or production config, deletions.

**Escalation triggers** raise the tier during the run:

- a plan that needs more units than the tier's cap
- more files or modules than Gauge expected
- unexpected callers, or another repo
- a unit that uses all its attempts
- a risk trigger appearing

Escalation keeps the work done so far, and the new tier's cap counts the units already done. The tier never goes down. Add the new tier's steps to the todo list: review-plan runs only on the units not yet implemented, and review-diff always runs before raise-mr.

## Effort checkpoint

When the units used reach the tier's cap, decide in this order:

1. Only delivery is left (raise-mr and babysit): finish.
2. An escalation trigger explains the extra units: escalate and continue.
3. Otherwise: stop. Report what's done, what's left, why it needed more, and the options: continue at the next tier, narrow the scope, or hand it over. Wait for the user.

## Where the run stops for you

- Frame: an open question blocks the goal.
- Review-plan: a hard limit fired, or the score is a near miss.
- The effort checkpoint, when nothing explains the extra units.
- Triage: the fix loop ran out, or the failure wasn't caused by the change. Report and stop.
- A restack that needs a force-push after the handoff to `babysit`.
- Multi-repo work: ask for the other repo's local path or clone URL, before Plan.
- `--resume`, when live state contradicts the recovered `cook state` block.

Everywhere else the run proceeds without waiting.

## Principles

Before applying a principle, read its full `SKILL.md` at the path below. The final report names each principle that changed a decision and the choice it changed, citing only principles actually read during this run. When a new principle is added to hstack, add a row here.

| Principle | Where | Tiers |
|---|---|---|
| [principle-never-block-on-the-human](../principle-never-block-on-the-human/SKILL.md) | the whole run | all |
| [principle-prove-it-works](../principle-prove-it-works/SKILL.md) | implement | all |
| [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md) | plan, review-diff | 1 to 3 |
| [principle-build-the-lever](../principle-build-the-lever/SKILL.md) | plan, implement, when edits are bulk or repetitive | 1 to 3 |
| [principle-encode-lessons-in-structure](../principle-encode-lessons-in-structure/SKILL.md) | review-diff, final report, when a correction recurs | 2 and 3 |

## Workspace and branches

Every run works in its own git worktree, tier 0 included. It never touches the user's checkout, and two runs never collide.

1. Find the default branch: `git symbolic-ref refs/remotes/origin/HEAD`. If that fails, `gh repo view --json defaultBranchRef` or `glab repo view -F json`.
2. Pick the branch name. Follow the repo's convention when it has one (CLAUDE.md, CONTRIBUTING, or the pattern recent merged branches use). Otherwise `hstack/cook-<slug>`, where the slug is the ticket key when there is one plus a short description, for example `hstack/cook-proj-123-fix-login-redirect`.
3. Pick the path: `<repo-parent>/<repo>.worktrees/<branch-slug>`, outside the repo.
4. If the branch or the path already exists, append `-2`, then `-3`, and so on. Never reuse or delete an existing branch or worktree.
5. `git fetch origin <default>`, then `git worktree add <path> -b <branch> origin/<default>`.
6. Switch the session into the worktree with Claude Code's `EnterWorktree` tool in `path` mode. The user invoked `cook`, which works in a worktree, so this is the asked-for use. Edits there then need no permission prompts. If `EnterWorktree` isn't available, `cd` into the worktree for every command.

`EnterWorktree` accepts a sibling path like this only once per session. Tier 3 creates each stacked MR's branch inside the same worktree, branching off the one below it. For multi-repo work, `cd` into the other repos' worktrees instead of entering them.

The worktree stays through the fix loop. After the final report, leave it with `ExitWorktree` and `action: "keep"`, since `ExitWorktree` doesn't remove a worktree entered by path. Then, from the main checkout, run `git worktree remove <path>`. The branch stays, because its PR or MR needs it. If the run stopped with work unfinished, skip the removal, keep the worktree for `--resume`, and say where it is.

## Multi-repo work

When Gauge or Implement finds that the task spans another repo, ask the user for that repo's local path, or where to get it (a clone URL). Don't guess from nearby directories. With a path, use that clone. With a URL, clone it next to the current repo: the user's answer is the authorization, and `cook` never clones anything the user didn't name. Each repo gets its own worktree, branch, and MR, and the MR descriptions link each other.

## Tickets

Ticket sources are read-only. `cook` never writes back to a ticket: no comments, transitions, links, or assignment. The ticket key in the branch name and MR title lets the hosts link the MR to the ticket on their side. Moving a ticket through a team's workflow stays with the user.

## Delivery

- **Authorized by invoking `/hstack:cook`:** pushing new branches this run created, opening their PRs or MRs (ready for review, or draft with `--draft`), and handing them to `babysit`.
- **Never authorized:** merging, pushing to branches this run didn't create, pushing to the default branch.
- **Force-push:** prefer new commits. A restack uses `--force-with-lease`, only on this run's branches, and only before the handoff to `babysit`. After that, ask.

## State and the cook state block

- The brief, the plan, and review notes live in the conversation and the scratchpad, never in the repo. When the user asks to save one of them, copy it to the location they name.
- The MR description carries the plan summary and source links, so the durable record lives with the MR.
- There is no separate work file. The `cook state` block in the transcript and the MR description are the record.

At every checkpoint (each step boundary and each implement unit), write one line in the message:

```
cook state · tier <n> · step <name> · units <done>/<cap> · attempts <list> · worktree <path> · branches <list> · MRs <list>
```

This line is what `--resume` finds later.

## Resuming

`/hstack:cook --resume` continues the most recent unfinished run in this repo.

1. Find the transcript folders: `~/.claude/projects/<slug>/`, where `<slug>` is an absolute path with every `/` replaced by `-`. Check the repo's own path and the path of each worktree from `git worktree list`.
2. Grep their `*.jsonl` files for the literal `cook state ·`. Skip blocks whose step is `done`, and runs whose newest block is `done`. Take the newest remaining block by the entry's `timestamp`.
3. Read [../recall/SKILL.md](../recall/SKILL.md) and run it, scoped to this repo, only for surrounding context: decisions made, open questions, the brief.
4. Check the block against live state: the worktree exists, the branches and their commits match, the MRs are in the state the block says.
5. Show the recovered state in one line and continue from the recorded step. If live state contradicts the block (worktree gone, branch rewritten), report the difference and stop. If no block is found, say so and stop.

Claude Code deletes transcripts after 30 days by default (`cleanupPeriodDays`), so an older run can't be resumed this way.

## Babysit and session lifetime

The `babysit` watcher runs in the session's background. If the user closes the session before CI finishes, no report arrives. Say so at the handoff. Running `/hstack:babysit <MR>` later picks the watch back up.

## Tuning

**Effective caps.** `tune.py caps --repo <remote>` merges, most specific first: the repo's section of the overrides file, the top-level overrides, the defaults. It prints each cap with its source. `--tier` on the command line picks the tier, not the caps.

**State directory.** `$HSTACK_HOME` when set, otherwise `~/.claude/hstack/`. It sits outside every repo and the plugin cache, so plugin updates never touch it. It holds:

- `cook-runs.jsonl`: the run ledger, one line per finished run.
- `cook.json`: cap overrides. Only `--tune` writes it.

**Recording a run.** At the end of every run, including stopped ones, pipe one JSON object to `python3 <skill-dir>/scripts/tune.py record`:

```json
{"repo": "<remote>", "date": "YYYY-MM-DD", "outcome": "green|red|stopped", "gauge_tier": 1, "final_tier": 1,
 "escalations": [{"from": 1, "to": 2, "trigger": "plan needed 5 units"}], "units_planned": 3, "units_used": 3,
 "attempts": [1, 1, 2], "stuck_units": 0, "review_rounds": 0, "fix_rounds": 0, "gauge_ops": 8, "tier_override": null}
```

`tier_override` is the `--tier` value, or `null` when Gauge's tier stood. If `record` rejects the object, fix the field it names and retry. A failure to record never changes the run's outcome; mention it in the report.

**`--tune`.**

1. Run `python3 <skill-dir>/scripts/tune.py suggest --repo <remote>` (leave out `--repo` outside a git repo).
2. Show each suggestion with its evidence, the notes, and the baseline from the morpheus-os calibration. With too few runs there are no suggestions; say how many runs exist.
3. Ask which suggestions to apply.
4. For each approved one, run `python3 <skill-dir>/scripts/tune.py apply --change <path>=<value> [--repo <remote>] --evidence "<evidence>"`. A suggestion scoped to a repo applies with `--repo`.

`--tune` always waits for the user's choice. This overrides `principle-never-block-on-the-human` here: with no answer, it writes nothing.

## Doctor

`/hstack:cook --doctor` checks prerequisites without starting a task. It is read-only: it names fixes and never runs installs or logins. Print a checklist where each line is pass, fail, or not checked, with the fix for each failure. A check is not checked when the session's permissions blocked its command: name the command so the user can run it or allow it.

Get the state directory and config checks from one command, `python3 <skill-dir>/scripts/tune.py caps`, whose `"state"` field reports the directory, whether it exists, and whether it is writable, and whose `warnings` report a broken `cook.json`. Don't expand `$HSTACK_HOME` or list `~/.claude/hstack/` by hand.

- `git` is present, this is a git repo with an `origin`, and `git worktree list` works. Outside a git repo, this line fails and the rest still run.
- The repo's host, from `origin`, and its CLI installed and signed in: `gh auth status` for GitHub, `glab auth status` for GitLab. Otherwise, whether a matching MCP server is connected.
- `python3` is present.
- The state directory (`$HSTACK_HOME` or `~/.claude/hstack/`) exists and is writable, or can be created.
- `cook.json` is absent (defaults in use), valid (list the overrides), or broken (show `tune.py caps` warnings).
- The Jira connector `frame` would use: `acli`, `jira-cli`, an MCP server, or none, meaning tickets get pasted.
- The skills `cook` reads are present next to it: `babysit`, `recall`, `hermes`, `how`, `why`, and the five principles.

## Final report

Write it through [../hermes/SKILL.md](../hermes/SKILL.md), including its `unslop` pass:

- the outcome, in one sentence
- the tier, why it was chosen, and any escalations
- what changed, with PR or MR links and pipeline links
- the cause of any failure still red, and what was tried
- the principles that shaped decisions, citing only those read during this run
- effort used against the tier's caps, naming any cap that came from an override
- gaps and assumptions, including unverified units and declined review findings
- what's next for the user
