# AWS (via the `aws` CLI)

## What this source contains

AWS holds the cloud-side record: what the infrastructure was configured to do, who changed it, and what it reported while running. Use the `aws` CLI from the terminal. If an AWS MCP is also available, prefer the CLI.

- **CloudTrail.** API activity: who changed which resource, and when. Event history covers the last 90 days of management events per region. A config change that lands the same day as the target PR often explains both.
- **CloudWatch alarms.** Conditions the team decided were worth paging on. An alarm threshold that matches a constant in the code is strong evidence.
- **CloudWatch metrics.** Built-in service metrics and custom ones the team published. A custom metric's existence shows someone cared about that number.
- **CloudWatch Logs.** Application and service logs. Often hold the error conditions that motivated defensive code.
- **AWS Config history.** Point-in-time configuration of a resource, if AWS Config records it.
- **Service quotas and hard limits.** Many "why is this N?" answers are an AWS limit: a batch of 25 items for DynamoDB `BatchWriteItem`, 10 messages per SQS batch, a 15-minute Lambda timeout.
- **Tags.** Owner, team, ticket, or cost-center tags on the resource can point at the people and tickets behind it.

AWS answers "what did the infrastructure require or report around the time this code was written?"

## Read-only rules

- Run only read commands: `describe-*`, `list-*`, `get-*`, `lookup-events`, `filter-log-events`, and the Logs Insights trio `start-query`, `get-query-results`, `stop-query`.
- Never run `create-*`, `put-*`, `update-*`, `delete-*`, `tag-*`, `invoke`, or any other command that changes a resource.
- Pass `--profile` and `--region` on each command. Never run `aws configure set` or change the user's AWS config.
- Never run `aws sso login` or any other login. If the CLI isn't authenticated, stop and report the gap, and say the user can sign in with `aws sso login` (or their usual method).
- Add `--output json --no-cli-pager` so output parses and nothing waits on a pager.

## How to search it

1. **Confirm the identity and scope.**

   ```bash
   aws sts get-caller-identity --profile <profile>
   aws configure list-profiles
   ```

   Pick the account and region from the repo: Terraform, CDK, CloudFormation, `serverless.yml`, or deploy config usually name them. Record which account and region you searched. A null result from the wrong account is not a null result.

2. **Find the resources behind the target.** Search the repo's infrastructure code for the resource names the target uses (queue, table, function, bucket, alarm). Then confirm they exist:

   ```bash
   aws resourcegroupstaggingapi get-resources --tag-filters Key=<tag>,Values=<value>
   aws lambda get-function-configuration --function-name <name>
   ```

3. **Alarms first. They show what the team cares about.**

   ```bash
   aws cloudwatch describe-alarms --alarm-name-prefix <service>
   aws cloudwatch describe-alarm-history --alarm-name <name> --start-date <iso> --end-date <iso>
   ```

   Note each alarm's metric, threshold, and creation date. Alarm history shows when it fired, which can line up with the PR date.

4. **Metrics around the change date.**

   ```bash
   aws cloudwatch list-metrics --namespace <namespace> --dimensions Name=<dim>,Value=<value>
   aws cloudwatch get-metric-statistics --namespace <ns> --metric-name <name> \
     --dimensions Name=<dim>,Value=<value> --statistics Sum Maximum \
     --start-time <iso> --end-time <iso> --period 3600
   ```

   Bound the window to about 30 days before and after the target's merge date.

5. **Logs. Narrow, don't dump.**

   ```bash
   aws logs describe-log-groups --log-group-name-prefix <prefix>
   aws logs filter-log-events --log-group-name <group> --filter-pattern '"<error string>"' \
     --start-time <epoch-ms> --end-time <epoch-ms> --max-items 100
   ```

   For counts over time, use Logs Insights (`start-query`, then poll `get-query-results`). Logs Insights bills by data scanned, so keep the window and log groups narrow. Check each group's retention: missing data before the retention cutoff is a gap, not a null.

6. **CloudTrail for configuration changes.**

   ```bash
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=ResourceName,AttributeValue=<name> \
     --start-time <iso> --end-time <iso>
   ```

   Event history is per region and covers 90 days. Anything older needs a trail delivered to S3 or CloudWatch Logs. If none is queryable, report it as a gap.

7. **AWS Config history, if enabled.**

   ```bash
   aws configservice get-resource-config-history --resource-type <AWS::Service::Type> \
     --resource-id <id> --earlier-time <iso> --later-time <iso>
   ```

8. **Quotas and limits.**

   ```bash
   aws service-quotas list-service-quotas --service-code <code>
   aws service-quotas get-service-quota --service-code <code> --quota-code <quota>
   ```

   For hard limits that aren't adjustable quotas, cite the AWS documentation page that states the limit.

## What good evidence looks like here

- An alarm whose threshold matches the constant the code enforces
- A CloudTrail event that changed the resource's timeout, memory, concurrency, or retry setting on the same day as the target PR
- A metric or log pattern that spiked before the change and settled after
- A quota or documented limit equal to the number the code clamps to
- A tag naming the ticket or team that owns the resource

## Common pitfalls

- **Wrong account or region.** Resources, CloudTrail history, and logs are scoped to both. Confirm scope before reporting an absence.
- **Deploy roles hide the human.** Changes applied by CI or Terraform show the deploy role in CloudTrail, not the person. Correlate the event time with the pipeline run and commit.
- **Out-of-band changes.** A CloudTrail change with no matching commit means someone changed the infrastructure by hand. That is itself a finding.
- **Retention cliffs.** CloudTrail event history keeps 90 days. Log groups have their own retention. Missing old data is a gap.
- **A limit is a ceiling, not a reason.** A quota equal to the code's constant is strong circumstantial evidence, but confirm with the PR or commit message before calling it the motive.

## What to return

For each relevant item:
- Type (alarm / metric / log pattern / CloudTrail event / config history / quota / tag)
- Identifier (ARN, alarm name, log group and timestamp, CloudTrail `EventId`, quota code)
- Account and region
- Who and when (CloudTrail `Username`, creation or change date)
- The exact command you ran, so the reader can rerun it
- The condition, value, or log line that bears on the question (verbatim where possible)
- Relevance: what this suggests about the target code, and how strong the connection is
