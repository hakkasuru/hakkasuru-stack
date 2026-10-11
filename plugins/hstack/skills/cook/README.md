# Cook

`/hstack:cook` takes a task from a prompt, a Jira ticket, or an issue link to a merge-ready pull request or merge request. It frames the requirements, sizes the task, plans, implements, opens the MR, and watches its pipeline. How much process it runs depends on the task: a one-line fix goes straight from edit to MR, and a cross-cutting change gets a reviewed plan and a stack of MRs.

Use it when you want a task done end to end and are happy to review the MR it opens.

## Before your first run

Run the doctor in the repo you'll work in:

```
/hstack:cook --doctor
```

It checks your tools and prints the fix for anything missing. It never installs anything or signs you in.

## Requirements

- `git`.
- `gh` signed in, for GitHub repos, or `glab` signed in, for GitLab repos. `cook` uses them to open MRs and watch pipelines.
- `python3`, for effort caps and pipeline watching. macOS ships it.
- Optional: `acli` or `jira-cli` for Jira tickets, or a connected Atlassian or Jira MCP server. Without one, `cook` asks you to paste the ticket.

No other setup is needed. Defaults ship with the plugin, and `cook` creates its state directory on first use.

## Usage

Describe the task in words:

```
/hstack:cook fix the typo in the login button label
```

Point it at a ticket or an issue:

```
/hstack:cook PROJ-123
/hstack:cook https://github.com/acme/web/issues/42
```

Or mix them. `cook` merges every source into one brief:

```
/hstack:cook PROJ-123 https://gitlab.com/acme/api/-/issues/7 also update the docs
```

## Flags

| Flag | Effect |
|---|---|
| `--tier N` | Force tier `N` (0 to 3) instead of the one `cook` picks. A risky change still gets at least tier 2. |
| `--draft` | Open draft PRs or MRs instead of ones ready for review. |
| `--resume` | Continue the most recent unfinished run in this repo. |
| `--tune` | Suggest effort-cap changes from your past runs, and apply the ones you approve. |
| `--doctor` | Check prerequisites without starting a task. |

## Tiers

`cook` picks a tier after a quick read-only scan of the code. The tier decides which steps run and how many units of work the task gets. A unit is one change that ends in a check that can fail.

| Tier | Typical task | Sequence | Unit cap |
|---|---|---|---|
| 0 Trivial | known one-line or very local fix | frame → gauge → implement → raise-mr → babysit | 1 |
| 1 Small | one module, obvious approach | + plan (bullets, into the MR description) | 3 |
| 2 Standard | several files, some design choices | + review-plan, + review-diff | 8 |
| 3 Hard | cross-cutting, ambiguous, multi-repo | + how and why before plan, stacked raise-mr, babysit on the stack | 20 |

Changes that touch security, data or migrations, a public API, infrastructure or production config, or deletions get at least tier 2. If the work turns out bigger than expected, `cook` moves up a tier and keeps what it has done. It never moves down.

The unit caps come from 58 finished tasks: each cap is the 80th percentile of steps those tasks needed. You can tune them to your own work with `--tune`.

## What it will and won't do

`cook` will:

- work in its own git worktree, next to your repo, so your checkout is never touched
- push the new branches it creates
- open their PRs or MRs, then watch the pipelines and report the result
- fix a pipeline failure its own change caused, up to twice

`cook` won't:

- merge anything
- push to a branch it didn't create, or to the default branch
- comment on, move, or edit tickets
- assign reviewers or add labels
- re-run CI jobs

## Where it stops for you

It keeps going on its own except:

- when an open question blocks the goal
- when a plan review hits a hard limit, such as a destructive step or security scope
- when the task needs more units than its tier allows and nothing explains why
- when the pipeline is still red after two fix attempts, or failed for a reason the change didn't cause
- when the task needs another repo: it asks for the local path or clone URL
- when a stack needs a force-push after the pipeline watch has started
- when `--resume` finds a saved state that no longer matches the worktree or the MRs

## Resuming

If a run stops partway, its worktree stays in place. In a later session, run:

```
/hstack:cook --resume
```

`cook` finds the last checkpoint in your Claude Code session history, checks it against the worktree and the MRs, and continues from there. Session history is kept for 30 days by default, so older runs can't be resumed this way.

## Tuning and your data

`cook` keeps two files in `~/.claude/hstack/`, outside every repo and the plugin, so plugin updates never touch them:

- `cook-runs.jsonl` records each finished run: the tier, the units used, escalations, and the outcome.
- `cook.json` holds your cap overrides. Only `--tune` writes it, and only after you approve each change.

After about 20 runs, or 5 at one tier, run `/hstack:cook --tune` to see suggested cap changes with the evidence behind each.

## Troubleshooting

- **"No connector" for a ticket.** Install and sign in to `acli` or `jira-cli`, or connect an Atlassian MCP server. Until then, paste the ticket when asked.
- **The MR can't be opened.** Run `gh auth login` or `glab auth login`. The pushed branches stay in place.
- **No pipeline report arrived.** The watcher stops if you close the session while CI runs. Run `/hstack:babysit <MR link>` to watch it again.
- **Something else.** Run `/hstack:cook --doctor`.
