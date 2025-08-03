#!/bin/bash

# Dynamic hook runner that works from any directory
# Usage: run_hook.sh <hook_script_name>

# Get the project root from the saved JSON file or use current directory as fallback
PROJECT_ROOT=$(cat .claude/project_root.json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["project_root"])' 2>/dev/null || pwd)

# Change to project root and run the hook with absolute path
cd "$PROJECT_ROOT" && uv run "$PROJECT_ROOT/.claude/hooks/$1"