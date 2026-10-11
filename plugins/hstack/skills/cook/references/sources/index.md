# Requirement sources

These playbooks are how [../../runbooks/frame.md](../../runbooks/frame.md) fetches requirements. Frame matches each input against a playbook's Matches section, then follows that playbook's Fetch, Follow, and Extract sections to build the brief. Every playbook is read-only.

| Source | Matches | CLI | MCP fallback |
|---|---|---|---|
| [jira.md](jira.md) | `PROJ-123`, `*.atlassian.net/browse/...` | `acli` or `jira-cli`, whichever is installed and signed in | Atlassian or Jira MCP |
| [github-issue.md](github-issue.md) | `#123` in a GitHub repo, `github.com/.../issues/...` | `gh issue view` | GitHub MCP |
| [gitlab-issue.md](gitlab-issue.md) | `#123` in a GitLab repo, `.../-/issues/...` | `glab issue view` | GitLab MCP |

A link into a source with no playbook, such as a Confluence page or a Google Doc, is recorded in the brief as a gap with its URL. It is not fetched.

## Playbook contract

Every playbook has these sections:

- **Matches.** The ticket keys or URLs it handles.
- **Tooling.** The CLI and its auth check, then the MCP fallback.
- **Read-only.** Never comment on, transition, link, assign, or edit an item.
- **Fetch.** The commands it runs.
- **Follow.** Which links it pulls and how deep.
- **Extract.** Which fields map to which brief sections: goal, acceptance criteria, constraints, out of scope, open questions, sources.

## Adding a source

1. Write `<source>.md` with the six sections above.
2. Add a row to the table.
3. Keep it read-only.
4. Prefer the source's CLI, with an auth check, and fall back to an MCP server. Never run a login command. An unreachable source is a gap that names the install or login step.
5. Verify it by fetching one real item read-only before committing.
