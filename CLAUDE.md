# hakkasuru-stack

Claude Code plugins marketplace. Each subdirectory under `plugins/` is a self-contained plugin.

## Structure

```
hakkasuru-stack/
├── .claude-plugin/
│   └── marketplace.json    # Marketplace manifest
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json # Plugin metadata
│       └── skills/
│           └── <skill-name>/
│               └── SKILL.md
└── CLAUDE.md
```

## Adding a Plugin

1. Create a directory under `plugins/<plugin-name>/`
2. Add `.claude-plugin/plugin.json`:
   ```json
   {
     "name": "plugin-name",
     "description": "What this plugin does"
   }
   ```
3. Add skills under `skills/<skill-name>/SKILL.md` with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: When to trigger this skill and what it does
   ---
   ```
4. Register the plugin in `.claude-plugin/marketplace.json` under `plugins`:
   ```json
   {
     "name": "plugin-name",
     "source": "./plugins/plugin-name",
     "description": "What this plugin does"
   }
   ```

## Installation

```bash
claude plugin marketplace add hakkasuru/hakkasuru-stack --scope user
claude plugin install <plugin-name>@hakkasuru-stack
```

## Validation

```bash
claude plugin validate .
```
