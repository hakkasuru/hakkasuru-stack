# GitHub issues

## Matches

- `github.com/<owner>/<repo>/issues/<n>` URLs.
- A bare `#<n>` when `git remote -v` points at `github.com`.

## Tooling

Check `gh auth status`. If it fails, `gh` isn't usable. Don't run `gh auth login`.

MCP fallback: a GitHub MCP server's tools for getting an issue and listing its comments. Tool names vary by server, and deferred tools load with ToolSearch. If neither works, record a gap, say the user can sign in with `gh auth login`, and ask them to paste the issue.

## Read-only

Never comment on, close, reopen, label, assign, or edit the issue.

## Fetch

```bash
gh issue view <n> -R <owner>/<repo> --json number,title,body,labels,milestone,comments,url
```

## Follow

Depth 1. Fetch issues and PRs referenced in the body or comments on the same host, as `#123` or full URLs. A link to another host routes back to frame, which matches it to that host's playbook or records it as a gap.

## Extract

- **Goal:** the title and body.
- **Acceptance criteria:** checklists, and sections headed "Acceptance", "Expected", or similar.
- **Constraints:** labels and the milestone, plus comments that narrow scope.
- **Out of scope:** comments that drop part of the request.
- **Open questions:** questions in the body or comments that nobody answered.
- **Conflicts:** when a later comment changes scope, the newest wins, and the change is recorded.
- **Sources:** the issue URL and each followed item's URL.
