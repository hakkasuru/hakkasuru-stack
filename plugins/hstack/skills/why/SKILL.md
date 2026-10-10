---
name: why
description: "Investigate why code has its current shape: trace git history, PRs, CLIs (aws, gcloud, snow), and every connected MCP evidence source (tickets, docs, chat, observability, error tracking, analytics) in parallel, then return a cited read that separates evidence from inference."
disable-model-invocation: true
---

# Why

Investigate the motivation and intent behind code.

Companion to `/hstack:how`. `how` answers what the code does and how it works. `why` answers what forces led to its shape. If the question is only about runtime behavior ("how does this work?", "where does this live?"), tell the user `/hstack:how` is the better fit instead of running the investigation.

Spawn every subagent below with the Agent tool. If a `model` value is rejected, leave `model` unset and say so.

## Operating posture

Operate as a **careful, cautious, and precise investigator**. Be honest about what you know vs what you're inferring. Read [references/epistemics.md](references/epistemics.md) for the full confidence framework and phrasing guide. The synthesizer must follow it.

## Step 1. Understand the target and the question

Parse what the user is asking. The **target** is usually a chunk of code, a pattern, a feature, or a named design decision. The **question** is usually a design rationale, a tradeoff, a motivating edge case, an external constraint, dead code, or a broad history sweep.

If the target is vague ("why do we do it this way?" with no clear referent), make your best guess from conversation context (open files, recent edits, the IDE selection, what was just discussed). State your interpretation briefly so the user can redirect if you're off, then proceed.

## Step 2. Establish the code anchor

Before spawning investigators, anchor the investigation in concrete code. You need:

- The relevant file path(s) and line range(s)
- The key symbols (function names, class names, constants)
- An initial commit list. The last few commits touching the target.
- PR numbers from merge commits (pattern `(#1234)` in the subject line on GitHub, `!1234` on GitLab)

Build this inline.

```bash
# Blame target lines for last-touch commits
git blame -L <start>,<end> <file>

# Full file history, with patches, through renames
git log --follow -p -- <file>

# Last N commits touching the file, PR numbers visible
git log --oneline -20 -- <file>

# Extract PR numbers from a commit message
git log -1 --format=%B <commit>
```

Pull PR bodies and discussion for any substantive commits. Check `git remote -v` for the host. On GitHub use `gh`:

```bash
gh pr view <number> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews
```

On GitLab use `glab`, where PRs are merge requests:

```bash
glab mr view <number> --comments
```

Capture this as seed context (file paths, symbols, commits, PR numbers, linked ticket IDs). Pass it to the investigators.

## Step 3. Spawn parallel investigators (default posture)

**Default to the full parallel investigation.**

### Discovery

Before spawning investigators, list the sources available in this session. Prefer terminal CLIs over MCPs.

Check the CLIs first. Each counts as a source only if it is installed and authenticated:

```bash
command -v aws && aws sts get-caller-identity --output json --no-cli-pager
command -v gcloud && gcloud auth list --filter=status:ACTIVE --format="value(account)"
command -v snow && snow connection list --format JSON
```

For `snow`, a listed connection is not proof of sign-in. The Snowflake investigator confirms it with `snow connection test` and reports a gap if that asks for an interactive login.

If a CLI is installed but not authenticated, record it as a gap. Don't run a login command. Tell the user they can sign in with `aws sso login`, `gcloud auth login`, or `snow connection test -c <connection>`.

Then list the MCP servers. Their tools appear as `mcp__<server>__<tool>`, either in your tool list or in the deferred-tool list in system reminders. Servers that need authentication are listed separately. You can't authorize them, so record each one as a gap and tell the user they can authorize it with `/mcp`.

Map each available source to one evidence category:

1. Source control history
2. Issue / ticket tracker
3. Long-form documents
4. Real-time team chat
5. Infrastructure observability
6. Error / exception tracking
7. Product analytics warehouse

Source control is always available through git and `gh` or `glab`. `aws` and `gcloud` are infrastructure observability. `snow` is product analytics warehouse. For the other MCPs, classify using the server name, server instructions, and tool names and descriptions. If a source could fit more than one category, choose the one matching its primary evidence. Record ambiguous cases in the coverage map. When a CLI and an MCP reach the same source (an AWS MCP and `aws`), use the CLI and record the MCP as unused, not as a gap.

Aim for a complete **coverage map**, not a minimal one. Document the null, don't skip the search.

Launch all matching investigators in a single message so they run concurrently. Don't ask one agent to cover multiple sources. Wait until every investigator has returned before Step 4.

Subagent config (each):
- `subagent_type`: `general-purpose`. It has every tool, including Bash, MCP tools, and ToolSearch. **Do not use a read-only type such as `Explore` or `Plan`.** Investigators need Bash and MCP access. They still shouldn't write anything, and the investigator prompt says so.
- `model`: `sonnet`

Each investigator gets:
1. The base prompt from [references/investigator-prompt.md](references/investigator-prompt.md)
2. The source playbook `references/sources/<source>.md`, if [references/source-playbook.md](references/source-playbook.md) lists one for that source or its tool family. Adapt it to the tool. Sources with no playbook get none.
3. The cross-cutting [references/sources/incident-postmortem.md](references/sources/incident-postmortem.md) **if the target code looks defensive** (null checks, retry logic, timeout handling, rate limiting, feature flags, egress guards, OOM handlers)
4. The code anchor from Step 2 (file paths, symbols, commit hashes, PR numbers, ticket IDs)
5. The user's original question

### Investigator roster. One per available source

Spawn one investigator per available source. Each owns exactly one CLI or MCP. A category with two sources, such as Datadog and AWS, gets two investigators.

Each entry names the category and the kind of "why" it uniquely surfaces. Use it to know what to expect back, how to name a gap when a category returns empty, and (only in the rare provably-irrelevant case) to justify a skip.

1. **Source control investigator**. Git history, `gh` or `glab` for PRs and MRs, code comments, tests. Always spawn. The only guaranteed source. Best at surfacing *implementation-time rationale captured during review*.

2. **Issue / ticket tracker investigator** (e.g. GitHub Issues via `gh`, GitLab Issues via `glab`, or a Linear, Jira, Plane, or Shortcut MCP). Best at surfacing *the product or business forcing function*. Strongest when the why is external to engineering.

3. **Long-form documents investigator** (e.g. Notion, Confluence, Google Docs, Coda MCP). Best at surfacing *long-form design rationale*. Where the why is written out before it becomes code.

4. **Real-time team chat investigator** (e.g. Slack, Discord, Microsoft Teams, Mattermost MCP). Best at surfacing *real-time deliberation that never reached a doc*. Especially important when the source control, ticket, and doc paper trail is thin.

5. **Infrastructure observability investigator** (e.g. the `aws` or `gcloud` CLI, or a Datadog, New Relic, Honeycomb, Grafana, or Splunk MCP). For AWS and Google Cloud, CloudTrail and audit logs show who changed the infrastructure and when, and quotas often explain a hard-coded number. Infra/runtime view. Best at surfacing *infrastructure and runtime reality that motivated the code*. Strongest when the target reacts to an infra signal (timeouts, retries, rate limits, circuit breakers).

6. **Error / exception tracking investigator** (e.g. Sentry, Rollbar, Bugsnag, Airbrake MCP). Best at surfacing *the specific exceptions and error trajectories that motivated defensive or corrective code*. Strongest for catch blocks, null guards, type checks, retries, and other defenses.

7. **Product analytics warehouse investigator** (e.g. Snowflake via `snow`, or a Databricks, BigQuery, ClickHouse, dbt, or Redshift MCP). Product/data view. Best at surfacing *product and data reality that shaped the code*. Strongest for flag-gated code, experiment-driven ships, data migrations, and "where did this number come from" questions.

### When to skip an investigator

Only skip with an **explicit, written justification** that goes in the final "Sources Consulted" section. Two valid reasons:

- **No source is available for that category** in this environment: no matching MCP and no authenticated CLI, or the only match needs authentication. Flag this as a gap, not a choice. Example: "Real-time team chat skipped. No matching MCP available, so the conversational record was not searchable."
- **The source is provably irrelevant**, not just "probably irrelevant." A high bar. Example: "Error / exception tracking skipped. Target is a build-time script with no runtime code path."

If your scope assessment suggests a single-commit trivial target where the PR description already contains the complete answer, you may answer inline **only after** confirming all seven available category searches would be redundant. Say so explicitly. This should be rare.

## Step 4. Synthesize

Spawn one synthesizer subagent:

- `subagent_type`: `general-purpose`. The synthesizer's quality check spot-verifies citations, which can require MCP access, so don't use a read-only type.
- `model`: unset, so it inherits yours

The synthesizer gets:
1. The investigator findings, including any null results and any categories skipped with justification
2. The code anchor from Step 2 (file paths, symbols, commit hashes, PR numbers, ticket IDs)
3. The user's original question
4. The epistemics framework from [references/epistemics.md](references/epistemics.md)
5. The synthesizer prompt template from [references/synthesizer-prompt.md](references/synthesizer-prompt.md)

## Step 5. Present

The user can't see subagent output, so present the synthesizer's output yourself. You may lightly edit for clarity or add context from the conversation, but **do not rewrite the confidence language**.

## Output format

The output structure is the one in [references/synthesizer-prompt.md](references/synthesizer-prompt.md): The Question, The Code in Question, What We Found, What We Can Reasonably Infer, Competing Hypotheses, What We Don't Know, Sources Consulted, Confidence Summary. Adapt as needed, but keep the confidence separation intact, and keep Sources Consulted as one line per investigator, including the ones that returned nothing or were skipped, with the reason.

After the Sources Consulted block, if the user's `why` question is a precursor to actually changing this code, convert the lineage findings into a Preserve / Change / Avoid / Risk constraint set suitable for planning the change.

## Common failure modes to avoid

- **Recency bias**. Assuming the most recent commit is authoritative. The current shape is often the accretion of many earlier decisions. Trace back.

## Reference files

- [references/epistemics.md](references/epistemics.md). Confidence tiers and phrasing guide. The synthesizer must follow it.
- [references/investigator-prompt.md](references/investigator-prompt.md). Base prompt template for investigator subagents.
- [references/source-playbook.md](references/source-playbook.md). Index pointing at the category playbooks below.
- `references/sources/*.md`. Self-contained example playbooks for source control (git, `gh`, `glab`), real-time team chat (Slack), infrastructure observability (Datadog, AWS, Google Cloud), and product analytics warehouse (Snowflake), plus cross-cutting `incident-postmortem.md`. Give an investigator the single file that matches its source, if there is one, and adapt it to the tool.
- [references/adding-a-source.md](references/adding-a-source.md). How to write and register a new source playbook. Not for investigators.
- [references/synthesizer-prompt.md](references/synthesizer-prompt.md). Prompt template for the synthesizer subagent, including the output format.
