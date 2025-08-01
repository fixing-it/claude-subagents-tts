# Smart TTS Cache System - Technical Guide

## 🎯 Overview

The Claude Code Hooks system includes an intelligent TTS caching mechanism that dramatically reduces costs and improves performance for audio feedback.

## 💡 How It Works

### 1. Smart Filename Generation
```python
# Standard phrases get human-readable names
"Work complete!" → work-complete.mp3
"Task finished!" → task-finished.mp3

# Custom phrases get sanitized names  
"This is a test message!" → this-is-a-test-message.mp3
```

### 2. Cache Hierarchy
1. **Check cache** - Look for existing audio file
2. **Play cached** - Instant playback if found
3. **Generate new** - API call + cache if not found
4. **Save for future** - Store with smart filename

### 3. Pre-generated Standard Phrases
The system comes with 11 pre-generated audio files:

| Phrase | Filename | Use Case |
|--------|----------|----------|
| "Work complete!" | work-complete.mp3 | General completion |
| "Task finished!" | task-finished.mp3 | Task completion |
| "All done!" | all-done.mp3 | Simple completion |
| "Job complete!" | job-complete.mp3 | Job completion |
| "Ready for next task!" | ready-for-next-task.mp3 | Ready state |
| "Subagent complete!" | subagent-complete.mp3 | Agent completion |
| "Setup completed successfully!" | setup-completed-successfully.mp3 | Setup completion |
| "Test passed!" | test-passed.mp3 | Test success |
| "Build successful!" | build-successful.mp3 | Build success |
| "Deployment complete!" | deployment-complete.mp3 | Deploy success |
| "Analysis finished!" | analysis-finished.mp3 | Analysis done |

## 🔧 Technical Implementation

### Core Script: `cached_elevenlabs_tts.py`

```python
# Key features:
- Smart filename mapping for standard phrases
- MD5 fallback for unknown phrases  
- Automatic cache directory creation
- Error handling with graceful fallbacks
- ElevenLabs Turbo v2.5 integration
```

### Hook Integration

All TTS-capable hooks automatically use the cached version:

```python
def get_tts_script_path():
    if os.getenv('ELEVENLABS_API_KEY'):
        cached_script = tts_dir / "cached_elevenlabs_tts.py"
        if cached_script.exists():
            return str(cached_script)  # ← Uses cached version
        # Fallback to direct version
```

### Setup Tool Integration

The `setup-claude-hooks.py` automatically:
1. Copies pre-generated cache files
2. Creates output directory structure
3. Reports cache file count in setup summary

## 💰 Cost Analysis

### Without Caching
```
"Work complete!" × 100 uses = 100 API calls
Cost: 100 × $0.002 = $0.20
```

### With Caching
```
"Work complete!" × 100 uses = 1 API call + 99 cache hits
Cost: 1 × $0.002 + 99 × $0.00 = $0.002
Savings: 99% cost reduction
```

### Real-World Scenarios

**Daily Development Session:**
- 20x "Work complete!" 
- 10x "Task finished!"
- 5x "Build successful!"
- 5x "Test passed!"

**Without cache**: 40 × $0.002 = $0.08
**With cache**: 4 × $0.002 = $0.008 (90% savings)

**Monthly (20 working days)**: $1.60 → $0.16 savings

## 🔧 Cache Management

### Manual Cache Operations

```bash
# Test cached phrase
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Work complete!"
# Output: 🔄 Using cached audio: work-complete.mp3

# Generate new phrase
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "New custom message"
# Output: 🔊 Generating new audio... 💾 Cached as: new-custom-message.mp3

# View cache contents
ls -la output/tts-cache/
```

### Cache Location
```
project-root/
└── output/
    └── tts-cache/
        ├── work-complete.mp3
        ├── task-finished.mp3
        └── [more cached files]
```

### Cache Maintenance
- **No expiration** - Cache files never expire automatically
- **Manual cleanup** - Remove files manually if needed
- **Regeneration** - Delete file to force regeneration
- **Backup** - Cache files are copied by setup tool

## 🚀 Performance Benefits

### Speed Comparison
| Operation | Direct TTS | Cached TTS |
|-----------|------------|------------|
| API Call | ~2-3 seconds | 0 seconds |
| File I/O | N/A | ~50ms |
| Audio Processing | ~500ms | ~50ms |
| **Total** | **~3 seconds** | **~100ms** |

**Result**: 30x speed improvement for cached phrases

### Network Benefits
- **Reduced API calls** - Less network dependency
- **Offline capability** - Cached phrases work offline
- **Bandwidth savings** - No repeated downloads
- **Latency elimination** - No API round-trip time

## 🛠️ Customization

### Adding New Standard Phrases

Edit `cached_elevenlabs_tts.py`:

```python
STANDARD_PHRASES = {
    "Work complete!": "work-complete.mp3",
    "Task finished!": "task-finished.mp3",
    # Add your phrases here:
    "Code review complete!": "code-review-complete.mp3",
    "Deployment successful!": "deployment-successful.mp3",
}
```

### Generating New Cache

```bash
# Generate new standard phrases
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Code review complete!"
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Deployment successful!"

# Update setup tool cache source
cp -r output/tts-cache/* template-directory/output/tts-cache/
```

## 🔍 Troubleshooting

### Common Issues

**Cache not working:**
```bash
# Check cache directory exists
ls -la output/tts-cache/

# Check file permissions
chmod 644 output/tts-cache/*.mp3
```

**Audio not playing:**
```bash
# Check FFmpeg installation
which ffmpeg
brew install ffmpeg  # macOS
```

**API key issues:**
```bash
# Verify environment variables
echo $ELEVENLABS_API_KEY

# Check .env file
cat .env | grep ELEVENLABS
```

### Debug Mode

Enable verbose output:
```bash
# Add debug flag to script
uv run .claude/hooks/utils/tts/cached_elevenlabs_tts.py "Test" --debug
```

## 📈 Monitoring

### Usage Statistics

Track cache efficiency by monitoring log files:
```bash
# Count cache hits vs API calls
grep "Using cached audio" logs/*.json | wc -l
grep "Generating new audio" logs/*.json | wc -l
```

### Cost Tracking

Monitor ElevenLabs usage:
- Check ElevenLabs dashboard for character usage
- Compare against expected cached vs live generations
- Set up billing alerts for unexpected usage spikes

---

*This caching system provides production-ready TTS optimization for Claude Code workflows.*