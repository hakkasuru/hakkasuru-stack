# GitHub pull requests

## Targets

A GitHub pull request, or a stack of them. Requests look like a PR number (`#123`), a PR URL, a branch name, "my PR", "this stack", or the current branch. A PR's pipeline is its set of checks: GitHub Actions jobs plus any external status checks.

## Tooling

Prefer the `gh` CLI through [`scripts/github.py`](../scripts/github.py), which needs `python3`. Run it by absolute path from this skill's base directory.

1. Check the CLI: `gh auth status`. If it fails, the CLI isn't usable. Don't run `gh auth login`.
2. Pick the repo. Inside the repo's checkout, leave `-R` off. Otherwise pass `-R OWNER/REPO`, taken from the PR URL or `git remote -v`.

**MCP fallback.** If `gh` is missing or not signed in and a GitHub MCP server is available (tools named `mcp__<server>__*`, loaded with ToolSearch if deferred), use it for each step below. Names vary by server. You need tools that get a pull request and its head commit, list the check runs or status for a commit, list PRs by head or base branch, and fetch a job's logs. Follow the MCP fallback in [SKILL.md](../SKILL.md) for watching. If neither the CLI nor an MCP works, report a gap and say the user can sign in with `gh auth login`.

## Read-only

Never re-run, retry, or cancel a check or workflow. Never push, comment, review, approve, merge, close, or change labels.

## Resolve

```bash
python3 <skill-dir>/scripts/github.py [-R OWNER/REPO] stack <pr>
```

- Returns `prs` ordered bottom first, the `trunk` branch the stack lands on, and `branches` where one PR has several children.
- It follows open PRs only. Down: the PR whose head branch is this PR's base. Up: PRs whose base is this PR's head.
- For a branch name, resolve the PR first with `gh pr view <branch> --json number`.
- If `branches` is not empty, watch every PR and say in the report where the stack forks.

## Calibrate

```bash
python3 <skill-dir>/scripts/github.py [-R OWNER/REPO] calibrate
```

- Samples the last 10 merged PRs. A PR's pipeline time is its longest single check, since checks run in parallel. The span from the first start to the last finish is not used, because re-runs and label-triggered workflows stretch it across days.
- `interval` is the shortest pipeline time, clamped to 30 seconds through 10 minutes. `timeout` is 3 times the longest, clamped to 15 minutes through 6 hours.
- With no usable history it falls back to a 60-second interval and a 2-hour timeout. `source` says which applied.

## Watch

Start it with the Bash tool and `run_in_background: true`:

```bash
python3 <skill-dir>/scripts/github.py [-R OWNER/REPO] watch --interval <interval> --timeout <timeout> <pr> [<pr>...]
```

- A PR is finished when it has checks and none are pending. It watches every check, not only required ones.
- Final statuses: `success`, `failed` (any check failed), `canceled`, `no_pipeline` (no checks after 3 polls), `merged` or `closed` (with no checks), `error` (the CLI call failed), and `running` (the timeout passed first, with `timed_out: true`).
- A new push changes the head commit. The watcher follows the new checks and lists the old commit in `superseded`.

## Diagnose

For each PR with status `failed`:

```bash
python3 <skill-dir>/scripts/github.py [-R OWNER/REPO] diagnose <pr> [--lines 80]
```

- Returns each failed check with `job_url`, `run_url`, and `log_excerpt`. The excerpt starts a little before the first `##[error]` line and runs to the last one, so runner cleanup noise is left out.
- External checks (not GitHub Actions) have no log through `gh`. Report the `job_url` and say the log lives in that system.
- If the excerpt doesn't show the cause, read more of the log with `gh run view --job <job-id> --log-failed` or the whole run with `gh run view <run-id> --log`.

## Report

Order entries bottom of the stack first. Each entry adds:

- the PR link (`url`)
- the pipeline link: the workflow run, `run_url`. A PR can have several failing runs. Link each one.
- for each failed check: its name and `job_url`, then the cause. Name the failing command, test, or file.

Notes worth raising: a superseded head commit (a push landed mid-watch), a PR with no checks, an external check whose log you couldn't read, and a stack that forks.

Close with where the interval came from, for example "Polled every 7m 52s for up to 45m, from 10 merged PRs."
