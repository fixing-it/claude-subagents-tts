#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "rich",
# ]
# ///

"""
Claude Code Hooks & Sub-Agents Setup Tool

Kopiert ein funktionsfähiges Claude Code Template mit konfigurierten 
Hooks und Sub-Agents in ein neues Projekt-Verzeichnis.

Usage:
    uv run setup-claude-hooks.py /path/to/new/project
    uv run setup-claude-hooks.py /path/to/new/project --interactive
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()

# Template source directory (current directory)
TEMPLATE_DIR = Path(__file__).parent

# Available MCP servers
AVAILABLE_MCPS = {
    "firecrawl": {
        "name": "Firecrawl MCP",
        "description": "Web scraping and crawling",
        "npm_package": "firecrawl-mcp",
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
        "env_vars": ["FIRECRAWL_API_KEY"]
    },
    "github": {
        "name": "GitHub MCP", 
        "description": "GitHub repository operations", 
        "npm_package": "@modelcontextprotocol/server-github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    },
    "elevenlabs": {
        "name": "ElevenLabs MCP",
        "description": "Text-to-speech with ElevenLabs",
        "python_package": "elevenlabs-mcp",
        "command": "uvx",
        "args": ["elevenlabs-mcp"],
        "env_vars": ["ELEVENLABS_API_KEY"]
    },
    "context7": {
        "name": "Context7 MCP",
        "description": "Up-to-date code documentation",
        "npm_package": "@upstash/context7-mcp",
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"],
        "env_vars": []
    },
    "serena": {
        "name": "Serena MCP",
        "description": "Coding agent toolkit with semantic retrieval",
        "python_package": "git+https://github.com/oraios/serena",
        "command": "uvx",
        "args": ["--from", "git+https://github.com/oraios/serena", "serena-mcp-server"],
        "env_vars": []
    }
}

def create_project_structure(target_dir: Path) -> bool:
    """Create the basic project structure."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "logs").mkdir(exist_ok=True)
        return True
    except Exception as e:
        console.print(f"❌ Error creating project structure: {e}", style="red")
        return False

def copy_claude_directory(target_dir: Path) -> bool:
    """Copy .claude directory with all configurations."""
    source_claude = TEMPLATE_DIR / ".claude"
    target_claude = target_dir / ".claude"
    
    if not source_claude.exists():
        console.print("❌ Source .claude directory not found!", style="red")
        return False
    
    try:
        if target_claude.exists():
            shutil.rmtree(target_claude)
        shutil.copytree(source_claude, target_claude)
        console.print("✅ Copied .claude directory", style="green")
        return True
    except Exception as e:
        console.print(f"❌ Error copying .claude directory: {e}", style="red")
        return False

def copy_tts_cache(target_dir: Path) -> bool:
    """Copy pre-generated TTS cache files for common phrases."""
    source_cache = TEMPLATE_DIR / "output" / "tts-cache"
    target_output = target_dir / "output"
    target_cache = target_output / "tts-cache"
    
    if not source_cache.exists():
        console.print("⚠️  No TTS cache found, skipping", style="yellow")
        return True  # Not an error, just no cache to copy
    
    try:
        # Create output directory
        target_output.mkdir(exist_ok=True)
        
        # Copy cache directory
        if target_cache.exists():
            shutil.rmtree(target_cache)
        shutil.copytree(source_cache, target_cache)
        
        # Count cached files
        cached_files = len(list(target_cache.glob("*.mp3")))
        console.print(f"✅ Copied TTS cache ({cached_files} files)", style="green")
        return True
    except Exception as e:
        console.print(f"⚠️  Warning: Could not copy TTS cache: {e}", style="yellow")
        return True  # Non-critical error

def select_mcps(interactive: bool = False) -> list:
    """Select MCP servers to install."""
    if not interactive:
        return []
    
    console.print("\n🔧 MCP Server Selection", style="bold blue")
    
    # Show available MCPs in a table
    table = Table(title="Available MCP Servers")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="green")
    
    mcp_ids = list(AVAILABLE_MCPS.keys())
    for i, (mcp_id, mcp_info) in enumerate(AVAILABLE_MCPS.items(), 1):
        table.add_row(str(i), mcp_info["name"], mcp_info["description"])
    
    console.print(table)
    
    # Get selection
    selected_mcps = []
    console.print("\nSelect MCP servers (comma-separated numbers, e.g., '1,3,5' or 'none'):")
    console.print("Recommended: [cyan]4,5[/cyan] (context7, serena)", style="dim")
    selection = Prompt.ask("Your choice", default="none")
    
    if selection.lower() != "none":
        try:
            indices = [int(x.strip()) for x in selection.split(',')]
            for idx in indices:
                if 1 <= idx <= len(mcp_ids):
                    selected_mcps.append(mcp_ids[idx - 1])
        except ValueError:
            console.print("⚠️  Invalid selection, skipping MCPs", style="yellow")
    
    return selected_mcps

def install_mcps(target_dir: Path, selected_mcps: list) -> bool:
    """Install selected MCP servers - just create configuration, no actual installation."""
    if not selected_mcps:
        return True
    
    success_count = 0
    for mcp_id in selected_mcps:
        mcp_info = AVAILABLE_MCPS[mcp_id]
        console.print(f"🔧 Configuring {mcp_info['name']}...")
        success_count += 1
    
    if success_count > 0:
        console.print(f"✅ Configured {success_count} MCP servers", style="green")
    
    return success_count == len(selected_mcps)

def create_mcp_settings(target_dir: Path, selected_mcps: list) -> bool:
    """Create or update .claude/settings.json with MCP configuration."""
    if not selected_mcps:
        return True
    
    settings_file = target_dir / ".claude" / "settings.json"
    
    # Read existing settings or create new
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        except Exception:
            pass
    
    # Add MCP servers configuration
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    
    for mcp_id in selected_mcps:
        mcp_info = AVAILABLE_MCPS[mcp_id]
        settings["mcpServers"][mcp_id] = {
            "command": mcp_info["command"],
            "args": mcp_info["args"]
        }
        
        # Add environment variables if needed
        if mcp_info["env_vars"]:
            settings["mcpServers"][mcp_id]["env"] = {
                var: f"${{{var}}}" for var in mcp_info["env_vars"]
            }
    
    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        console.print("✅ Updated settings.json with MCP configuration", style="green")
        return True
    except Exception as e:
        console.print(f"❌ Failed to update settings.json: {e}", style="red")
        return False

def create_env_files(target_dir: Path, interactive: bool = False) -> bool:
    """Copy existing .env or create .env.sample file with API key templates."""
    source_env = TEMPLATE_DIR / ".env"
    target_env_sample = target_dir / ".env.sample"
    target_env = target_dir / ".env"
    
    # If source .env exists, copy it
    if source_env.exists():
        try:
            shutil.copy2(source_env, target_env)
            console.print("✅ Copied existing .env file", style="green")
            
            # Also create .env.sample as template
            try:
                shutil.copy2(source_env, target_env_sample)
                console.print("✅ Created .env.sample as backup template", style="green")
            except Exception as e:
                console.print(f"⚠️  Warning: Could not create .env.sample: {e}", style="yellow")
            
            return True
        except Exception as e:
            console.print(f"❌ Error copying .env file: {e}", style="red")
            # Fall through to create template
    
    # Create .env.sample template if no .env exists
    env_content = """ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
ELEVENLABS_API_KEY=
ENGINEER_NAME=YourName
FIRECRAWL_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
OLLAMA_HOST=
OPENAI_API_KEY="""
    
    if interactive:
        console.print("\n🔑 API Key Configuration", style="bold blue")
        engineer_name = Prompt.ask("Engineer Name", default="YourName")
        env_content = env_content.replace("YourName", engineer_name)
        
        # Ask for specific API keys
        if Confirm.ask("Configure ElevenLabs API Key?", default=False):
            elevenlabs_key = Prompt.ask("ElevenLabs API Key", password=True, default="")
            if elevenlabs_key:
                env_content = env_content.replace("ELEVENLABS_API_KEY=", f"ELEVENLABS_API_KEY={elevenlabs_key}")
        
        # Create actual .env file in interactive mode
        try:
            target_env.write_text(env_content)
            console.print("✅ Created .env file with your configuration", style="green")
        except Exception as e:
            console.print(f"❌ Error creating .env file: {e}", style="red")
    
    try:
        target_env_sample.write_text(env_content)
        console.print(f"✅ Created .env.sample template", style="green")
        return True
    except Exception as e:
        console.print(f"❌ Error creating .env.sample: {e}", style="red")
        return False

def create_readme(target_dir: Path, project_name: str) -> bool:
    """Create README.md with setup instructions."""
    readme_content = f"""# {project_name}

Claude Code Projekt mit konfigurierten Hooks, Sub-Agents und intelligentem TTS-Caching.

## 🚀 Setup

### 1. API Keys konfigurieren
```bash
cp .env.sample .env
# Edit .env und trage deine API Keys ein
# Mindestens ELEVENLABS_API_KEY für TTS Features
```

### 2. Testen
```bash
hi claude              # Greeting Agent
tts summary           # TTS Summary Agent  
build new agent       # Meta-Agent

# TTS Cache testen
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Work complete!"
```

## 🎵 Features

- **3 Sub-Agents**: hello-world, tts-summary, meta-agent
- **8 Hooks**: Vollständige Lifecycle-Abdeckung
- **Smart TTS Cache**: Pre-generated common phrases (11 files), automatic caching
- **Cost Optimization**: 99% Kostenreduktion für häufige Phrasen
- **Intelligent Fallback**: ElevenLabs → OpenAI → pyttsx3
- **Security**: Gefährliche Commands werden blockiert
- **Logging**: Alle Aktivitäten werden geloggt

## 📁 Struktur

```
.claude/
├── agents/              # Sub-Agents
├── commands/            # Slash Commands  
├── hooks/               # Python Hook Scripts
│   └── utils/tts/       # TTS Provider Scripts
│       ├── cached_elevenlabs_tts.py  # Smart caching (primary)
│       ├── elevenlabs_tts.py         # Direct TTS (fallback)
│       ├── openai_tts.py
│       └── pyttsx3_tts.py
└── settings.json        # Hook Konfiguration
output/
└── tts-cache/          # Pre-generated audio files (11 standard phrases)
    ├── work-complete.mp3
    ├── task-finished.mp3
    └── [9 more cached phrases]
```

## 💰 TTS Cost Optimization

**Pre-cached Phrases** (kostenlos nach Setup):
- "Work complete!", "Task finished!", "All done!"
- "Job complete!", "Ready for next task!"
- "Subagent complete!", "Test passed!"
- "Build successful!", "Setup completed successfully!"

**Cost Example**: 
- Erste Generation: ~$0.002 pro Phrase
- Weitere Nutzung: $0.00 (Cache)
- 100x "Work complete!": $0.002 statt $0.20

---
*Erstellt mit setup-claude-hooks.py - Template mit intelligentem TTS-Caching*
"""
    
    try:
        (target_dir / "README.md").write_text(readme_content)
        console.print("✅ Created README.md", style="green")
        return True
    except Exception as e:
        console.print(f"❌ Error creating README.md: {e}", style="red")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Setup Claude Code Hooks & Sub-Agents Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run setup-claude-hooks.py /path/to/new/project
  uv run setup-claude-hooks.py ./my-project --interactive
        """
    )
    parser.add_argument(
        "target_directory",
        help="Target directory for the new project"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive setup with API key configuration"
    )
    parser.add_argument(
        "--mcps",
        help="Comma-separated list of MCP servers to install (firecrawl,github,elevenlabs,context7,serena)"
    )
    
    args = parser.parse_args()
    
    target_dir = Path(args.target_directory).resolve()
    project_name = target_dir.name
    
    # Header
    console.print(Panel.fit(
        Text("Claude Code Hooks & Sub-Agents Setup", style="bold blue"),
        style="blue"
    ))
    
    console.print(f"📁 Target Directory: {target_dir}")
    console.print(f"📝 Project Name: {project_name}")
    console.print(f"🔧 Interactive Mode: {'Yes' if args.interactive else 'No'}")
    
    if target_dir.exists() and any(target_dir.iterdir()):
        if not Confirm.ask(f"Directory {target_dir} is not empty. Continue?", default=False):
            console.print("❌ Aborted by user", style="red")
            sys.exit(1)
    
    console.print("\n🚀 Starting setup...", style="bold")
    
    # MCP selection
    selected_mcps = []
    if args.mcps:
        # Command line MCP selection
        requested_mcps = [mcp.strip() for mcp in args.mcps.split(',')]
        selected_mcps = [mcp for mcp in requested_mcps if mcp in AVAILABLE_MCPS]
        if selected_mcps != requested_mcps:
            invalid = set(requested_mcps) - set(selected_mcps)
            console.print(f"⚠️  Invalid MCPs ignored: {', '.join(invalid)}", style="yellow")
    elif args.interactive:
        selected_mcps = select_mcps(args.interactive)
    
    if selected_mcps:
        console.print(f"📦 Selected MCPs: {', '.join(selected_mcps)}", style="cyan")
    
    # Setup steps
    steps = [
        ("Creating project structure", lambda: create_project_structure(target_dir)),
        ("Copying .claude directory", lambda: copy_claude_directory(target_dir)),
        ("Copying TTS cache", lambda: copy_tts_cache(target_dir)),
        ("Installing MCP servers", lambda: install_mcps(target_dir, selected_mcps)),
        ("Configuring MCP settings", lambda: create_mcp_settings(target_dir, selected_mcps)),
        ("Setting up environment files", lambda: create_env_files(target_dir, args.interactive)),
        ("Creating README.md", lambda: create_readme(target_dir, project_name)),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        console.print(f"\n📋 {step_name}...")
        if step_func():
            success_count += 1
        else:
            console.print(f"❌ Failed: {step_name}", style="red")
    
    # Summary
    console.print("\n" + "="*50)
    if success_count == len(steps):
        console.print("🎉 Setup completed successfully!", style="bold green")
        console.print(f"\n📁 Project created at: {target_dir}")
        console.print("\n🚀 Next steps:")
        console.print("1. cd " + str(target_dir))
        console.print("2. cp .env.sample .env")
        console.print("3. Edit .env with your API keys")
        console.print("4. Test with: hi claude")
    else:
        console.print(f"⚠️  Setup completed with {len(steps) - success_count} errors", style="yellow")
        sys.exit(1)

if __name__ == "__main__":
    main()