# Gauge

Size the task from the brief and a short read-only scan of the code. The output is a tier, its unit cap, and the reasons, in one line.

## Scan

The scan is read-only.

- Grep the symbols, files, and terms the brief names.
- Count the callers of what would change.
- List the modules and repos touched.

Stop as soon as the four scores below can be given. The backstop is `caps.gauge_backstop` searches or file reads, from `tune.py caps`. At the backstop, decide with what is known, say "scan capped" in the output line, and score uncertainty high. An incomplete scan pushes the tier up, never down.

Count every search and file read. The run's ledger entry records the total as `gauge_ops`.

## Score

- **Scope.** How many files, modules, and repos change.
- **Uncertainty.** Whether the fix is already known or needs exploring.
- **Blast radius.** What breaks, and for whom, if the change is wrong.
- **Verification cost.** One targeted test, a full suite, or manual checking.

## Risk triggers

Any one of these sets a floor of tier 2, however small the change:

- security or auth
- data or migrations
- a public API
- infrastructure or production config
- deletions

## Pick the tier

| Tier | Typical task |
|---|---|
| 0 Trivial | known one-line or very local fix |
| 1 Small | one module, obvious approach |
| 2 Standard | several files, some design choices |
| 3 Hard | cross-cutting, ambiguous, multi-repo |

- Another repo in scope means tier 3, and triggers the multi-repo question in SKILL.md before Plan.
- `--tier N` overrides the pick, but never below a risk-trigger floor.
- The unit cap is `caps.units.<tier>` from `tune.py caps`.

## Output

Print one line, then continue without waiting:

```
Tier <n>: <reasons>. Up to <unit cap> units.
```

For example: `Tier 1: single module, known fix, no risk triggers. Up to 3 units.` Keep the four scores and any risk triggers hit for the final report.
