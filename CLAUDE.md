# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# hakkasuru-stack

Claude Code plugins marketplace. There is no build, lint, or test step. Every plugin is plain Markdown and JSON. Each subdirectory under `plugins/` is a self-contained plugin.

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
│               └── references/      # Optional supporting files, linked relatively from SKILL.md
└── CLAUDE.md
```

## Validation

```bash
claude plugin validate .                    # marketplace manifest
claude plugin validate plugins/<plugin-name> # a single plugin manifest
```

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
   description: When to trigger this skill and what it does
   ---
   ```
   Add `disable-model-invocation: true` for skills that should only run when the user explicitly invokes them (as the `hstack` verification skills do).
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
- When you change a plugin's content, bump `version` in its `plugin.json`. Existing installs use the version to detect updates. Make the bump its own commit (e.g. "Bump hstack to 0.2.0").
- Skill bodies are written for a Claude agent that reads them cold in the middle of a task, not for human readers.
- `hstack`'s skills are adapted from Cursor's pstack plugin (MIT); `hermes` is pstack's `technical-writing` renamed. Keep `plugins/hstack/THIRD_PARTY_NOTICES.md` accurate when you add or rename adapted content.

## Installation

```bash
claude plugin marketplace add hakkasuru/hakkasuru-stack --scope user
claude plugin install <plugin-name>@hakkasuru-stack
claude plugin list   # verify
```
