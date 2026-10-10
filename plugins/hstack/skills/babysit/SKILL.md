---
name: babysit
description: "Watch any long-running target in the background until it reaches a finished state, then report the outcome and, for failures, why. Only watches targets that have a runbook. Runbooks exist today for GitHub pull requests and GitLab merge requests, including stacks."
disable-model-invocation: true
---

# Babysit

Babysit watches a target until it reaches a finished state, without the user in the loop, then reports what happened. A target is anything that runs for a while and then succeeds or fails: a pull request's pipeline, a deploy, a batch job, a release. Babysit only watches targets that have a runbook. The runbook knows the target. This skill owns the process, and every runbook follows it.

## Runbooks

| Target | Runbook |
|---|---|
| GitHub pull requests, including stacks | [runbooks/github-pr.md](runbooks/github-pr.md) |
| GitLab merge requests, including stacks | [runbooks/gitlab-mr.md](runbooks/gitlab-mr.md) |

If the request matches no runbook, stop. Say there is no runbook for that target, and offer to write one that meets the contract below. Don't improvise a watch.

Runbooks may call scripts in this skill's `scripts/` directory. Run them by absolute path from the skill's base directory, shown as `<skill-dir>` in the runbooks.

## Process

Follow these steps in order. Don't skip one.

1. **Route.** Pick the runbook that matches the request. If more than one could match, use the runbook's Targets section to decide, and ask only if they still tie.
2. **Resolve.** Follow the runbook's Resolve section to turn the request into a concrete list of targets. If the targets form a group with an order, such as a stack, keep that order. State the list in one line and keep going.
3. **Calibrate.** Follow the runbook's Calibrate section to get the poll interval and time limit from the recent history of the same kind of target. An interval or limit the user named overrides the calibrated one.
4. **Watch.** Start the runbook's watch command with the Bash tool and `run_in_background: true`. Use one watcher per request, covering every target. Tell the user in one or two sentences what you're watching, the interval, and the time limit. Then end your turn, or carry on with other work the user asked for. Don't poll by hand and don't sleep. Claude Code notifies you when the watcher exits.
5. **Diagnose.** When the watcher exits, read its output. For each target that failed, follow the runbook's Diagnose section and work out the cause from the evidence it returns. If the evidence doesn't show the cause, gather more with the runbook's read-only commands.
6. **Report.** Write the report described below.

## Rules

- **Observe only.** Babysit never changes the target or anything around it. Each runbook's Read-only section lists the actions that are off limits for its target. Babysit reports. The user acts.
- **CLI first, MCP as fallback.** Each runbook names its CLI and an auth check. If the CLI is missing or not signed in and an MCP server for the target is available, use the MCP fallback below. If neither works, report a gap and name the login command for the user to run. Never run a login command yourself.
- **One watcher per target.** If a target is already being watched in this session, say so instead of starting a second watcher.
- **Time limits.** If the watcher hits its time limit, report the unfinished targets as still running, with links. Don't restart the watch unless the user asks.

### MCP fallback

The background watch command needs the CLI. Without it, spawn one `general-purpose` subagent with `run_in_background: true`. Give it the target list, the interval, the time limit, and the runbook's MCP notes. Tell it to stay read-only, poll with the MCP tools, and wait between polls with `sleep <interval>` in Bash. It stops when every target has finished or the time limit passes, then runs the runbook's Diagnose steps with the MCP tools. It returns the same shape the watch command emits. You write the report from that.

## Report

Write the report through `/hstack:hermes` (read [../hermes/SKILL.md](../hermes/SKILL.md) and apply it, including the `unslop` pass it requires).

1. **Lead with the outcome** in one sentence: how many targets finished and how many failed, naming the failures.
2. **One entry per target**, in the order from Resolve. Each entry gives the target's link, its final state, and the fields the runbook's Report section adds. For each failure, add one to three sentences on why it failed.
3. **Notes**, when they apply: the notes the runbook's Report section lists, plus time limits that passed and gaps such as evidence you couldn't reach.
4. **Close with the interval and time limit** you used and where they came from.

In each failure summary, name the thing that failed and quote the key error in code font. Separate what the evidence shows from what you infer. Never paste raw evidence in bulk.

## Runbook contract

Every runbook in `runbooks/` has these sections:

- **Targets.** What it watches, and the requests that match it.
- **Tooling.** The CLI it prefers, the auth check, and the MCP fallback.
- **Read-only.** The actions that would change the target and are off limits.
- **Resolve.** How a request becomes concrete targets, including any ordered group such as a stack.
- **Calibrate.** How the recent history of the same kind of target sets the interval and time limit. Sample the last 10 finished runs. The interval is the shortest run time and the time limit is 3 times the longest. Clamp both, and use a fallback when there is no history. The existing runbooks clamp the interval to 30 seconds through 10 minutes (60-second fallback) and the time limit to 15 minutes through 6 hours (2-hour fallback). A target with much longer runs may justify other bounds. Say why in the runbook.
- **Watch.** The background command, the target's finished states, and how it handles a target that restarts or never starts. The command exits when every target has finished or the time limit passes. It emits JSON with `elapsed_seconds`, `timed_out`, `interval`, `timeout`, and one entry per target with its status and link.
- **Diagnose.** Read-only steps that return the evidence for a failure, such as log excerpts.
- **Report.** The fields each target's entry adds, and the notes worth raising.

To add a runbook, write the file, add a row to the Runbooks table, and put the calibrate, watch, and diagnose logic in a script under `scripts/` so it runs the same way every time and can be tested.
