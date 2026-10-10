# Add a source playbook

Read this when you add a new evidence source to `/hstack:why`: a CLI (`az`, `kubectl`, `jira`) or an MCP (Linear, Notion, Sentry). Don't give it to investigators. They get the finished playbook.

A playbook tells an investigator, who reads it cold, how to pull motivation evidence out of one source. The rules below come from the playbooks this skill has carried: git, Slack, Datadog, AWS, and Google Cloud, plus earlier ones for Linear, Notion, Sentry, and Databricks.

## 1. Decide what the source is for

1. Name the one "why" the source holds that no other source does. Ticket trackers hold the business forcing function. Docs hold long-form rationale written before the code. Chat holds deliberation that never reached a doc. Runtime sources (observability, error tracking, analytics, cloud) hold the production reality around the change date. If you can't name it, the source probably doesn't need a playbook.
2. Assign it to exactly one of the seven categories in `SKILL.md`. If it fits two, pick the one that matches its primary evidence. Add a new category only if none fits. That also means updating the category list, the roster, and the Sources Consulted format in `synthesizer-prompt.md`.
3. Pick the tool. Prefer a terminal CLI over an MCP when both exist. A CLI is scriptable, shows the exact command for the citation, and doesn't need an MCP server installed.

## 2. Write the playbook

Create `sources/<source>.md`, named after the tool (`aws.md`, `linear.md`). Use these sections in this order. Copy the shape of [aws.md](./sources/aws.md) for a CLI or [datadog.md](./sources/datadog.md) for an MCP.

### Title

`# <Source> (via <tool>)`, for example `# AWS (via the aws CLI)`.

### What this source contains

- One bullet per evidence type, each with a sentence on why it matters for motivation, not what it is in general. "A monitor's threshold is direct evidence the team worried about that number" beats "Monitors alert on conditions."
- End with one line naming the question the source answers, for example "AWS answers 'what did the infrastructure require or report around the time this code was written?'"
- Name the parts that exist but can't be searched (Databricks notebooks behind a SQL-only MCP, Slack DMs, Data Access audit logs that are off by default), so the investigator reports them as gaps.

### Read-only rules

Required for any CLI, and for any MCP that has write tools.

- List the allowed command verbs or tool names explicitly (`describe-*`, `list-*`, `get-*`). List the forbidden ones too.
- Make the investigator pass scope flags (`--profile`, `--project`, `--region`) on every command instead of changing the user's CLI config.
- Forbid login commands. An unauthenticated source is a gap, and the playbook names the command the user can run to sign in. For an MCP, that is `/mcp`.
- Ask for machine-readable output (`--output json`, `--format=json`) and turn off pagers.

### How to search it

Numbered steps, each with real commands or real MCP tool names in a code block. The steps that paid off across every source:

1. **Orient and confirm scope first.** Find the account, project, workspace, organization, or region before searching (`aws sts get-caller-identity`, Sentry's `find_organizations`). Take the scope from the repo's config where you can, and record it. A null result from the wrong scope is not a null result.
2. **Probe names before trusting them.** Schemas, table names, channel names, and MCP tool signatures vary by company and by server. List or describe first (`SHOW TABLES`, inspect the tool schema). Reporting a result from a table nobody confirmed exists is a classic failure.
3. **Start from the code anchor.** Fetch the IDs the commits and PRs already name (ticket IDs, Sentry URLs, incident IDs, PR URLs) before running any keyword search.
4. **Read curated artifacts before raw data.** Dashboards, monitors, alarms, parent tickets, and project docs show what the team decided mattered. Raw logs and events come after.
5. **Go wide, then narrow.** Try several phrasings of the feature name, symbols, error strings, and author names. Then narrow to the items that match.
6. **Bound every query in time.** Use a window of about 30 days before and after the target's merge date. Unbounded queries time out, cost money, or bury the signal. For runtime sources, temporal correlation is the main finding: first seen, last seen, spike before the change and calm after.
7. **Read whole items, not previews.** Rationale sits in comments, sub-pages, threads, and review replies.
8. **Walk the relationships inside the source.** Parent issues, duplicate chains, backlinks, child pages, and thread replies. Cross-source links go under Additional Leads, not into this investigator's search.
9. **Handle async and expensive calls.** Poll a query ID instead of re-running it (`poll_sql_result`, Logs Insights `get-query-results`). Dry-run scan-billed queries first (`bq query --dry_run`).

Keep company-specific names as placeholders (`<your_analytics_db>.<schema>`). A playbook that bakes in one company's table names breaks for everyone else.

### What good evidence looks like here

Four to six concrete patterns, each tied to the code. "An alarm whose threshold matches the constant the code enforces." "A parent issue titled like an initiative." "A postmortem that names the target code as the fix."

### Common pitfalls

Check each of these against the new source, and write down the ones that apply in its own terms:

- **Correlation is not causation.** A spike before the PR and calm after is suggestive. Other changes may have landed in the same window.
- **Instrumented is not caused.** A metric or event existing shows someone cared, not that the code exists because of it.
- **Plans drift from code.** Specs, tickets, and threads describe intent at the time. Check them against the shipped PR and flag divergence.
- **Boilerplate "why" sections.** Required template fields filled with generic text are not evidence.
- **The human hides behind automation.** Deploy roles, service accounts, and bots make the change. Correlate with the pipeline run and commit to find the person.
- **Wrong scope.** Account, project, region, workspace, environment.
- **Retention cliffs and access limits.** Old data that expired, pages you can't open, an MCP that isn't authenticated. Each is a gap, not a null, and the playbook says so.
- **Schema and grouping drift.** Renamed metrics, regrouped errors, and new event properties can make one thing look like two.

### What to return

A bullet list of fields per finding. Always include:

- Type of item
- A stable identifier or link the reader can open (ticket ID, URL, ARN, `EventId`, fully-qualified table)
- Scope (account, project, region, workspace)
- Author or principal, and date
- The exact query or command, so the reader can rerun it
- A verbatim quote, or a compact numeric summary. Never raw row dumps.
- Relevance and strength: direct, circumstantial, or weak

## 3. Register it

1. Add a row to the table in [source-playbook.md](./source-playbook.md).
2. Add the source as an example in its roster entry in `SKILL.md`. For a CLI, also add its install-and-auth check to Discovery.
3. If the source can carry incident signal, add a bullet to [incident-postmortem.md](./sources/incident-postmortem.md).
4. If you added a category, update the Sources Consulted format in [synthesizer-prompt.md](./synthesizer-prompt.md).
5. Bump the `hstack` version in `plugin.json` in its own commit.
