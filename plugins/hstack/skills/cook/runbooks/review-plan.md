# Review plan

A fresh reviewer scores the plan before any code is written. Tiers 2 and 3 only.

## Reviewer

Spawn one `general-purpose` subagent with the Agent tool. Leave `model` unset so it inherits the session's model: judging a plan needs the strongest one available.

Give it the brief and the plan, and ask it to:

1. Score 0-100 how likely this plan meets every acceptance criterion with the smallest change.
2. List any hard limits the plan hits (below).
3. List findings, each with the points it costs.

Tell it the work is read-only: no edits, no commits.

## Hard limits

Any one of these sends the plan to the user, with the review, whatever the score:

- open questions that only the user can answer
- destructive steps: deleting data, dropping tables, removing public APIs
- security-touching scope: auth, secrets, permissions, crypto

## Decide

- No hard limit and confidence at or above `caps.review_threshold` (from `tune.py caps`): proceed to Implement.
- Otherwise, revise the plan against the findings and spawn a fresh reviewer.

Stop revising and go to the user, with the latest review and the round history, when any of these happens:

- the score is a near miss, within 5 points below the threshold
- a round improved the score by fewer than 5 points
- the same finding stayed unresolved across two reviews
- `caps.review_rounds` autonomous rounds are spent

Count the rounds. The run's ledger entry records them as `review_rounds`.
