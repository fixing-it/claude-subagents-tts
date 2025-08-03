#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import os
import stat
import sys
from pathlib import Path

def setup_hooks():
    """Setup hook system by configuring all hook commands with absolute paths."""
    
    # Get current working directory (project root)
    project_root = Path.cwd().resolve()
    print(f"Setting up hooks for project: {project_root}")
    
    # Create .claude directory if it doesn't exist
    claude_dir = project_root / '.claude'
    claude_dir.mkdir(exist_ok=True)
    
    # Save project root to JSON file
    project_root_file = claude_dir / 'project_root.json'
    with open(project_root_file, 'w') as f:
        json.dump({"project_root": str(project_root)}, f, indent=2)
    print(f"✓ Created {project_root_file}")
    
    # Read current settings
    settings_file = claude_dir / 'settings.json'
    if not settings_file.exists():
        print(f"❌ Settings file not found: {settings_file}")
        return False
    
    with open(settings_file, 'r') as f:
        settings = json.load(f)
    
    # Hook configurations with their script names and arguments
    hook_configs = {
        "PreToolUse": ("pre_tool_use.py", ""),
        "PostToolUse": ("post_tool_use.py", ""),
        "Notification": ("notification.py", "--notify"),
        "Stop": ("stop.py", "--chat"),
        "SubagentStop": ("subagent_stop.py", ""),
        "UserPromptSubmit": ("user_prompt_submit.py", "--log-only"),
        "PreCompact": ("pre_compact.py", ""),
        "SessionStart": ("session_start.py", "")
    }
    
    # Update hook commands with absolute paths
    updated_hooks = 0
    for hook_name, (script_name, args) in hook_configs.items():
        if hook_name not in settings.get('hooks', {}):
            continue
            
        script_path = project_root / '.claude' / 'hooks' / script_name
        
        # Check if script exists
        if not script_path.exists():
            print(f"⚠️  Hook script not found: {script_path}")
            continue
        
        # Make script executable
        script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
        
        # Build command with absolute path
        if args:
            command = f'cd "{project_root}" && uv run "{script_path}" {args}'
        else:
            command = f'cd "{project_root}" && uv run "{script_path}"'
        
        # Update all hooks for this hook type
        hook_list = settings['hooks'][hook_name]
        for hook_config in hook_list:
            if 'hooks' in hook_config:
                for hook_item in hook_config['hooks']:
                    if hook_item.get('type') == 'command':
                        hook_item['command'] = command
                        updated_hooks += 1
                        print(f"✓ Updated {hook_name}: {script_name}")
    
    # Write updated settings back
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print(f"\n✅ Successfully updated {updated_hooks} hook commands")
    print(f"📁 Project root: {project_root}")
    print(f"🔧 All hooks now use absolute paths and should work correctly")
    
    return True

if __name__ == '__main__':
    try:
        success = setup_hooks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error setting up hooks: {e}")
        sys.exit(1)