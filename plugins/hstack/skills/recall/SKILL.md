---
name: recall
description: "Rebuild recent working context from this repo's Claude Code session transcripts, its worktrees, live git and MR state, and the shared record, then hand back a short brief: capsule, thread status, problems, and the next move."
disable-model-invocation: true
---

# Recall

**Before you start or resume work, you rebuild the user's recent working context and hand back a tight capsule of where things stand now and what to do next.**

Keep it tight and on-topic. Read only what the in-scope threads need, then stop.

Your context lives in two records. Your own chat history holds what you did and decided. The shared record holds everything that happened around the same code under other names: the symptoms users keep reporting, the fixes that shipped and got reverted, the errors still firing in prod. That second record is what `/hstack:why` searches, across source control, the issue tracker, chat and issue channels, long-form docs, and error tracking. A feature with a long bug tail keeps most of its story there, so don't reconstruct it from your transcripts alone.

Transcripts live at `~/.claude/projects/<slug>/<session-id>.jsonl`, where `<slug>` is the absolute path with every character other than a letter, digit, or `-` replaced by `-` (so `/Users/you/proj` becomes `-Users-you-proj`, and `/Users/you/proj/.claude/worktrees/x` becomes `-Users-you-proj--claude-worktrees-x`). Subagent transcripts sit in a folder named after the session. Every line is one entry with `cwd`, `gitBranch`, `timestamp`, and the message. Claude Code deletes transcripts after 30 days by default (`cleanupPeriodDays`), so older work isn't recoverable this way.

1. Classify the request. Recall loads working context across recent sessions before you act. A human-readable summary of your work is a different task. If the user already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. Lock the scope before searching. Pin the window ("recent" is a real range, default the last 7 days, overridable with `--days N`), the topic if named, and the repo. The repo includes its worktrees from `git worktree list`; their transcripts live under their own slugs. Never read another project's transcripts without being asked. Skip the current session. State the scope back. Never quietly turn "all" into "recent N".
3. Fan out across your session history. Spawn parallel `general-purpose` subagents with `model: sonnet` through the Agent tool, each taking a slice of the corpus. Tell every subagent to order candidates by real modification time (`ls -t`) and never by session ID, grep the topic first and then read only the matching sessions and only their relevant regions, and skip the current session plus obvious noise (subagent, eval, and test sessions). Each returns the same schema, one block per session: topic, the user's goal, decisions, open threads, struggles and corrections, and artifacts (PRs, MRs, tickets, branches), each citing the session ID. For one or two sessions, skip the fan-out and search directly. The raw transcripts stay in the subagents. The main thread gets only their findings.
4. Sweep the shared record whenever the topic names a feature, file, subsystem, area, or bug. This is the default, not a judgment call, and "my work on X" does not exempt it. Hand it to `/hstack:why` (read [../why/SKILL.md](../why/SKILL.md)) and its source investigators, but steer their question from "why was this built this way" to "what's the current state, what's been tried and didn't hold, and what are users still reporting". Reuse its per-source playbooks, run the investigators in parallel with the session-history mining, and inherit its posture: one investigator per source, null results are findings, skip an unavailable source and say so. Fold what comes back into the brief. Skip this step only for pure activity recall with no named target ("what did I do this week"), where your own history and live state are the entire answer.
5. Verify against live state. Take the PRs, MRs, branches, and tickets that the mining and the sweep surfaced and check them with `git`, and `gh` or `glab` depending on the host. When the answer hinges on what an agent actually did (the tools it ran, files it read, errors it hit), read the full transcript, not just a summary.
6. Write the brief to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move. Deeper detail goes below or gets cut.

- **Capsule.** At most 5 bullets. What this work is and where it stands overall.
- **Threads.** One line each, prefixed with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[open MR !N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]`. A thread with no tag is not done yet, so tag it. If a transcript contains a line starting `cook state ·`, quote the newest one verbatim under Threads.
- **Problems.** At most 5, the recurring ones. Include the symptoms users keep reporting and any fix that shipped and was reverted, so the next attempt starts where the last one failed.
- **Next move.** The single most useful next action, concrete.

An adjacent feature or ticket stays out unless it blocks this one. When the capsule and thread lines outgrow a screen, cut detail before you cut threads. Write the brief through `/hstack:unslop` (read [../unslop/SKILL.md](../unslop/SKILL.md)), cite session findings by session ID and shared-record findings by their source (PR #, MR !, ticket key, chat permalink), and sanitize private context before any public output.

**Reply:** the brief, to the contract above.
