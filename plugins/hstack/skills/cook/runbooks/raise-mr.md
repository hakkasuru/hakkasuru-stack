# Raise MR

Push the run's branches and open their PRs or MRs. Invoking `/hstack:cook` is the user's authorization for exactly this, within the boundary below.

## Boundary

- Push only branches this run created. Never push another branch, and never the default branch.
- Never merge, approve, or enable auto-merge.
- Force-push only to restack, with `--force-with-lease`, only on this run's branches, and only before the handoff to `babysit`. After the handoff, ask the user first.

## Push

Push each branch, bottom of the stack first:

```bash
git push -u origin <branch>
```

In a fix round, push the new commits to the existing branch. The open PR or MR picks them up. Don't open another one, and skip Open below.

## Open

Write the title and the description to files in the scratchpad first (`<title-file>`, `<description-file>`). Then open the PR or MR through the host's API, where `-F key=@<file>` makes the CLI read the value from the file. Never put ticket-derived text inside a shell argument, and don't use command substitution like `$(cat ...)`: a title containing `$(...)` or backticks would run as a command, and Claude Code's permission checks block substitution anyway. Stack: each one's base is the branch below it, and the bottom one's base is the default branch.

GitHub, from inside the repo (`{owner}/{repo}` fills in from the checkout):

```bash
gh api repos/{owner}/{repo}/pulls -f head=<branch> -f base=<base> -F title=@<title-file> -F body=@<description-file> -F draft=false
```

GitLab, from inside the repo (`:id` fills in from the checkout; add `--hostname <host>` for a self-managed instance):

```bash
glab api projects/:id/merge_requests -f source_branch=<branch> -f target_branch=<base> -F title=@<title-file> -F description=@<description-file> -F squash=true
```

The response's `html_url` (GitHub) or `web_url` (GitLab) is the link to report.

With `--draft`: on GitHub, pass `-F draft=true`. On GitLab, start the title file with `Draft: `. Otherwise the PR or MR opens ready for review.

## Merge strategy

Squash on merge, unless the repo's conventions say otherwise (CLAUDE.md, CONTRIBUTING, or the merge style of recent merged PRs or MRs). On GitLab, `-F squash=true` sets it on the MR; drop that field when the repo's convention is to keep commits. GitHub has no per-PR flag, and setting it through auto-merge would be merging, so leave it to the repo's settings.

## Title and description

Write both through [../../hermes/SKILL.md](../../hermes/SKILL.md), including its `unslop` pass.

- The title carries the ticket key when the brief has one, for example `PROJ-123: Fix login redirect loop`. Jira, GitHub, and GitLab link the MR to the ticket from the key, with no write to the ticket.
- The description is a briefing a reviewer reads in under a minute: what changed, why, how it was verified, and what to look at. Link the brief's sources. At tier 1 and above, include the plan summary. Never paste logs or long output; link them.
- In a stack, each description states its position ("2 of 4") and links the PRs or MRs above and below it. Update the lower ones' descriptions as the upper ones open.

## Don't

- Assign reviewers or add labels. The repo's own setup (CODEOWNERS, default reviewers) handles that.
- Write to tickets.

## Without a CLI

If `gh` or `glab` is missing or not signed in, use the host's MCP server tool for creating a PR or MR. If neither works, stop, keep the pushed branches, and report a gap naming `gh auth login` or `glab auth login`.

## Output

The PR or MR URLs, bottom of the stack first. `babysit` takes these as its targets.
