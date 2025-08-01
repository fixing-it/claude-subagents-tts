#!/bin/bash
# Wrapper script to ensure UV is in PATH for Claude Code

# Add UV to PATH
export PATH="$HOME/.local/bin:$PATH"

# Execute UV with all arguments
exec uv "$@"