# Claude Code Sub-Agents & Hooks Mastery

Complete demonstration of Claude Code sub-agents and hooks system for deterministic control over AI coding workflows with intelligent TTS caching.

> **Based on**: This project builds upon and extends the excellent work from [claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery/tree/main) by disler, adding intelligent TTS caching, automated project setup, and cost optimization features.

## 🎯 Features

### Sub-Agents
- **hello-world-agent** - Friendly greeting with tech news
- **work-completion-summary** - Audio summaries with ElevenLabs TTS
- **meta-agent** - Agent that builds other agents

### Hooks (All 8 Lifecycle Events)
- **UserPromptSubmit** - Prompt logging and validation
- **PreToolUse** - Security blocking (dangerous commands)
- **PostToolUse** - Tool result logging and transcript conversion
- **Notification** - TTS alerts for user input needs
- **Stop** - AI-generated completion messages with TTS
- **SubagentStop** - "Subagent Complete" announcements
- **PreCompact** - Transcript backup before compaction
- **SessionStart** - Development context loading

### Smart TTS System
- **Intelligent Caching** - Pre-generated common phrases for instant playback
- **Cost Optimization** - 99% cost reduction for frequent phrases
- **Automatic Fallback** - ElevenLabs → OpenAI → pyttsx3
- **Smart Filenames** - Human-readable cache files (work-complete.mp3)
- **Live Generation** - New phrases automatically generated and cached

## 🚀 Quick Start

### Prerequisites
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [UV](https://docs.astral.sh/uv/getting-started/installation/) - Fast Python package manager
- [ElevenLabs API Key](https://elevenlabs.io/) (optional, for TTS features)
- [FFmpeg](https://ffmpeg.org/) - For audio playback (`brew install ffmpeg`)

### Setup Tool
Create new projects instantly with the automated setup tool:
```bash
# Create new project with template + cached TTS
uv run setup-claude-hooks.py /path/to/new/project

# Interactive setup with API key configuration
uv run setup-claude-hooks.py ./my-project --interactive
```

### Manual Usage

**Sub-Agents:**
```bash
# Activate greeting agent
hi claude

# Get audio work summary  
tts summary

# Create new agent
build a new sub agent that runs tests
```

**Cached TTS:**
```bash
# Test cached phrases (instant playback)
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Work complete!"

# New phrases are generated and cached automatically
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Custom message here"
```

**Hooks in Action:**
- All prompts are logged to `logs/user_prompt_submit.json`
- Dangerous commands like `rm -rf` are blocked
- Completion messages are generated with AI and spoken via cached TTS
- Session starts load git status and development context

## 📁 Project Structure

```
subagents_v1/
├── .claude/
│   ├── agents/              # Sub-Agents
│   │   ├── hello-world.md   # Greeting agent
│   │   ├── meta-agent.md    # Agent builder
│   │   └── tts-summary.md   # TTS work summaries  
│   ├── commands/            # Custom slash commands
│   │   ├── prime.md         # Development workflow
│   │   ├── prime-tts.md     # Dev workflow with TTS
│   │   └── all-tools.md     # Tool inventory
│   ├── hooks/               # Python hook scripts
│   │   ├── user_prompt_submit.py
│   │   ├── pre_tool_use.py
│   │   ├── post_tool_use.py
│   │   ├── notification.py
│   │   ├── stop.py
│   │   ├── subagent_stop.py
│   │   ├── pre_compact.py
│   │   ├── session_start.py
│   │   └── utils/           # TTS and LLM utilities
│   │       ├── tts/         # TTS Provider Scripts
│   │       │   ├── cached_elevenlabs_tts.py  # Smart caching (primary)
│   │       │   ├── elevenlabs_tts.py         # Direct TTS (fallback)
│   │       │   ├── openai_tts.py
│   │       │   └── pyttsx3_tts.py
│   │       └── llm/         # LLM Utilities
│   └── settings.json        # Hook configuration
├── logs/                    # Hook execution logs
├── output/                  # Generated files
│   └── tts-cache/          # Pre-generated audio files
│       ├── work-complete.mp3
│       ├── task-finished.mp3
│       ├── all-done.mp3
│       └── [9 more standard phrases]
├── setup-claude-hooks.py    # Automated project setup tool
└── README.md               # This file
```

## 🔧 Hook Configuration

Hooks are configured in `.claude/settings.json` with UV single-file scripts:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command", 
            "command": "uv run .claude/hooks/user_prompt_submit.py --log-only"
          }
        ]
      }
    ]
  }
}
```

## 🎨 Hook Flow Control

### Exit Codes
- **0** - Success (stdout shown in transcript mode)
- **2** - Blocking error (stderr fed to Claude automatically)
- **Other** - Non-blocking error (stderr shown to user)

### Key Blocking Capabilities
- **UserPromptSubmit** - Can block prompts, add context
- **PreToolUse** - Can block tool execution
- **Stop** - Can force continuation
- **PostToolUse** - Cannot block (tool already executed)

### Security Features
- Blocks dangerous `rm -rf` commands
- Prevents access to sensitive files (`.env`)
- Validates tool parameters before execution
- Logs all activities for audit trails

## 🎵 Smart TTS Integration

### Intelligent Caching System
The TTS system uses smart caching to optimize costs and performance:

**Pre-generated Standard Phrases** (instant playback):
- "Work complete!", "Task finished!", "All done!"
- "Job complete!", "Ready for next task!"
- "Subagent complete!", "Test passed!", "Build successful!"
- "Setup completed successfully!", "Analysis finished!", "Processing complete!"

**Automatic Caching** for new phrases:
- First use: Generated via ElevenLabs API + cached
- Subsequent uses: Instant playback from cache
- Smart filenames: `work-complete.mp3` instead of hash

### Provider Hierarchy
Audio feedback using multiple providers with intelligent fallback:
1. **ElevenLabs** (primary) - `cached_elevenlabs_tts.py` with caching
2. **OpenAI** - Backup TTS provider  
3. **pyttsx3** - Local fallback

### Cost Optimization
- **Standard phrases**: ~99% cost reduction after first generation
- **Custom phrases**: Generated once, then free forever
- **ElevenLabs Turbo v2.5**: ~$0.18 per 1000 chars
- **Example**: "Work complete!" = $0.002 once, then $0.00

Configuration via environment variables:
```bash
export ELEVENLABS_API_KEY="your-key"
export OPENAI_API_KEY="your-key"  
export ENGINEER_NAME="YourName"
```

## 📊 Logging

All hook executions are logged as JSON:
- `logs/user_prompt_submit.json` - User prompts
- `logs/pre_tool_use.json` - Tool blocking events
- `logs/post_tool_use.json` - Tool completions
- `logs/stop.json` - Completion events
- `logs/chat.json` - Readable conversation transcript

## 🔍 Best Practices

### Sub-Agents
- Write system prompts, not user prompts
- Sub-agents respond to primary agent, not user
- Use `description` field for automatic delegation
- Include explicit trigger phrases

### Hooks  
- Use UserPromptSubmit for early intervention
- Use PreToolUse for prevention 
- Use PostToolUse for validation
- Handle errors gracefully with clear messages
- Avoid infinite loops in Stop hooks

## 🚀 Advanced Usage

### Automated Project Setup
```bash
# Quick project creation with full template
uv run setup-claude-hooks.py /path/to/new/project

# Interactive setup with API key entry
uv run setup-claude-hooks.py ./my-project --interactive

# Setup includes:
# - Complete .claude directory structure
# - Pre-generated TTS cache (11 audio files)
# - Environment files (.env + .env.sample)
# - Project-specific README
```

### Meta-Agent Workflow
```bash
# The meta-agent builds agents from descriptions
"Create a performance testing agent that runs benchmarks"

# It will:
# 1. Scrape latest Claude Code docs
# 2. Generate properly formatted agent
# 3. Select minimal required tools
# 4. Create structured system prompt
```

### TTS Cache Management
```bash
# Test specific cached phrases
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Work complete!"

# Generate and cache custom phrases
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Custom completion message"

# Cache location: ./output/tts-cache/
# Standard phrases are pre-generated and copied by setup tool
```

### Hook Customization
Each hook supports command-line flags:
- `--log-only` (UserPromptSubmit) - Just log, no validation
- `--validate` (UserPromptSubmit) - Enable security checks
- `--notify` (Notification) - Enable TTS alerts
- `--chat` (Stop) - Generate chat transcript

## 📚 Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code Hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code Sub-Agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [UV Single-File Scripts](https://docs.astral.sh/uv/guides/scripts/)

## 🎬 Demo

Try these commands to see the system in action:

1. **Project Setup**: `uv run setup-claude-hooks.py ./demo-project` → Creates full template
2. **Greeting**: `hi claude` → Activates hello-world agent
3. **Work Summary**: `tts summary` → Audio completion summary
4. **Agent Creation**: `build a new code reviewer agent`
5. **Cached TTS**: Audio feedback uses pre-generated phrases for instant playback
6. **Custom Command**: `/prime` → Professional development workflow

All activities are logged and include intelligent audio feedback with cost optimization!

---

*This project demonstrates mastery of Claude Code's most advanced features for building sophisticated AI coding workflows.*