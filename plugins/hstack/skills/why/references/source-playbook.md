# Source playbooks

`/hstack:why` spawns one investigator per available source, each reading the source-specific playbook below when one exists. A category can have several sources, such as Datadog, AWS, and Google Cloud for infrastructure observability. The playbooks are concrete examples. Adapt one for a different tool in the same category. An investigator with no playbook works from the base investigator prompt alone.

Prefer terminal CLIs. When a CLI and an MCP reach the same source, the investigator uses the CLI.

To add a source, follow [adding-a-source.md](./adding-a-source.md).

| Category | Playbook | Example source it documents |
|---|---|---|
| Source control history | [`code-archaeology.md`](./sources/code-archaeology.md) | git, `gh`, `glab` (CLI) |
| Issue / ticket tracker | None | |
| Long-form documents | None | |
| Real-time team chat | [`slack.md`](./sources/slack.md) | Slack MCP (adapt for Discord, Microsoft Teams, Mattermost) |
| Infrastructure observability | [`datadog.md`](./sources/datadog.md) | Datadog MCP (adapt for New Relic, Honeycomb, Grafana, Splunk) |
| Infrastructure observability | [`aws.md`](./sources/aws.md) | AWS via the `aws` CLI |
| Infrastructure observability | [`gcloud.md`](./sources/gcloud.md) | Google Cloud via the `gcloud` CLI |
| Error / exception tracking | None | |
| Product analytics warehouse | [`snowflake.md`](./sources/snowflake.md) | Snowflake via the `snow` CLI (adapt for BigQuery, Databricks, Redshift) |

Cross-cutting:

- [`incident-postmortem.md`](./sources/incident-postmortem.md). Add this if the target code looks defensive (null checks, retry, timeout, rate limit, feature flag, egress guard, OOM handler).
