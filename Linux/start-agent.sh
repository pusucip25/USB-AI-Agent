#!/bin/bash
# ===================================================
#  USB AI AGENT - Portable Agent (Linux)
# ===================================================
#  Porneste Ollama portabil + agentul AI autonom.
#  Merge pe orice Linux, inclusiv Tails (cu Tor).
# ===================================================

echo "==================================================="
echo "    USB AI AGENT - Agent Portabil pe SSD (Linux)"
echo "==================================================="
echo ""
echo "  Ruleaza un agent AI autonom cu modele locale."
echo "  OSINT, deep search, fisiere, cod — totul pe USB."
echo ""

# ---- Paths ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(dirname "$SCRIPT_DIR")"
SHARED_DIR="$USB_ROOT/Shared"
OLLAMA_RUNTIME="$SHARED_DIR/.ollama-runtime"
mkdir -p "$OLLAMA_RUNTIME"

# ---- Full portability: keep EVERYTHING on the USB ----
export OLLAMA_MODELS="$SHARED_DIR/models/ollama_data"
export OLLAMA_HOME="$OLLAMA_RUNTIME"
export OLLAMA_TMPDIR="$OLLAMA_RUNTIME/tmp"
export OLLAMA_ORIGINS="*"
export OLLAMA_HOST="127.0.0.1:11434"
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_KEEP_ALIVE=300s
mkdir -p "$OLLAMA_RUNTIME/tmp"

# -------------------------------------------------------
# Check if portable Linux engine is available
# -------------------------------------------------------
if [ ! -x "$SHARED_DIR/bin/ollama-linux" ]; then
    echo "==================================================="
    echo "  ERROR: Linux AI Engine Not Found!"
    echo "==================================================="
    echo ""
    echo "  Ruleaza mai intai:"
    echo "    bash install.sh"
    echo "  din acest folder pentru a descarca Ollama Linux."
    echo ""
    read -n 1 -s -r -p "Press any key to continue..."
    echo ""
    exit 1
fi

# -------------------------------------------------------
# Start Ollama Engine (if not already running)
# -------------------------------------------------------
if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "[OK] Ollama engine is already running!"
else
    echo "Starting Linux AI Engine..."
    HOME="$OLLAMA_RUNTIME" "$SHARED_DIR/bin/ollama-linux" serve &
    OLLAMA_PID=$!
    
    echo -n "Waiting for engine "
    for i in $(seq 1 60); do
        if curl -s http://127.0.0.1:11434/api/tags | grep -q '"models"'; then
            echo " [OK]"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    if ! curl -s http://127.0.0.1:11434/api/tags | grep -q '"models"'; then
        echo ""
        echo "ERROR: Engine did not become ready in 60 seconds."
        [ -n "$OLLAMA_PID" ] && kill "$OLLAMA_PID" 2>/dev/null
        exit 1
    fi
fi

# -------------------------------------------------------
# Start Agent
# -------------------------------------------------------
echo ""
echo "==================================================="
echo "  AGENT PORNIT"
echo "  Scrie /help pentru comenzi, /exit pentru a iesi"
echo "  Apasa Ctrl+C pentru a opri totul."
echo "==================================================="
echo ""

# Launch agent using system Python
if command -v python3 &> /dev/null; then
    python3 "$SHARED_DIR/agent.py"
elif command -v python &> /dev/null; then
    python "$SHARED_DIR/agent.py"
else
    echo "ERROR: Python not found. Install python3:"
    echo "  sudo apt install python3    (Debian/Ubuntu/Tails)"
    echo "  sudo pacman -S python       (Arch)"
    exit 1
fi

# Cleanup - only kill if we started it
if [ -n "$OLLAMA_PID" ]; then
    echo ""
    echo "Shutting down Ollama..."
    kill $OLLAMA_PID 2>/dev/null
    wait $OLLAMA_PID 2>/dev/null
fi

echo "Done. Goodbye!"
