# Setup Hooks Command

This command sets up the hook system by dynamically configuring all hook commands with the current working directory.

## Usage
```
/setup-hooks
```

## What it does
1. Gets the current working directory (project root)
2. Updates all hook commands in `.claude/settings.json` to use absolute paths
3. Creates/updates `.claude/project_root.json` with the current path
4. Makes all hook scripts executable

This ensures hooks work correctly regardless of where Claude Code is started from.