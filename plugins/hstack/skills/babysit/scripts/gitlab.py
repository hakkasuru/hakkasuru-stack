#!/usr/bin/env python3
"""Read-only GitLab MR watcher for /hstack:babysit. Shells out to `glab`.

Subcommands print one JSON document on stdout. Progress goes to stderr.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from urllib.parse import quote

FLOOR_INTERVAL = 30
CAP_INTERVAL = 600
FALLBACK_INTERVAL = 60
FALLBACK_TIMEOUT = 7200
FLOOR_TIMEOUT = 900
CAP_TIMEOUT = 21600
NO_PIPELINE_POLLS = 3
FINISHED = {"success", "failed", "canceled", "skipped", "manual"}
SKIPPED_SECTIONS = ("after_script", "upload_artifacts", "archive_cache", "cleanup_file_variables")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
LOG_PREFIX = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z [0-9a-f]{2}[OE]\+? ?")
SECTION = re.compile(r"section_(start|end):\d+:([A-Za-z0-9_.-]+)(\[[^\]]*\])?")


class Glab:
    def __init__(self, repo, hostname):
        self.repo = repo
        self.hostname = hostname
        self.project = f"projects/{quote(repo, safe='')}" if repo else "projects/:id"

    def run(self, args):
        out = subprocess.run(["glab"] + args, capture_output=True, text=True)
        if out.returncode != 0:
            return None, (out.stderr or out.stdout).strip()
        return out.stdout, None

    def mr(self, args):
        text, err = self.run(["mr"] + args + ["-F", "json"] + (["-R", self.repo] if self.repo else []))
        return (json.loads(text) if text and text.strip() else None), err

    def api(self, path, raw=False, project=None):
        endpoint = f"{project or self.project}/{path}"
        text, err = self.run(["api", endpoint] + (["--hostname", self.hostname] if self.hostname else []))
        if text is None or raw:
            return text, err
        return (json.loads(text) if text.strip() else None), err


def stack(args, g):
    root, err = g.mr(["view", str(args.mr)])
    if root is None:
        fail(err)
    chain = [slim(root)]
    seen = {root["iid"]}
    target = root["target_branch"]
    while True:
        below, _ = g.mr(["list", "--source-branch", target])
        below = [m for m in (below or []) if m["iid"] not in seen]
        if not below:
            break
        chain.insert(0, slim(below[0]))
        seen.add(below[0]["iid"])
        target = below[0]["target_branch"]
    frontier = [root]
    branches = []
    while frontier:
        node = frontier.pop(0)
        above, _ = g.mr(["list", "--target-branch", node["source_branch"]])
        above = [m for m in (above or []) if m["iid"] not in seen]
        if len(above) > 1:
            branches.append({"at": node["iid"], "children": [m["iid"] for m in above]})
        for m in above:
            seen.add(m["iid"])
            chain.append(slim(m))
            frontier.append(m)
    emit({"trunk": chain[0]["target_branch"], "mrs": chain, "branches": branches})


def slim(mr):
    return {k: mr.get(k) for k in ("iid", "web_url", "state", "source_branch", "target_branch", "sha")}


def calibrate(args, g):
    merged, err = g.mr(["list", "--merged", "--per-page", str(args.samples)])
    if merged is None:
        fail(err)
    samples = []
    for mr in merged[: args.samples]:
        pipelines, _ = g.api(f"merge_requests/{mr['iid']}/pipelines")
        if not pipelines:
            continue
        pipeline, _ = g.api(f"pipelines/{pipelines[0]['id']}")
        if not pipeline or pipeline.get("status") != "success" or not pipeline.get("duration"):
            continue
        samples.append({
            "mr": mr["iid"],
            "url": mr["web_url"],
            "seconds": int(pipeline["duration"]),
            "queued_seconds": int(pipeline.get("queued_duration") or 0),
        })
    if not samples:
        emit({"interval": FALLBACK_INTERVAL, "timeout": FALLBACK_TIMEOUT, "source": "fallback: no merged MRs with a successful pipeline", "samples": []})
        return
    shortest = min(s["seconds"] for s in samples)
    longest = max(s["seconds"] + s["queued_seconds"] for s in samples)
    emit({
        "interval": max(FLOOR_INTERVAL, min(CAP_INTERVAL, shortest)),
        "timeout": max(FLOOR_TIMEOUT, min(CAP_TIMEOUT, 3 * longest)),
        "source": f"{len(samples)} merged MRs: shortest {shortest}s, longest {longest}s including queue",
        "samples": samples,
    })


def watch(args, g):
    started = time.monotonic()
    state = {mr: {"mr": mr, "status": "running", "superseded": [], "empty_polls": 0} for mr in args.mrs}
    while True:
        for mr, entry in state.items():
            if entry["status"] != "running":
                continue
            view, err = g.mr(["view", str(mr)])
            if view is None:
                entry.update(status="error", error=err)
                continue
            entry["url"] = view["web_url"]
            pipeline = view.get("head_pipeline")
            if not pipeline:
                entry["empty_polls"] += 1
                if view["state"] != "opened":
                    entry["status"] = view["state"]
                elif entry["empty_polls"] >= NO_PIPELINE_POLLS:
                    entry["status"] = "no_pipeline"
                continue
            if entry.get("pipeline") and entry["pipeline"]["id"] != pipeline["id"]:
                entry["superseded"].append(entry["pipeline"]["web_url"])
            entry["pipeline"] = {k: pipeline.get(k) for k in ("id", "sha", "status", "web_url")}
            if pipeline["status"] in FINISHED:
                entry["status"] = pipeline["status"]
                log(f"!{mr} {entry['status']}")
        if all(e["status"] != "running" for e in state.values()):
            break
        if time.monotonic() - started + args.interval > args.timeout:
            break
        time.sleep(args.interval)
    elapsed = int(time.monotonic() - started)
    timed_out = any(e["status"] == "running" for e in state.values())
    for entry in state.values():
        entry.pop("empty_polls", None)
    emit({"elapsed_seconds": elapsed, "timed_out": timed_out, "interval": args.interval, "timeout": args.timeout, "mrs": list(state.values())})


def diagnose(args, g):
    view, err = g.mr(["view", str(args.mr)])
    if view is None:
        fail(err)
    pipeline = view.get("head_pipeline")
    if not pipeline:
        emit({"mr": args.mr, "url": view["web_url"], "pipeline_url": None, "failures": []})
        return
    project = f"projects/{pipeline['project_id']}" if pipeline.get("project_id") else None
    failures = failed_jobs(g, project, pipeline["id"], args.lines, depth=0)
    emit({"mr": args.mr, "url": view["web_url"], "pipeline_url": pipeline["web_url"], "failures": failures})


def failed_jobs(g, project, pipeline_id, lines, depth):
    failures = []
    jobs, err = g.api(f"pipelines/{pipeline_id}/jobs?scope[]=failed&per_page=100", project=project)
    if jobs is None:
        return [{"error": err}]
    for job in jobs:
        trace, trace_err = g.api(f"jobs/{job['id']}/trace", raw=True, project=project)
        item = {
            "name": job["name"],
            "stage": job["stage"],
            "job_url": job["web_url"],
            "allow_failure": job.get("allow_failure"),
            "failure_reason": job.get("failure_reason"),
            "log_excerpt": excerpt(trace, lines) if trace else None,
        }
        if trace_err:
            item["log_error"] = trace_err
        failures.append(item)
    bridges, _ = g.api(f"pipelines/{pipeline_id}/bridges?scope[]=failed&per_page=100", project=project)
    for bridge in bridges or []:
        downstream = bridge.get("downstream_pipeline") or {}
        item = {"name": bridge["name"], "stage": bridge["stage"], "job_url": bridge["web_url"], "downstream_pipeline_url": downstream.get("web_url")}
        if downstream.get("id") and depth < 2:
            item["downstream_failures"] = failed_jobs(g, f"projects/{downstream['project_id']}", downstream["id"], lines, depth + 1)
        failures.append(item)
    return failures


def excerpt(trace, lines):
    rows, skipping = [], None
    for raw in trace.replace("\r\n", "\n").split("\n"):
        line = ANSI.sub("", raw.split("\r")[-1] if "section_" not in raw else raw)
        marker = SECTION.search(line)
        if marker:
            kind, name = marker.group(1), marker.group(2)
            if kind == "start" and name.startswith(SKIPPED_SECTIONS):
                skipping = name
            elif kind == "end" and name == skipping:
                skipping = None
            line = ANSI.sub("", SECTION.sub("", line).split("\r")[-1])
        line = LOG_PREFIX.sub("", line)
        if skipping is None and line.strip():
            rows.append(line)
    return "\n".join(rows[-lines:])


def log(message):
    print(f"[{datetime.now():%H:%M:%S}] {message}", file=sys.stderr, flush=True)


def emit(document):
    print(json.dumps(document, indent=2))


def fail(message):
    emit({"error": message})
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-R", "--repo", help="GROUP/PROJECT, defaults to the current directory's repo")
    parser.add_argument("--hostname", help="GitLab host for API calls, for self-managed instances")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("stack", help="list the open MR stack around an MR, bottom first")
    p.add_argument("mr")
    p = sub.add_parser("calibrate", help="derive the poll interval and timeout from recent merged MRs")
    p.add_argument("--samples", type=int, default=10)
    p = sub.add_parser("watch", help="poll MR head pipelines until all finish or the timeout passes")
    p.add_argument("--interval", type=int, required=True)
    p.add_argument("--timeout", type=int, required=True)
    p.add_argument("mrs", nargs="+")
    p = sub.add_parser("diagnose", help="failed jobs of an MR's head pipeline, with log excerpts")
    p.add_argument("mr")
    p.add_argument("--lines", type=int, default=80)
    args = parser.parse_args()
    g = Glab(args.repo, args.hostname)
    {"stack": stack, "calibrate": calibrate, "watch": watch, "diagnose": diagnose}[args.command](args, g)


if __name__ == "__main__":
    main()
