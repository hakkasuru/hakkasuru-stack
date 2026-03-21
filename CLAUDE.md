# hakkasuru-skills

This is a personal Claude Code plugin and skills repository.

## Structure

```
hakkasuru-skills/
├── .claude-plugin/
│   └── plugin.json     # Plugin metadata
├── skills/
│   └── <skill-name>/
│       └── SKILL.md    # Skill instructions and trigger conditions
└── CLAUDE.md
```

## Adding Skills

Create a new directory under `skills/` with a `SKILL.md` file:

```
skills/
  my-skill/
    SKILL.md
```

Each `SKILL.md` requires YAML frontmatter:

```yaml
---
name: my-skill
description: When to trigger this skill and what it does
---
```

## Installation

The parent directory must be registered as a marketplace, then install this plugin:

```bash
claude plugin marketplace add /Users/anderssoh/Workspace --scope user
claude plugin install hakkasuru-skills@Workspace
```
