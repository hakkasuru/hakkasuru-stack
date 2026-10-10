#!/usr/bin/env python3
"""Read-only GitHub PR watcher for /hstack:babysit. Shells out to `gh`.

Subcommands print one JSON document on stdout. Progress goes to stderr.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime

FLOOR_INTERVAL = 30
CAP_INTERVAL = 600
FALLBACK_INTERVAL = 60
FALLBACK_TIMEOUT = 7200
FLOOR_TIMEOUT = 900
CAP_TIMEOUT = 21600
NO_PIPELINE_POLLS = 3
PR_FIELDS = "number,url,state,headRefName,baseRefName,headRefOid"
CHECK_FIELDS = "name,bucket,state,link,workflow,startedAt,completedAt"


def gh(args, repo):
    cmd = ["gh"] + args + (["-R", repo] if repo else [])
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0 and not out.stdout.strip():
        return None, out.stderr.strip()
    return out.stdout, None


def gh_json(args, repo):
    text, err = gh(args, repo)
    if text is None:
        return None, err
    return json.loads(text) if text.strip() else None, None


def parse_time(value):
    if not value or value.startswith("0001-"):
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def checks_for(pr, repo):
    data, err = gh_json(["pr", "checks", str(pr), "--json", CHECK_FIELDS], repo)
    if data is None and err and "no checks reported" in err:
        return [], None
    return data or [], err


def stack(args):
    root, err = gh_json(["pr", "view", str(args.pr), "--json", PR_FIELDS], args.repo)
    if root is None:
        fail(err)
    chain = [root]
    seen = {root["number"]}
    base = root["baseRefName"]
    while True:
        below, _ = gh_json(["pr", "list", "--head", base, "--state", "open", "--json", PR_FIELDS], args.repo)
        below = [p for p in (below or []) if p["number"] not in seen]
        if not below:
            break
        chain.insert(0, below[0])
        seen.add(below[0]["number"])
        base = below[0]["baseRefName"]
    frontier = [root]
    branches = []
    while frontier:
        node = frontier.pop(0)
        above, _ = gh_json(["pr", "list", "--base", node["headRefName"], "--state", "open", "--json", PR_FIELDS], args.repo)
        above = [p for p in (above or []) if p["number"] not in seen]
        if len(above) > 1:
            branches.append({"at": node["number"], "children": [p["number"] for p in above]})
        for p in above:
            seen.add(p["number"])
            chain.append(p)
            frontier.append(p)
    emit({"trunk": chain[0]["baseRefName"], "prs": chain, "branches": branches})


def pipeline_seconds(checks):
    durations = []
    for c in checks:
        start, end = parse_time(c.get("startedAt")), parse_time(c.get("completedAt"))
        if c.get("bucket") in ("pass", "fail") and start and end:
            durations.append(int((end - start).total_seconds()))
    return max(durations) if durations else None


def calibrate(args):
    merged, err = gh_json(["pr", "list", "--state", "merged", "--limit", str(args.samples), "--json", "number,url"], args.repo)
    if merged is None:
        fail(err)
    samples = []
    for pr in merged:
        checks, _ = checks_for(pr["number"], args.repo)
        seconds = pipeline_seconds(checks)
        if seconds and seconds > 0:
            samples.append({"pr": pr["number"], "url": pr["url"], "seconds": seconds})
    emit(choose(samples))


def choose(samples):
    if not samples:
        return {"interval": FALLBACK_INTERVAL, "timeout": FALLBACK_TIMEOUT, "source": "fallback: no merged PRs with finished checks", "samples": []}
    shortest = min(s["seconds"] for s in samples)
    longest = max(s["seconds"] for s in samples)
    return {
        "interval": max(FLOOR_INTERVAL, min(CAP_INTERVAL, shortest)),
        "timeout": max(FLOOR_TIMEOUT, min(CAP_TIMEOUT, 3 * longest)),
        "source": f"{len(samples)} merged PRs: shortest {shortest}s, longest {longest}s",
        "samples": samples,
    }


def outcome(checks):
    buckets = {c.get("bucket") for c in checks}
    if "pending" in buckets:
        return "running"
    if "fail" in buckets:
        return "failed"
    if "cancel" in buckets:
        return "canceled"
    return "success"


def watch(args):
    started = time.monotonic()
    state = {pr: {"pr": pr, "status": "running", "superseded": [], "empty_polls": 0} for pr in args.prs}
    while True:
        for pr, entry in state.items():
            if entry["status"] != "running":
                continue
            view, err = gh_json(["pr", "view", str(pr), "--json", PR_FIELDS], args.repo)
            if view is None:
                entry.update(status="error", error=err)
                continue
            entry["url"] = view["url"]
            sha = view["headRefOid"]
            if entry.get("sha") and entry["sha"] != sha:
                entry["superseded"].append(entry["sha"])
                entry["empty_polls"] = 0
            entry["sha"] = sha
            checks, err = checks_for(pr, args.repo)
            if err and not checks:
                entry.update(status="error", error=err)
                continue
            entry["checks"] = checks
            if not checks:
                entry["empty_polls"] += 1
                if view["state"] != "OPEN":
                    entry["status"] = view["state"].lower()
                elif entry["empty_polls"] >= NO_PIPELINE_POLLS:
                    entry["status"] = "no_pipeline"
                continue
            entry["status"] = outcome(checks)
            if entry["status"] != "running":
                log(f"#{pr} {entry['status']}")
        if all(e["status"] != "running" for e in state.values()):
            break
        if time.monotonic() - started + args.interval > args.timeout:
            break
        time.sleep(args.interval)
    elapsed = int(time.monotonic() - started)
    timed_out = any(e["status"] == "running" for e in state.values())
    for entry in state.values():
        entry.pop("empty_polls", None)
    emit({"elapsed_seconds": elapsed, "timed_out": timed_out, "interval": args.interval, "timeout": args.timeout, "prs": list(state.values())})


def diagnose(args):
    checks, err = checks_for(args.pr, args.repo)
    if err and not checks:
        fail(err)
    failures = []
    for check in checks:
        if check.get("bucket") != "fail":
            continue
        link = check.get("link") or ""
        item = {"name": check.get("name"), "workflow": check.get("workflow"), "job_url": link}
        match = re.search(r"/actions/runs/(\d+)/job/(\d+)", link)
        if match:
            item["run_url"] = link.split("/job/")[0]
            log_text, log_err = gh(["run", "view", "--job", match.group(2), "--log-failed"], args.repo)
            item["log_excerpt"] = excerpt(log_text, args.lines) if log_text else None
            if log_err:
                item["log_error"] = log_err
        else:
            item["log_excerpt"] = None
            item["log_error"] = "external check: logs not reachable through gh, open job_url"
        failures.append(item)
    view, _ = gh_json(["pr", "view", str(args.pr), "--json", "url"], args.repo)
    emit({"pr": args.pr, "url": (view or {}).get("url"), "failures": failures})


LOG_PREFIX = re.compile(r"^[^\t]*\t[^\t]*\t\d{4}-\d\d-\d\dT[\d:.]+Z ?")


def excerpt(text, lines):
    rows = [LOG_PREFIX.sub("", row) for row in text.rstrip().splitlines()]
    errors = [i for i, row in enumerate(rows) if "##[error]" in row]
    if not errors:
        return "\n".join(rows[-lines:])
    start = max(0, errors[0] - lines // 4)
    end = min(len(rows), errors[-1] + 3, start + lines)
    return "\n".join(rows[start:end])


def log(message):
    print(f"[{datetime.now():%H:%M:%S}] {message}", file=sys.stderr, flush=True)


def emit(document):
    print(json.dumps(document, indent=2))


def fail(message):
    emit({"error": message})
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-R", "--repo", help="OWNER/REPO, defaults to the current directory's repo")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("stack", help="list the open PR stack around a PR, bottom first")
    p.add_argument("pr")
    p = sub.add_parser("calibrate", help="derive the poll interval and timeout from recent merged PRs")
    p.add_argument("--samples", type=int, default=10)
    p = sub.add_parser("watch", help="poll PR checks until all finish or the timeout passes")
    p.add_argument("--interval", type=int, required=True)
    p.add_argument("--timeout", type=int, required=True)
    p.add_argument("prs", nargs="+")
    p = sub.add_parser("diagnose", help="failed checks of a PR, with log excerpts for GitHub Actions jobs")
    p.add_argument("pr")
    p.add_argument("--lines", type=int, default=80)
    args = parser.parse_args()
    {"stack": stack, "calibrate": calibrate, "watch": watch, "diagnose": diagnose}[args.command](args)


if __name__ == "__main__":
    main()
