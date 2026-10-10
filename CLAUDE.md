# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# hakkasuru-stack

Claude Code plugins marketplace. Each subdirectory under `plugins/` is a self-contained plugin. Plugins are plain Markdown and JSON, with one exception: `hstack`'s `babysit` skill ships Python scripts. There is no build or lint step.

## Structure

```
hakkasuru-stack/
├── .claude-plugin/
│   └── marketplace.json    # Marketplace manifest; registers every plugin
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json # Plugin metadata (name, description, version, author)
│       ├── THIRD_PARTY_NOTICES.md   # Only when content is adapted from elsewhere
│       └── skills/
│           └── <skill-name>/
│               ├── SKILL.md
│               ├── references/      # Optional supporting files, linked relatively from SKILL.md
│               └── scripts/         # Optional executables the skill runs (babysit only today)
└── CLAUDE.md
```

## Validation

```bash
claude plugin validate .                    # marketplace manifest
claude plugin validate plugins/<plugin-name> # a single plugin manifest
```

For skill scripts (`plugins/hstack/skills/babysit/scripts/*.py`):

```bash
python3 -m py_compile plugins/hstack/skills/babysit/scripts/*.py
python3 plugins/hstack/skills/babysit/scripts/github.py -R cli/cli calibrate      # read-only, against a public repo
python3 plugins/hstack/skills/babysit/scripts/gitlab.py -R gitlab-org/cli calibrate
```

Test every subcommand read-only against real public repos (`cli/cli` on GitHub, `gitlab-org/cli` on GitLab). For paths you can't reach live, such as a pipeline still running at the timeout, put stub `gh` or `glab` executables first on `PATH`. Delete `__pycache__/` before committing.

## Adding a Plugin

1. Create a directory under `plugins/<plugin-name>/`
2. Add `.claude-plugin/plugin.json`:
   ```json
   {
     "name": "plugin-name",
     "description": "What this plugin does",
     "version": "0.1.0",
     "author": { "name": "hakkasuru" }
   }
   ```
3. Add skills under `skills/<skill-name>/SKILL.md` with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: What the skill does (plus when to trigger it, if the model may invoke it)
   ---
   ```
   Add `disable-model-invocation: true` for skills that should only run when the user explicitly invokes them. Every `hstack` skill sets it. Those skills' descriptions only say what the skill does, with no trigger phrases.
4. Register the plugin in `.claude-plugin/marketplace.json` under `plugins`:
   ```json
   {
     "name": "plugin-name",
     "source": "./plugins/plugin-name",
     "description": "What this plugin does"
   }
   ```

## Conventions

- Plugin skills are invoked namespaced as `/<plugin>:<skill>` (e.g. `/hstack:create-verification-skill`). Skills refer to each other by these names. If you rename a skill or plugin, update every reference to it.
- A skill with `disable-model-invocation: true` can't be called through the Skill tool, even by another skill. A skill that builds on another one reads it by relative path instead (`../<skill>/SKILL.md`). For example, `teach` reads `how` and `why`, `hermes` and `teach` read `unslop`, and `babysit` reads `hermes`. Keep these paths valid when renaming.
- Skill bodies are written for a Claude agent that reads them cold in the middle of a task, not for human readers. `hstack` skill headings use sentence case.
- Skill scripts run by absolute path from the skill's base directory, use only the Python 3 standard library, and stay read-only.
- Skills that reach external systems prefer a terminal CLI (`gh`, `glab`, `aws`, `gcloud`, `snow`) and fall back to an MCP server. They never run a login command. An unauthenticated source is reported as a gap.
- Two skills are built to be extended. To add an evidence source to `why`, follow `why/references/adding-a-source.md`. To add a watch target to `babysit`, follow the runbook contract in `babysit/SKILL.md`.
- When you change a plugin's content, bump `version` in its `plugin.json`. Existing installs use the version to detect updates. Commits are split as content, then the notices change, then the bump in its own commit (e.g. "Bump hstack to 0.2.0"). Commits go straight to `main`.

## Adapting skills from pstack

Most `hstack` skills are adapted from Cursor's pstack plugin (MIT), at `https://github.com/cursor/plugins/tree/main/pstack/skills`. `hermes` is pstack's `technical-writing` renamed.

- Fetch upstream files with `gh api repos/cursor/plugins/contents/<path> -H "Accept: application/vnd.github.raw"`. Follow the skill's relative links to pull in the skills it depends on.
- Replace Cursor-specific mechanics with Claude Code equivalents: the `Task` tool and its `readonly` flag become the Agent tool, the `pstack-models.mdc` model rule becomes the Agent `model` parameter, Cursor's `mcps/` directory becomes `mcp__<server>__<tool>` tools, and references to pstack skills hstack doesn't have get dropped or replaced.
- Keep `plugins/hstack/THIRD_PARTY_NOTICES.md` accurate. List adapted skills there. Files you write from scratch inside an adapted skill's directory are listed as original to hstack. A skill written entirely from scratch, like `babysit`, needs no entry.

## Installation

```bash
claude plugin marketplace add hakkasuru/hakkasuru-stack --scope user
claude plugin install <plugin-name>@hakkasuru-stack
claude plugin list                                  # verify
claude plugin marketplace update hakkasuru-stack   # pick up a new version
```
