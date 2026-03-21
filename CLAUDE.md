# hakkasuru-skills

Personal Claude Code skills marketplace. Each subdirectory under `plugins/` is a self-contained plugin.

## Structure

```
hakkasuru-skills/
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json     # Plugin metadata
│       └── skills/
│           └── <skill-name>/
│               └── SKILL.md    # Skill instructions and trigger conditions
└── CLAUDE.md
```

## Adding a Plugin

Create a directory under `plugins/` with a `.claude-plugin/plugin.json` and a `skills/` directory.

Each `SKILL.md` requires YAML frontmatter:

```yaml
---
name: skill-name
description: When to trigger this skill and what it does
---
```

## Installation

```bash
claude plugin marketplace add https://github.com/anderssoh/hakkasuru-skills --scope user
claude plugin install <plugin-name>@hakkasuru-skills
```
