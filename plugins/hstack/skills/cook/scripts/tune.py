#!/usr/bin/env python3
"""Effort caps for /hstack:cook: defaults, user overrides, the run ledger, and tuning suggestions.

Every subcommand prints one JSON document on stdout.
"""
import argparse
import json
import math
import os
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULTS = {
    "units": {"0": 1, "1": 3, "2": 8, "3": 20},
    "attempts": 3,
    "gauge_backstop": 25,
    "review_rounds": 2,
    "fix_rounds": 2,
    "review_threshold": 85,
}
BASELINE = {
    "source": "58 finished morpheus-os items grouped by MR size",
    "units_p80": {"0": 1, "1": 3, "2": 8, "3": 14},
    "units_max": {"0": 4, "1": 4, "2": 11, "3": 19},
    "review_rounds_p80": 2,
}
MIN_TIER_RUNS = 5
MIN_RUNS = 20
ESCALATION_RATE = 0.3
OUTCOMES = {"green", "red", "stopped"}
RECORD_FIELDS = {
    "repo": str, "date": str, "outcome": str, "gauge_tier": int, "final_tier": int, "escalations": list,
    "units_planned": int, "units_used": int, "attempts": list, "stuck_units": int, "review_rounds": int,
    "fix_rounds": int, "gauge_ops": int,
}


def home():
    return Path(os.environ.get("HSTACK_HOME") or Path.home() / ".claude" / "hstack")


def paths():
    h = home()
    return h / "cook.json", h / "cook-runs.jsonl"


def cap_paths():
    for tier in DEFAULTS["units"]:
        yield f"units.{tier}"
    for key in DEFAULTS:
        if key != "units":
            yield key


def get(caps, path):
    if path.startswith("units."):
        return caps["units"][path.split(".", 1)[1]]
    return caps[path]


def put(caps, path, value):
    if path.startswith("units."):
        caps.setdefault("units", {})[path.split(".", 1)[1]] = value
    else:
        caps[path] = value


def valid_value(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def flatten(section, label, warnings):
    out = {}
    if section is None:
        return out
    if not isinstance(section, dict):
        warnings.append(f"{label}: must be an object, ignored")
        return out
    for key, value in section.items():
        if key == "units" and not isinstance(value, dict):
            warnings.append(f"{label}: units must be an object, ignored")
        elif key == "units":
            for tier, cap in value.items():
                path = f"units.{tier}"
                if path not in set(cap_paths()):
                    warnings.append(f"{label}: unknown cap {path}, ignored")
                elif not valid_value(cap):
                    warnings.append(f"{label}: invalid value for {path} ({cap!r}), ignored")
                else:
                    out[path] = cap
        elif key in DEFAULTS and key != "units":
            if valid_value(value):
                out[key] = value
            else:
                warnings.append(f"{label}: invalid value for {key} ({value!r}), ignored")
        else:
            warnings.append(f"{label}: unknown cap {key}, ignored")
    return out


def load_overrides(warnings):
    config, _ = paths()
    if not config.exists():
        return {}
    try:
        data = json.loads(config.read_text())
        if not isinstance(data, dict):
            raise ValueError("top level is not an object")
        return data
    except (ValueError, OSError) as exc:
        warnings.append(f"cook.json unreadable ({exc}), using defaults")
        return {}


def effective(repo):
    warnings = []
    data = load_overrides(warnings)
    caps = json.loads(json.dumps(DEFAULTS))
    sources = {path: "default" for path in cap_paths()}
    for path, value in flatten(data.get("caps"), "cook.json caps", warnings).items():
        put(caps, path, value)
        sources[path] = "override"
    repos = data.get("repos")
    if repos is not None and not isinstance(repos, dict):
        warnings.append("cook.json repos: must be an object, ignored")
        repos = None
    section = (repos or {}).get(repo) if repo else None
    if section is not None and not isinstance(section, dict):
        warnings.append(f"cook.json repos.{repo}: must be an object, ignored")
        section = None
    if section:
        for path, value in flatten(section.get("caps"), f"cook.json repos.{repo}", warnings).items():
            put(caps, path, value)
            sources[path] = "repo"
    return caps, sources, warnings


def cmd_caps(args):
    caps, sources, warnings = effective(args.repo)
    emit({"caps": caps, "sources": sources, "warnings": warnings})


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_record(rec):
    if not isinstance(rec, dict):
        return "run must be a JSON object"
    for key, kind in RECORD_FIELDS.items():
        value = rec.get(key)
        if isinstance(value, bool) or not isinstance(value, kind):
            return f"missing or invalid field: {key}"
    if rec["outcome"] not in OUTCOMES:
        return f"outcome must be one of {sorted(OUTCOMES)}"
    for key in ("gauge_tier", "final_tier"):
        if not 0 <= rec[key] <= 3:
            return f"{key} must be 0-3"
    if "tier_override" not in rec:
        return "missing field: tier_override (use null when Gauge's tier stood)"
    override = rec["tier_override"]
    if override is not None and not (is_int(override) and 0 <= override <= 3):
        return "tier_override must be 0-3 or null"
    if not all(is_int(a) and a > 0 for a in rec["attempts"]):
        return "attempts must be positive integers"
    for esc in rec["escalations"]:
        if not (isinstance(esc, dict) and is_int(esc.get("from")) and is_int(esc.get("to")) and isinstance(esc.get("trigger"), str)):
            return "escalations must be objects with integer from, integer to, and string trigger"
    try:
        datetime.strptime(rec["date"], "%Y-%m-%d")
    except ValueError:
        return "date must be YYYY-MM-DD"
    return None


def cmd_record(args):
    try:
        rec = json.loads(sys.stdin.read())
    except ValueError as exc:
        fail(f"run is not valid JSON: {exc}")
    problem = validate_record(rec)
    if problem:
        fail(problem)
    _, ledger = paths()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    emit({"recorded": True, "ledger": str(ledger)})


def read_ledger():
    _, ledger = paths()
    runs, skipped = [], 0
    if not ledger.exists():
        return runs, skipped
    for line in ledger.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            skipped += 1
            continue
        if validate_record(rec):
            skipped += 1
            continue
        runs.append(rec)
    return runs, skipped


def percentile(values, p):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def suggestions_for(runs, caps, scope, out, notes):
    for tier in DEFAULTS["units"]:
        used = [r["units_used"] for r in runs if str(r["final_tier"]) == tier]
        if len(used) >= MIN_TIER_RUNS:
            p80 = max(1, percentile(used, 0.8))
            current = caps["units"][tier]
            if p80 != current:
                out.append({"cap": f"units.{tier}", "current": current, "suggested": p80, "scope": scope,
                            "evidence": f"80th percentile {p80} units across {len(used)} tier {tier} runs"})
        started = [r for r in runs if str(r["gauge_tier"]) == tier]
        if len(started) >= MIN_TIER_RUNS:
            rate = sum(1 for r in started if r["final_tier"] > r["gauge_tier"]) / len(started)
            if rate > ESCALATION_RATE:
                notes.append(f"{scope}: tier {tier} escalated in {rate:.0%} of {len(started)} runs. Gauge may start too low, or the cap is tight.")
    if len(runs) >= MIN_RUNS:
        ops = [r["gauge_ops"] for r in runs]
        p95 = percentile(ops, 0.95)
        if p95 >= 0.9 * caps["gauge_backstop"]:
            out.append({"cap": "gauge_backstop", "current": caps["gauge_backstop"], "suggested": math.ceil(p95 * 1.2), "scope": scope,
                        "evidence": f"95th percentile of gauge operations is {p95} across {len(runs)} runs"})
        attempts = [a for r in runs for a in r["attempts"]]
        stuck = sum(r["stuck_units"] for r in runs)
        third = sum(1 for a in attempts if a == caps["attempts"])
        notes.append(f"{scope}: {third} units succeeded on the last allowed attempt, {stuck} got stuck, across {len(attempts)} units.")
        overrides = [r for r in runs if r.get("tier_override") is not None]
        if len(overrides) >= MIN_TIER_RUNS:
            up = sum(1 for r in overrides if r["tier_override"] > r["gauge_tier"])
            share = max(up, len(overrides) - up) / len(overrides)
            if share >= 0.7:
                direction = "up" if up * 2 >= len(overrides) else "down"
                notes.append(f"{scope}: --tier overrode Gauge {direction} in {share:.0%} of {len(overrides)} overrides. Gauge is systematically off.")


def cmd_suggest(args):
    runs, skipped = read_ledger()
    out, notes = [], []
    caps, _, warnings = effective(None)
    suggestions_for(runs, caps, "global", out, notes)
    repos = sorted({r["repo"] for r in runs})
    if args.repo and args.repo not in repos:
        notes.append(f"{args.repo}: no runs in the ledger yet.")
    for repo in ([args.repo] if args.repo else repos):
        scoped = [r for r in runs if r["repo"] == repo]
        if scoped and len(scoped) == len(runs) and len(repos) == 1:
            notes.append(f"{repo}: every run is from this repo, so the global suggestions already apply to it.")
        elif scoped:
            repo_caps, _, _ = effective(repo)
            suggestions_for(scoped, repo_caps, repo, out, notes)
    emit({"runs": len(runs), "skipped_lines": skipped, "suggestions": out, "notes": notes + warnings, "baseline": BASELINE})


def cmd_apply(args):
    config, _ = paths()
    warnings = []
    data = load_overrides(warnings) if config.exists() else {}
    if warnings:
        fail(warnings[0])
    for key, kind in (("history", list), ("caps", dict), ("repos", dict)):
        if key in data and not isinstance(data[key], kind):
            fail(f"cook.json {key} has the wrong type; fix the file by hand before applying")
    if args.repo and not isinstance(data.get("repos", {}).get(args.repo, {}), dict):
        fail(f"cook.json repos.{args.repo} has the wrong type; fix the file by hand before applying")
    data.setdefault("version", 1)
    data.setdefault("history", [])
    changes = []
    for change in args.change:
        path, _, raw = change.partition("=")
        if path not in set(cap_paths()):
            fail(f"unknown cap {path}")
        try:
            value = int(raw)
        except ValueError:
            fail(f"value for {path} must be an integer")
        if not valid_value(value):
            fail(f"value for {path} must be positive")
        changes.append((path, value))
    current, _, _ = effective(args.repo)
    target = data.setdefault("repos", {}).setdefault(args.repo, {}).setdefault("caps", {}) if args.repo else data.setdefault("caps", {})
    applied = []
    for path, value in changes:
        before = get(current, path)
        put(target, path, value)
        entry = {"date": date.today().isoformat(), "change": f"{path}: {before} -> {value}", "evidence": args.evidence}
        if args.repo:
            entry["repo"] = args.repo
        data["history"].append(entry)
        applied.append(entry)
    config.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(config)
    emit({"applied": applied, "file": str(config)})


def emit(document):
    print(json.dumps(document, indent=2))


def fail(message):
    emit({"error": message})
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("caps", help="effective caps for a repo, with the source of each")
    p.add_argument("--repo")
    sub.add_parser("record", help="append one finished run (JSON on stdin) to the ledger")
    p = sub.add_parser("suggest", help="suggest cap changes from the ledger")
    p.add_argument("--repo")
    p = sub.add_parser("apply", help="write approved cap changes to cook.json")
    p.add_argument("--change", action="append", required=True, metavar="PATH=VALUE")
    p.add_argument("--repo")
    p.add_argument("--evidence", required=True)
    args = parser.parse_args()
    {"caps": cmd_caps, "record": cmd_record, "suggest": cmd_suggest, "apply": cmd_apply}[args.command](args)


if __name__ == "__main__":
    main()
