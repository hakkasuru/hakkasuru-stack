---
name: how
description: "Explain how a part of the codebase works: subsystem architecture, runtime flow, and where code lives, at the level a senior engineer needs to start working in it. Uses parallel explorers for large subsystems."
disable-model-invocation: true
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

Companion to `/hstack:why`. `how` answers what the code does and how it works. `why` answers what forces led to its shape. If the question is about motivation ("why is it built this way?", "why this limit?"), tell the user `/hstack:why` is the better fit, and answer only the "how" part here.

Every subagent below is read-only. Spawn them with the Agent tool, and keep the read-only instruction that the prompt templates carry. If a `model` value is rejected, leave `model` unset and say so.

## Step 1. Assess complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. One explainer explores and explains in a single pass. Go to Step 2b.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): spawn parallel explorers first, then hand off to the explainer. Go to Step 2a.

When in doubt, take the simple path.

## Step 2a. Explore (complex questions only)

Decompose the question into 2 to 4 exploration angles, each a distinct slice of the subsystem. Spawn all explorers in a single message:

- `subagent_type`: `general-purpose`
- `model`: `sonnet`

Each explorer gets the prompt in [references/explorer-prompt.md](references/explorer-prompt.md) with its angle filled in. Wait until every explorer has returned, then go to Step 3.

## Step 2b. Direct explain (simple questions)

Spawn one subagent that explores and explains in one pass:

- `subagent_type`: `general-purpose`
- `model`: unset, so it inherits yours

Build its prompt from [references/explainer-prompt.md](references/explainer-prompt.md), following the template's note for the direct path. Go to Step 4.

## Step 3. Synthesize (complex questions only)

Spawn one subagent to synthesize the explorers' findings into one explanation:

- `subagent_type`: `general-purpose`
- `model`: unset, so it inherits yours

Build its prompt from [references/explainer-prompt.md](references/explainer-prompt.md) with every explorer's findings filled in.

## Step 4. Present

The user can't see subagent output, so present the explainer's output yourself. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

## Output format

The explanation uses the sections defined in [references/explainer-prompt.md](references/explainer-prompt.md), dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
