# Incident & Postmortem Context

Not a separate source, a **cross-cutting angle**. Incidents often motivate defensive code ("we added this check after the X outage"), so if the target looks defensive (null checks, retry logic, timeout handling, rate limiting, feature flags), specifically hunt for incident history across every available source:

- **Long-form documents**: search for postmortems mentioning the target file, feature, or error string
- **Issue / ticket tracker**: look for tickets labeled `incident`, `sev-*`, `postmortem-action-item`, `reliability`
- **Slack**: search `#sev-*` and `#incident-*` channels around the dates the target code was added
- **Git**: commits with messages like "fix for incident", "add defensive check", "revert" followed by "re-apply with..." are strong signals
- **Datadog**: `search_datadog_incidents` for formal incident records with timelines, dashboards and monitors created as postmortem action items
- **AWS**: CloudTrail changes and alarm history in the incident window, and alarms created right after it as postmortem action items
- **Google Cloud**: Admin Activity audit entries and new revisions in the incident window, and alerting policies created right after it
- **Error / exception tracking**: issues whose first-seen/last-seen window aligns with the target's PR ship date, stack traces through the target
- **Product analytics warehouse**: product-analytics events that classify an error condition (client-reported failures, user-visible retry events, etc.) often spike during an incident window. A drop in that event count after the target PR ships is circumstantial support that the target code resolved the user-visible symptom, even when observability and error-tracking signal is noisy.

If you find an incident link, fetch the full postmortem. Postmortems typically have an "Action Items" section that ties directly to code changes. When multiple sources corroborate (a Datadog incident ID appears in a ticket, which appears in a postmortem doc, which appears in a Slack thread that links to the target PR, and the analytics error-event count drops after the fix), the evidence is especially strong.

Worth spending time on when the code's defensive character makes an incident-driven origin plausible. Skip it for code that doesn't look defensive.
