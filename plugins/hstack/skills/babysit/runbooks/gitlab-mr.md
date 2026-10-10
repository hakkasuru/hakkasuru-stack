# GitLab merge requests

## Targets

A GitLab merge request, or a stack of them. Requests look like an MR number (`!123`), an MR URL, a branch name, "my MR", "this stack", or the current branch. An MR's pipeline is its head pipeline, which can differ from the branch pipeline that `glab ci status` shows.

## Tooling

Prefer the `glab` CLI through [`scripts/gitlab.py`](../scripts/gitlab.py), which needs `python3`. Run it by absolute path from this skill's base directory.

1. Check the CLI: `glab auth status`. If it fails for the MR's host, the CLI isn't usable. Don't run `glab auth login`.
2. Pick the project. Inside the project's checkout, leave `-R` off. Otherwise pass `-R GROUP/PROJECT`, taken from the MR URL or `git remote -v`. For a self-managed instance outside the checkout, also pass `--hostname <host>`.

**MCP fallback.** If `glab` is missing or not signed in and a GitLab MCP server is available (tools named `mcp__<server>__*`, loaded with ToolSearch if deferred), use it for each step below. Names vary by server. You need tools that get a merge request with its head pipeline, list MRs by source or target branch, list a pipeline's failed jobs and bridges, and fetch a job's log. Follow the MCP fallback in [SKILL.md](../SKILL.md) for watching. If neither the CLI nor an MCP works, report a gap and say the user can sign in with `glab auth login`.

## Read-only

Never retry, re-run, play, or cancel a job or pipeline. Never push, comment, approve, merge, close, or change labels.

## Resolve

```bash
python3 <skill-dir>/scripts/gitlab.py [-R GROUP/PROJECT] stack <mr>
```

- Returns `mrs` ordered bottom first, the `trunk` branch the stack lands on, and `branches` where one MR has several children.
- It follows open MRs only. Down: the MR whose source branch is this MR's target. Up: MRs whose target is this MR's source.
- For a branch name, resolve the MR first with `glab mr view <branch> -F json`.
- If `branches` is not empty, watch every MR and say in the report where the stack forks.

## Calibrate

```bash
python3 <skill-dir>/scripts/gitlab.py [-R GROUP/PROJECT] calibrate
```

- Samples the last 10 merged MRs and reads the `duration` of each one's latest pipeline. Only pipelines that succeeded count, since a failed pipeline can stop in seconds.
- `interval` is the shortest duration, clamped to 30 seconds through 10 minutes. `timeout` is 3 times the longest duration plus queue time, clamped to 15 minutes through 6 hours.
- With no usable history it falls back to a 60-second interval and a 2-hour timeout. `source` says which applied.

## Watch

Start it with the Bash tool and `run_in_background: true`:

```bash
python3 <skill-dir>/scripts/gitlab.py [-R GROUP/PROJECT] watch --interval <interval> --timeout <timeout> <mr> [<mr>...]
```

- An MR is finished when its head pipeline reaches `success`, `failed`, `canceled`, `skipped`, or `manual`. `manual` means the pipeline waits on a person to start a job. Report it as blocked on that job, not as passed.
- Other final statuses: `no_pipeline` (no head pipeline after 3 polls), `merged` or `closed` (with no pipeline), `error` (the CLI call failed), and `running` (the timeout passed first, with `timed_out: true`).
- A new push or a re-run creates a new head pipeline. The watcher follows it and lists the old pipeline in `superseded`.

## Diagnose

For each MR with status `failed`:

```bash
python3 <skill-dir>/scripts/gitlab.py [-R GROUP/PROJECT] diagnose <mr> [--lines 80]
```

- Returns each failed job with `job_url`, `stage`, `failure_reason`, `allow_failure`, and `log_excerpt`. The excerpt drops ANSI codes, timestamps, and the `after_script`, artifact upload, cache, and cleanup sections, then keeps the last lines.
- A job with `allow_failure: true` didn't fail the pipeline. Mention it as a note, not as the cause.
- A failed bridge job triggers a child or downstream pipeline. The script follows it up to two levels and nests those failures under `downstream_failures`.
- MRs from forks run their pipeline in the fork's project. The script queries the pipeline's own project, so the links point at the fork.
- If the excerpt doesn't show the cause, read the full log with `glab api projects/<project-id>/jobs/<job-id>/trace`.

## Report

Order entries bottom of the stack first. Each entry adds:

- the MR link (`url`)
- the pipeline link (`pipeline_url`), plus `downstream_pipeline_url` for a failed child pipeline
- for each failed job: its name, stage, and `job_url`, then the cause. Name the failing command, test, or file.

Notes worth raising: a superseded pipeline (a push or re-run mid-watch), a pipeline waiting on a manual job, failed jobs that were allowed to fail, an MR with no pipeline, a pipeline that ran in a fork, and a stack that forks.

Close with where the interval came from, for example "Polled every 10m for up to 64m, from 10 merged MRs."
