# Google Cloud (via the `gcloud` CLI)

## What this source contains

Google Cloud holds the cloud-side record: what the infrastructure was configured to do, who changed it, and what it reported while running. Use the `gcloud` CLI from the terminal. If a Google Cloud MCP is also available, prefer the CLI.

- **Admin Activity audit logs.** Who changed which resource, and when. Always on, retained for 400 days. A config change that lands the same day as the target PR often explains both.
- **Cloud Logging.** Application and platform logs. Often hold the error conditions that motivated defensive code.
- **Cloud Monitoring alerting policies.** Conditions the team decided were worth paging on. A threshold that matches a constant in the code is strong evidence.
- **Cloud Monitoring metrics.** Built-in service metrics and custom ones the team wrote.
- **Resource configuration and revisions.** Cloud Run revisions, function versions, and cluster settings carry creation times and the settings each version ran with.
- **Cloud Asset Inventory history.** Earlier configurations of a resource over the last 35 days.
- **Labels.** Owner, team, or ticket labels on a resource can point at the people and tickets behind it.

Google Cloud answers "what did the infrastructure require or report around the time this code was written?"

## Read-only rules

- Run only read commands: `list`, `describe`, `logging read`, `asset get-history`, and `auth print-access-token` for read-only API calls.
- Never run `create`, `update`, `delete`, `deploy`, `set-iam-policy`, `add-iam-policy-binding`, or any other command that changes a resource.
- Pass `--project` (and `--region` where it applies) on each command. Never run `gcloud config set`, and never switch the user's active configuration.
- Never run `gcloud auth login`. If the CLI isn't authenticated, stop and report the gap, and say the user can sign in with `gcloud auth login`.
- Add `--format=json` so output parses.

## How to search it

1. **Confirm the identity and scope.**

   ```bash
   gcloud auth list --filter=status:ACTIVE --format="value(account)"
   gcloud config list --format=json
   gcloud projects list --format="value(projectId)"
   ```

   Pick the project and region from the repo: Terraform, deploy config, or CI files usually name them. Record which project you searched. A null result from the wrong project is not a null result.

2. **Find the resources behind the target.** Search the repo's infrastructure code for the resource names the target uses (service, topic, bucket, job). Then confirm and inspect them:

   ```bash
   gcloud run services describe <service> --project <p> --region <r> --format=json
   gcloud run revisions list --service <service> --project <p> --region <r> --format=json
   ```

   Revision creation times and their settings (timeout, concurrency, memory, env vars) show when each setting changed.

3. **Audit logs for configuration changes.**

   ```bash
   gcloud logging read \
     'logName:"cloudaudit.googleapis.com%2Factivity" AND protoPayload.resourceName:"<name>" AND timestamp>="<iso>" AND timestamp<="<iso>"' \
     --project <p> --limit 100 --format=json
   ```

   `protoPayload.authenticationInfo.principalEmail` names who made the change. Data Access audit logs are off by default, so their absence is not evidence.

4. **Alerting policies. They show what the team cares about.**

   ```bash
   gcloud alpha monitoring policies list --project <p> --format=json
   ```

   Use the beta or GA command group instead if your SDK has one. Note each policy's condition, threshold, and creation record.

5. **Application logs. Narrow, don't dump.**

   ```bash
   gcloud logging read '"<error string>" AND resource.type="<type>" AND timestamp>="<iso>" AND timestamp<="<iso>"' \
     --project <p> --limit 100 --format=json
   ```

   Bound the window to about 30 days before and after the target's merge date. Check the log bucket's retention: missing data before the cutoff is a gap, not a null.

6. **Metric time series.** `gcloud` has no time-series read command. Call the Monitoring API read-only:

   ```bash
   curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://monitoring.googleapis.com/v3/projects/<p>/timeSeries?filter=metric.type%3D%22<metric.type>%22&interval.startTime=<iso>&interval.endTime=<iso>"
   ```

7. **Asset history, for the last 35 days.**

   ```bash
   gcloud asset get-history --project <p> --asset-names=<full-resource-name> \
     --content-type=resource --start-time=<iso> --format=json
   ```

BigQuery datasets belong to the product analytics warehouse category, not this one. If that investigator uses `bq`, it should run `bq query --dry_run` first to see how much data a query scans.

## What good evidence looks like here

- An alerting policy whose threshold matches the constant the code enforces
- An audit-log entry that changed the resource's timeout, concurrency, scaling, or retry setting on the same day as the target PR
- A new revision whose settings changed in the same window as the target code
- A log pattern that spiked before the change and settled after
- A label naming the ticket or team that owns the resource

## Common pitfalls

- **Wrong project or region.** Resources, logs, and audit entries are scoped to the project. Confirm scope before reporting an absence.
- **Service accounts hide the human.** Changes applied by CI or Terraform show a service account, not the person. Correlate the entry time with the pipeline run and commit.
- **Out-of-band changes.** An audit-log change with no matching commit means someone changed the infrastructure by hand. That is itself a finding.
- **Retention cliffs.** Admin Activity logs keep 400 days, default log buckets keep 30, and asset history keeps 35. Missing old data is a gap.
- **Correlation is not causation.** A spike before the PR and calm after is suggestive. Check neighboring PRs before calling it the motive.

## What to return

For each relevant item:
- Type (audit entry / log pattern / alerting policy / metric / revision / asset history / label)
- Identifier (full resource name, policy name, log `insertId` and timestamp, revision name)
- Project and region
- Who and when (principal email, creation or change time)
- The exact command you ran, so the reader can rerun it
- The condition, value, or log line that bears on the question (verbatim where possible)
- Relevance: what this suggests about the target code, and how strong the connection is
