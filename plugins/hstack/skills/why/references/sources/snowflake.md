# Snowflake (via the `snow` CLI)

## What this source contains

Snowflake holds the product and data record: what users did, which experiments ran, how usage changed, and where a threshold could have come from. It complements infrastructure observability, which shows the runtime view. Use the Snowflake CLI (`snow`) from the terminal. If a Snowflake MCP is also available, prefer the CLI.

- **Product analytics events.** Feature use, clicks, submissions, and client-reported errors. Table names and schemas are company-specific, so probe before you trust a name.
- **Experiment and feature-flag data.** Exposure and outcome tables. A flag concluded around the PR date ties the code to a decision.
- **Table and column comments.** `COMMENT` text on a table or column sometimes states why the data exists or what a value means.
- **Query history.** `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` keeps 365 days of query text, duration, and bytes scanned. It shows the expensive queries behind a migration, backfill, or performance rewrite.
- **Access history.** `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY` (Enterprise Edition) shows which queries read or wrote which columns. Useful for "who still uses this field?"
- **Object metadata.** `SNOWFLAKE.ACCOUNT_USAGE.TABLES` and `COLUMNS` carry created and last-altered times, so you can line up a schema change with the PR date.
- **Time Travel.** `AT(TIMESTAMP => ...)` reads a table as it was at a past moment, within the table's retention (1 day by default, up to 90 on Enterprise Edition).
- **dbt models**, if the team uses dbt. Their SQL usually lives in a repo, so the rationale is in git. Hand that lead to the source control investigator.

Snowflake answers "what did the product and data look like around the time this code was written?"

Some parts can't be searched from here: Snowsight worksheets and dashboards aren't reachable through `snow sql`, and `ACCOUNT_USAGE` needs a role that has been granted access to the `SNOWFLAKE` database. Report either as a gap.

## Read-only rules

- `snow sql` runs whatever SQL you give it, so the rule sits on the statement. Run only `SELECT`, `SHOW`, `DESCRIBE`, and `EXPLAIN`.
- Never run `CREATE`, `ALTER`, `DROP`, `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `COPY`, `PUT`, `GRANT`, `REVOKE`, `CALL`, or `EXECUTE`. Never use `--single-transaction`, and never run a `.sql` file you didn't read first.
- Never run `snow connection add`, `snow connection set-default`, or any `deploy` command. Pass `-c <connection>` on each command. If the repo or the user names a read-only role, pass `--role <role>` too.
- Never start an interactive login. If `snow connection test` asks for MFA approval, a browser sign-in, or a password, stop and report the gap. Say the user can run `snow connection test -c <connection>` themselves to sign in.
- Always pass `-q` (never open the REPL), plus `--format JSON` and `--silent`.

## How to search it

1. **Confirm the connection and scope.**

   ```bash
   snow connection list --format JSON
   snow connection test -c <connection> --format JSON
   snow sql -c <connection> -q "SELECT CURRENT_ACCOUNT(), CURRENT_ROLE(), CURRENT_WAREHOUSE()" --format JSON --silent
   ```

   Pick the connection from the repo (dbt `profiles.yml`, app config, or CI files often name the account and database), or use the default. Record the account, role, and warehouse you searched. A null result from the wrong account or a role that can't see the table is not a null result.

2. **Probe names before querying.**

   ```bash
   snow sql -c <connection> -q "SHOW TABLES LIKE '%<keyword>%' IN SCHEMA <db>.<schema>" --format JSON --silent
   snow sql -c <connection> -q "DESCRIBE TABLE <db>.<schema>.<table>" --format JSON --silent
   ```

   Read the `comment` column in both results. A table or column comment can state the rationale outright.

3. **Bound every query in time, and keep it cheap.** Queries spend warehouse credits. Filter on the event timestamp with a window of about 30 days before and after the merge date. Aggregate in SQL and add `LIMIT`. Run `EXPLAIN` first on anything that might scan a large table.

4. **Pick the pattern that matches the target.**

   1. **Usage trajectory.** Daily counts of the relevant event across the window. A step from zero to steady volume a day or two after the merge suggests the PR launched the feature. A decay to zero suggests a deprecation.
   2. **Where a threshold came from.** Median, p99, and max of the relevant value in the 14 days before the PR (`APPROX_PERCENTILE(<col>, 0.99)`). A p99 that matches the code's constant suggests someone chose the number from data.
   3. **Experiment lookup.** Find the exposure table (`SHOW TABLES LIKE '%experiment%'`), then count exposures by variant for the flag key near the PR date.
   4. **Query history for migrations and rewrites.**

      ```sql
      SELECT start_time, user_name, role_name, total_elapsed_time, bytes_scanned, LEFT(query_text, 500)
      FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
      WHERE query_text ILIKE '%<table_or_symbol>%'
        AND start_time BETWEEN '<iso>' AND '<iso>'
      ORDER BY total_elapsed_time DESC
      LIMIT 50
      ```

      `ACCOUNT_USAGE` lags by up to 45 minutes. For the last 7 days, the `INFORMATION_SCHEMA.QUERY_HISTORY()` table function is fresher.
   5. **Schema change timing.** `CREATED` and `LAST_ALTERED` from `SNOWFLAKE.ACCOUNT_USAGE.TABLES` or `COLUMNS` for the objects the target reads or writes, compared with the PR date.
   6. **Config or lookup tables then and now.** If the target reads a config or lookup table, Time Travel shows what it held near the PR date: `SELECT * FROM <table> AT(TIMESTAMP => '<iso>'::TIMESTAMP_LTZ) LIMIT 100`. Past the retention window, that's a gap.

## What good evidence looks like here

- An event's daily count steps up within a day or two of the target PR's merge
- A p99 in the window before the PR that matches the threshold constant in the code
- An exposure table that shows the target's flag key concluded around the PR date
- An error-classifying event that drops to near zero after a defensive-code PR
- A table or column `COMMENT` that states why the data exists
- Expensive queries against a table that stop after a rewrite PR lands

## Common pitfalls

- **Instrumented is not caused.** An event's existence shows someone logged it, not that the code exists because of it. Pair the finding with a commit or PR from the source control investigator.
- **Silent instrumentation changes.** A step in event volume may mean a new event started being logged, not that behavior changed. Check for instrumentation PRs in the same window.
- **Company-specific tables.** Never report from a table you didn't confirm with `SHOW` or `DESCRIBE`.
- **Schema drift.** A column on today's table may not have existed when the target was written. Older rows may hold the value only inside a `VARIANT` column.
- **Role blindness.** A role without access sees no rows and no error on some views. Confirm with `CURRENT_ROLE()` and say which role you used.
- **Retention cliffs.** `ACCOUNT_USAGE` keeps 365 days, `INFORMATION_SCHEMA.QUERY_HISTORY()` keeps 7, and Time Travel keeps what the table's retention allows. A window before the cutoff is a gap, not a null.

## What to return

For each relevant finding:
- Type (product event / experiment exposure / query history / access history / object metadata / comment / Time Travel snapshot)
- Fully-qualified object name
- Connection, account, role, and warehouse
- The exact `snow sql` command, so the reader can rerun it
- The time window queried
- A compact numeric summary (counts, percentiles, first and last timestamps) or the verbatim comment. Never raw row dumps.
- Temporal correlation with the target's merge date (for example "first row 2024-08-15, PR #49074 merged 2024-08-14")
- Relevance and strength: direct, circumstantial, or weak
