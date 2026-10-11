# GitLab issues

## Matches

- `https://<host>/<group>/<project>/-/issues/<n>` URLs, on gitlab.com or a self-managed host.
- A bare `#<n>` when `git remote -v` points at a GitLab host.

## Tooling

Check `glab auth status` for the issue's host. If it fails, `glab` isn't usable. Don't run `glab auth login`.

MCP fallback: a GitLab MCP server's tools for getting an issue, its notes, and its links. Tool names vary by server, and deferred tools load with ToolSearch. If neither works, record a gap, say the user can sign in with `glab auth login`, and ask them to paste the issue.

## Read-only

Never comment on, close, reopen, label, assign, or edit the issue.

## Fetch

```bash
glab issue view <n> -R <group>/<project> --comments -F json
```

For a self-managed host, pass the full issue URL to `-R` or run from inside that project's checkout.

## Follow

Depth 1.

- Linked issues: `glab api projects/<url-encoded group/project>/issues/<n>/links`.
- Issues and MRs referenced in the description or comments, as `#123`, `!45`, or full URLs.
- Epics need a GitLab Premium API and are usually out of reach. Record a linked epic as a gap with its URL.

A link to another host routes back to frame.

## Extract

- **Goal:** the title and the `description` field.
- **Acceptance criteria:** checklists, and sections headed "Acceptance", "Expected", or similar.
- **Constraints:** labels and the milestone, plus comments that narrow scope.
- **Out of scope:** comments that drop part of the request.
- **Open questions:** questions in the description or comments that nobody answered.
- **Conflicts:** when a later comment changes scope, the newest wins, and the change is recorded.
- **Sources:** the issue URL and each followed item's URL.
