# Jira tickets

## Matches

- A ticket key matching `\b[A-Z][A-Z0-9]+-\d+\b`, but only when it is given as an input on its own. A key-shaped token inside prose, such as `SHA-256`, `UTF-8`, or `ISO-8601`, is not fetched. Record it under Assumptions instead.
- URLs `https://<site>.atlassian.net/browse/<KEY>`, and self-hosted `https://<host>/browse/<KEY>`.

## Tooling

Detect a connector in this order:

1. `acli`, Atlassian's CLI. Check `acli jira auth status`.
2. `jira`, from jira-cli. Check `jira me`.
3. An Atlassian or Jira MCP server's tool for getting an issue. Deferred tools load with ToolSearch.

If none works, record a gap naming both install options (`acli` or `jira-cli`) and ask the user to paste the ticket. Never run a login command.

## Read-only

Never comment on, transition, link, assign, log work on, or edit the ticket.

## Fetch

```bash
acli jira workitem view <KEY> --json
jira issue view <KEY> --raw
```

These commands are unverified: neither CLI was installed when this playbook was written. Before the first fetch, confirm the exact subcommand with `acli jira workitem view --help` or `jira issue view --help`. If they differ, use what the help shows and fix this playbook.

## Follow

Depth 1.

- The parent epic.
- Sub-tasks.
- Issue links of type "blocks", "is blocked by", and "relates to".

Confluence pages and other links have no playbook. Record them as gaps with their URLs.

## Extract

- **Goal:** the summary and description.
- **Acceptance criteria:** an "Acceptance criteria" field, or a heading of that name in the description.
- **Constraints:** fix version, components, and labels. The parent epic's goal goes here as context.
- **Out of scope:** comments that drop part of the request.
- **Open questions:** questions in the description or comments that nobody answered.
- **Conflicts:** when a later comment changes scope, the newest wins, and the change is recorded.
- **Sources:** the ticket URL and each followed ticket's URL.
