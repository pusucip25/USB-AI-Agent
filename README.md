# USB AI Agent — Portable Uncensored AI + Autonomous Agent

> Plug in. Run one script. Get a fully autonomous AI agent with 13 tools, deep search, OSINT, and persistent memory — all from a portable USB/SSD. Zero install, zero traces.

## 🔥 What Makes This Different

The original [USB-Uncensored-LLM](https://github.com/techjarves/USB-Uncensored-LLM) (now archived) was a great portable chat. **This takes it further** — it's not just a chat, it's an **agent** that can actually DO things.

| Feature | Original | This Project |
|---------|----------|-------------|
| Chat | ✅ | ✅ |
| Web Search | ❌ (broken) | ✅ DuckDuckGo Lite |
| Deep Search (multi-source) | ❌ | ✅ Fetches + reads + synthesizes |
| OSINT (email lookup) | ❌ | ✅ Holehe (121+ sites) |
| OSINT (username search) | ❌ | ✅ Maigret (600+ platforms) |
| OSINT (social search) | ❌ | ✅ Agent Reach (15 platforms) |
| File Operations | ❌ | ✅ Read/Write/List |
| Code Execution | ❌ | ✅ Python + Shell |
| Persistent Memory | ❌ | ✅ Auto-saves to USB |
| Cross-Platform | Partial | ✅ Windows + Linux |
| Autonomous Tool Calling | ❌ | ✅ Model decides which tools to use |

## 🚀 Quick Start

### Windows
```batch
# First time: install engine + models
Windows\install.bat

# Every time: launch the agent
Windows\start-agent.bat
```

### Linux (including Tails)
```bash
# First time: install engine + models
bash Linux/install.sh

# Every time: launch the agent
bash Linux/start-agent.sh
```

## 🛠️ Available Tools

The agent has **13 tools** it can use autonomously:

| Category | Tool | Description |
|----------|------|-------------|
| 🔍 Search | `web_search` | Search the web (DuckDuckGo Lite) |
| 🔍 Search | `deep_search` | Multi-source research (search → fetch → synthesize) |
| 🔍 Search | `web_get` | Download and extract any webpage |
| 🕵️ OSINT | `osint_email` | Check where an email is registered (121+ sites) |
| 🕵️ OSINT | `osint_username` | Find a username across 600+ platforms |
| 🕵️ OSINT | `osint_social` | Search 15 social platforms simultaneously |
| 📁 Files | `read_file` | Read any file on the system |
| 📁 Files | `write_file` | Create or overwrite files |
| 📁 Files | `list_files` | List directory contents |
| ⚡ Exec | `run_command` | Execute shell commands |
| 🐍 Exec | `run_python` | Execute Python code |
| 🧠 Memory | `remember` | Save information persistently |
| 🧠 Memory | `recall` | Retrieve saved information |

## 🧠 Models Included

Pre-configured for 5 uncensored GGUF models (~25GB total):

1. **Gemma 2 2B Abliterated** (~1.7 GB) — Blazing fast, recommended for all
2. **Gemma 4 E4B Ultra Uncensored** (~5.3 GB) — Maximum compliance
3. **Qwen 3.5 9B Uncensored** (~5.6 GB) — Best for agent/tool calling
4. **NemoMix Unleashed 12B** (~7.5 GB) — Heavyweight reasoning
5. **Dolphin 2.9 Llama 3 8B** (~4.9 GB) — Classic uncensored

Models are downloaded once and work on any OS without re-downloading.

## 💻 Requirements

- USB 3.0 drive or SSD with **30+ GB free**
- Host PC: 8 GB RAM minimum (16 GB recommended for 9B/12B models)
- Linux: `python3` (built-in on most distros)
- Windows: nothing (auto-downloads portable Python on first run)

## 📂 Architecture

```
USB-AI-Agent/
├── Windows/
│   ├── install.bat          # Downloads Ollama + models
│   ├── start-agent.bat      # 🆕 Launches the autonomous agent
│   └── start-fast-chat.bat  # Original web chat UI
├── Linux/
│   ├── install.sh           # Downloads Ollama Linux + models
│   ├── start-agent.sh       # 🆕 Launches the agent
│   └── start.sh             # Original web chat
├── Shared/
│   ├── agent.py             # 🆕 The autonomous agent (13 tools)
│   ├── chat_server.py       # Web chat server
│   ├── python/              # Auto-downloaded portable Python
│   ├── bin/                 # Portable Ollama engine
│   └── models/              # GGUF model files
└── .gitignore
```

## 🔒 Privacy

- Everything runs **fully offline** after initial download
- Zero data leaves your machine (except web searches when online)
- No accounts, no telemetry, no tracking
- Chat history saves **only to your USB drive**
- Works on **Tails** and other privacy-focused Linux distros

## 📱 Android Apps

This repo also includes standalone Android applications built with Capacitor + React:

| App | File | Description |
|-----|------|-------------|
| 🛸 **Blu** | `android-apks/Blu-v1.0.apk` | AI talking friend — your personal AI companion |
| 🤖 **ZENO** | `android-apks/ZENO-v1.3-fix.apk` | AI friend v1.3 — improved AI companion with fixes |
| ✈️ **AI Flight Search** | `android-apks/AI-Flight-Search.apk` | AI-powered flight search app |

All apps are Capacitor-based (React + TypeScript) and can be side-loaded on any Android device.

## 🙏 Credits

Built on top of [USB-Uncensored-LLM](https://github.com/techjarves/USB-Uncensored-LLM) by Tech Jarves.

OSINT tools: [Holehe](https://github.com/megadose/holehe), [Maigret](https://github.com/soxoj/maigret), [Agent Reach](https://github.com/Panniantong/Agent-Reach).

## 🔗 More from Pusu

| Project | Description |
|---|---|
| [🛡️ Pusu AdBlocker](https://github.com/pusucip25/pusu-adblocker) | Chrome MV3 ad blocker — 35,000+ rules, zero tracking |
| [🌐 AI-Flight-Search](https://github.com/pusucip25/AI-Flight-Search) | AI-powered flight search engine |
| [💡 ZENO](https://github.com/pusucip25/ZENO) | AI project — details coming soon |

## ⚖️ License

MIT — same as the original project.
