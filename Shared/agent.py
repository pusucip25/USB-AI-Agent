#!/usr/bin/env python3
"""
USB AI Agent — Agent autonom pe SSD extern
============================================
Un agent care rulează direct de pe USB/SSD, folosind Ollama portabil.
Are tools (fișiere, web, cod) și memorie persistentă.

Pornește cu: python agent.py
Sau din: Windows/start-agent.bat
"""

import json
import os
import sys
import re
import time
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import html
import traceback
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR / "agent_data"
MEMORY_FILE = AGENT_DIR / "memory.json"
CONFIG_FILE = AGENT_DIR / "config.json"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = "qwen3.5:9b"  # fallback, se rescrie din config

# ═══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Ești un agent AI autonom care rulează de pe un SSD portabil. Ai acces la instrumente reale pentru a ajuta utilizatorul.

## Instrumentele tale

Când ai nevoie să execuți o acțiune, răspunzi EXACT în formatul:

<tool>
  <name>nume_instrument</name>
  <params>{json}</params>
</tool>

Instrumente disponibile:

1. **read_file** — citește un fișier
   Parametri: {"path": "calea/catre/fișier"}

2. **write_file** — scrie/crează un fișier
   Parametri: {"path": "calea/catre/fișier", "content": "conținutul"}

3. **list_files** — listează fișierele dintr-un folder
   Parametri: {"path": "calea/catre/folder"}

4. **run_command** — execută o comandă în terminal (Windows)
   Parametri: {"command": "comanda"}

5. **run_python** — execută cod Python
   Parametri: {"code": "codul python"}

6. **web_search** — caută pe internet
   Parametri: {"query": "termeni de căutare"}

7. **web_get** — descarcă o pagină web
   Parametri: {"url": "https://..."}

8. **deep_search** — search + citește conținutul paginilor (mult mai puternic!)
   Parametri: {"query": "întrebare", "num_sources": 3}

9. **remember** — salvează informație în memorie
   Parametri: {"key": "cheie", "value": "valoare"}

10. **recall** — citește din memorie
   Parametri: {"key": "cheie"}

## OSINT Tools (investigații)

11. **osint_email** — verifică pe ce site-uri e înregistrat un email
   Parametri: {"email": "adresa@exemplu.com"}

12. **osint_username** — caută un username pe sute de platforme
   Parametri: {"username": "nume123"}

13. **osint_social** — caută pe platforme sociale (Twitter, Reddit, etc.)
   Parametri: {"query": "termen căutare", "platform": "twitter"}  // platform e opțional

## Reguli

- Folosește instrumentele când ai nevoie de informații reale sau să execuți acțiuni
- După fiecare instrument, vei primi rezultatul și poți continua
- Pune UN SINGUR tool pe răspuns
- Dacă nu ai nevoie de niciun tool, răspunde normal în limba utilizatorului
- Vorbește în română dacă utilizatorul vorbește română
- Ești direct și eficient"""

# ═══════════════════════════════════════════════════════════════════════
# PERSISTENT MEMORY
# ═══════════════════════════════════════════════════════════════════════

def load_memory():
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_memory(mem):
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"model": DEFAULT_MODEL, "temperature": 0.7}

def save_config(cfg):
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════════
# OLLAMA API
# ═══════════════════════════════════════════════════════════════════════

def ollama_request(endpoint, data=None, method="GET"):
    """Trimite o cerere la API-ul Ollama."""
    url = f"{OLLAMA_HOST}/api/{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else None
    
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": str(e)}

def list_models():
    """Listează modelele disponibile în Ollama."""
    result = ollama_request("tags")
    if "models" in result:
        return [m["name"] for m in result["models"]]
    return []

def chat_stream(model, messages, temperature=0.7):
    """
    Trimite un chat request la Ollama și returnează răspunsul complet.
    Folosește streaming pentru a arăta progresul.
    """
    data = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature}
    }
    
    url = f"{OLLAMA_HOST}/api/chat"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    
    full_response = ""
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            # Citește linie cu linie (streaming JSON)
            buffer = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line.strip():
                        try:
                            msg = json.loads(line.decode("utf-8"))
                            if "message" in msg and "content" in msg["message"]:
                                content = msg["message"]["content"]
                                full_response += content
                                print(content, end="", flush=True)
                            if msg.get("done"):
                                return full_response
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        print(f"\n[Eroare Ollama: {e}]")
        return full_response or f"[Eroare: {e}]"
    
    return full_response

# ═══════════════════════════════════════════════════════════════════════
# TOOL PARSER
# ═══════════════════════════════════════════════════════════════════════

def parse_tool_call(text):
    """
    Extrage un tool call din răspunsul modelului.
    Format: <tool><name>nume</name><params>{json}</params></tool>
    """
    pattern = r"<tool>\s*<name>(.*?)</name>\s*<params>(.*?)</params>\s*</tool>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        name = match.group(1).strip()
        try:
            params = json.loads(match.group(2).strip())
        except json.JSONDecodeError:
            params = {}
        return name, params, match.group(0)
    return None, None, None

# ═══════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════

def tool_read_file(params):
    path = params.get("path", "")
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    try:
        content = Path(path).read_text(encoding="utf-8", errors="replace")
        if len(content) > 5000:
            content = content[:5000] + f"\n... [trunchiat, {len(content)} caractere total]"
        return content
    except FileNotFoundError:
        return f"[Eroare] Fișierul nu există: {path}"
    except Exception as e:
        return f"[Eroare] {e}"

def tool_write_file(params):
    path = params.get("path", "")
    content = params.get("content", "")
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return f"[OK] Fișier salvat: {path} ({len(content)} caractere)"
    except Exception as e:
        return f"[Eroare] {e}"

def tool_list_files(params):
    path = params.get("path", ".")
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    try:
        items = []
        for f in sorted(Path(path).iterdir()):
            if f.is_dir():
                items.append(f"📁 {f.name}/")
            else:
                size = f.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                items.append(f"📄 {f.name} ({size_str})")
        if not items:
            return "[Gol]"
        return "\n".join(items[:50]) + (f"\n... și încă {len(items) - 50}" if len(items) > 50 else "")
    except Exception as e:
        return f"[Eroare] {e}"

def tool_run_command(params):
    command = params.get("command", "")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, 
                                text=True, timeout=30, cwd=os.getcwd())
        output = result.stdout.strip() or result.stderr.strip()
        if len(output) > 3000:
            output = output[:3000] + "\n... [trunchiat]"
        return output or "[comanda executată fără output]"
    except subprocess.TimeoutExpired:
        return "[Eroare] Comanda a durat prea mult (30s timeout)"
    except Exception as e:
        return f"[Eroare] {e}"

def tool_run_python(params):
    code = params.get("code", "")
    try:
        # Capture stdout
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            exec(code, {"__builtins__": __builtins__})
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return output.strip() or "[cod executat fără output]"
    except Exception as e:
        return f"[Eroare Python] {type(e).__name__}: {e}"

def tool_web_search(params):
    query = params.get("query", "")
    
    # DuckDuckGo Lite cu user-agent de browser text (nu e blocat)
    url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"[Eroare căutare] {e}"
    
    # Parsează rezultatele DuckDuckGo Lite
    results = []
    
    # Găsește toate linkurile de rezultate - structura:
    # <a rel="nofollow" href="//duckduckgo.com/l/?uddg=..." class='result-link'>Title</a>
    # apoi <td class='result-snippet'>snippet</td>
    link_pattern = re.compile(
        r"""<a[^>]*href="([^"]*)"[^>]*class='result-link'[^>]*>(.*?)</a>""",
        re.DOTALL
    )
    snippet_pattern = re.compile(
        r"""<td[^>]*class='result-snippet'[^>]*>(.*?)</td>""",
        re.DOTALL
    )
    
    links = link_pattern.findall(html_content)
    snippets = snippet_pattern.findall(html_content)
    
    for i, (href, title) in enumerate(links[:6]):
        # DuckDuckGo redirect URL — extrage URL-ul real
        uddg_match = re.search(r"uddg=(https?%3A[^&]+)", href)
        if uddg_match:
            real_url = urllib.parse.unquote(uddg_match.group(1))
        else:
            real_url = href
        
        title_clean = re.sub(r"<[^>]*>", "", title).strip()
        title_clean = html.unescape(title_clean)
        
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r"<[^>]*>", "", snippets[i]).strip()
            snippet = html.unescape(snippet)[:200]
        
        if not title_clean:
            continue
        
        results.append(f"{i+1}. **{title_clean}**\n   {snippet}\n   {real_url}")
    
    return "\n\n".join(results) if results else "[Niciun rezultat găsit]"

def tool_web_get(params):
    url = params.get("url", "")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            # Scoate tag-urile HTML
            text = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]*>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 4000:
                text = text[:4000] + f"\n... [trunchiat, {len(text)} caractere total]"
            return text
    except Exception as e:
        return f"[Eroare] {e}"

def tool_remember(params, memory):
    key = params.get("key", "")
    value = params.get("value", "")
    memory[key] = {"value": value, "timestamp": datetime.now().isoformat()}
    save_memory(memory)
    return f"[OK] Salvat '{key}' în memorie"

def tool_recall(params, memory):
    key = params.get("key", "")
    if key in memory:
        entry = memory[key]
        return f"[Memorie] {key}: {entry['value']} (salvat la {entry['timestamp']})"
    return f"[Memorie] Nu am găsit '{key}'"

def tool_deep_search(params):
    """
    Deep search: caută, citește conținutul paginilor, și returnează totul.
    Mult mai puternic decât un search simplu — intră efectiv pe pagini.
    """
    query = params.get("query", "")
    num_sources = min(params.get("num_sources", 3), 5)
    
    print(f"\n  🔍 Deep search: \"{query}\"...")
    
    # Pasul 1: Caută
    search_results = tool_web_search({"query": query})
    if search_results.startswith("[Niciun rezultat") or search_results.startswith("[Eroare"):
        return search_results
    
    # Extrage URL-urile din rezultate
    urls = re.findall(r"(https?://[^\s\n]+)", search_results)
    if not urls:
        return "[Deep search] Nu am găsit URL-uri în rezultatele căutării."
    
    urls = urls[:num_sources]
    
    # Pasul 2: Fetch + extract din fiecare URL
    all_content = []
    for i, url in enumerate(urls):
        print(f"  📄 Fetch [{i+1}/{len(urls)}]: {url[:60]}...", end="", flush=True)
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")
            
            # Curăță HTML-ul
            text = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<footer[^>]*>.*?</footer>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<header[^>]*>.*?</header>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]*>", " ", text)
            text = re.sub(r"&[a-z]+;", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            
            # Limitează la ~2000 caractere per sursă
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            all_content.append(f"--- Sursa {i+1}: {url} ---\n{text}")
            print(f" ✓ ({len(text)} chars)")
        except Exception as e:
            print(f" ✗ ({e})")
            all_content.append(f"--- Sursa {i+1}: {url} ---\n[Eroare la fetch: {e}]")
    
    result = f"🔎 DEEP SEARCH: \"{query}\"\n{'='*50}\n\n"
    result += "\n\n".join(all_content)
    result += f"\n\n{'='*50}\nSurse analizate: {len(urls)}. Acum sintetizează informația."
    
    return result


# ═══════════════════════════════════════════════════════════════════════
# OSINT TOOLS (Agent Reach + Holehe + Maigret)
# ═══════════════════════════════════════════════════════════════════════

def _get_portable_python():
    """Găsește Python-ul portabil de pe SSD, cross-platform."""
    import platform
    if platform.system() == "Windows":
        py = SCRIPT_DIR / "python" / "python.exe"
        if py.exists():
            return str(py)
    # Linux / macOS: folosește python3 din sistem
    for cmd in ["python3", "python"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            return cmd
        except Exception:
            continue
    return sys.executable

def _get_osint_cli(tool_name):
    """Găsește executabilul CLI al unui tool OSINT, cross-platform.
    Returnează o listă de argumente pentru subprocess."""
    import platform
    python = _get_portable_python()
    
    if platform.system() == "Windows":
        exe = SCRIPT_DIR / "python" / "Scripts" / f"{tool_name}.exe"
        if exe.exists():
            return [str(exe)]
    
    # Linux / macOS: folosește modulul Python
    module = tool_name.replace("-", "_")
    return [python, "-m", module]

def tool_osint_email(params):
    """OSINT: Verifică dacă un email e înregistrat pe 100+ site-uri (Holehe)."""
    email = params.get("email", "").strip()
    if not email or "@" not in email:
        return "[Eroare] Adresa de email nu pare validă."
    
    print(f"\n  🕵️ OSINT Email: {email}")
    print(f"  ⏳ Verific 100+ site-uri... (~15 sec)")
    
    cli = _get_osint_cli("holehe")
    try:
        result = subprocess.run(
            [cli, email, "--only-used"],
            capture_output=True, text=True, timeout=90, cwd=str(SCRIPT_DIR)
        )
        # Holehe pune output-ul frumos în stdout
        output = result.stdout.strip()
        # Curăță progress bars și blank lines
        output = re.sub(r'\r?\n?\r.*?\d+%.*?\r', '', output)
        output = re.sub(r'\n\s*\n\s*\n', '\n\n', output)
        if len(output) > 3000:
            output = output[:3000] + "\n... [trunchiat]"
        return output or "[Niciun rezultat - emailul nu a fost găsit pe site-urile verificate]"
    except subprocess.TimeoutExpired:
        return "[Timeout] Verificarea a durat prea mult."
    except Exception as e:
        return f"[Eroare OSINT] {e}"

def tool_osint_username(params):
    """OSINT: Caută un username pe sute de platforme (Maigret)."""
    username = params.get("username", "").strip()
    if not username:
        return "[Eroare] Username-ul nu poate fi gol."
    
    print(f"\n  🕵️ OSINT Username: @{username}")
    print(f"  ⏳ Caut pe sute de site-uri... (~45 sec)")
    
    cli = _get_osint_cli("maigret")
    try:
        result = subprocess.run(
            [cli, username, "--timeout", "10",
             "--no-recursive", "--no-extracting"],
            capture_output=True, text=True, timeout=120, cwd=str(SCRIPT_DIR)
        )
        output = result.stdout.strip() or result.stderr.strip()
        # Curăță output-ul
        output = re.sub(r'\r?\n?\r.*?\d+%.*?\r', '', output)
        if len(output) > 4000:
            output = output[:4000] + "\n... [trunchiat]"
        return output or "[Niciun rezultat]"
    except subprocess.TimeoutExpired:
        return "[Timeout] Căutarea a durat prea mult."
    except Exception as e:
        return f"[Eroare OSINT] {e}"

def tool_osint_social(params):
    """OSINT: Caută pe 15 platforme sociale (Agent Reach)."""
    query = params.get("query", "").strip()
    platform = params.get("platform", "").strip().lower()
    
    if not query:
        return "[Eroare] Query-ul nu poate fi gol."
    
    platforms_ok = ["twitter", "reddit", "youtube", "linkedin", "facebook",
                   "instagram", "tiktok", "github", "medium", "wikipedia"]
    
    if platform and platform not in platforms_ok:
        return f"[Eroare] Platforma '{platform}' invalidă. Încearcă: {', '.join(platforms_ok)}"
    
    print(f"\n  🕵️ OSINT Social: \"{query}\"" + 
          (f" pe {platform}" if platform else " (toate)"))
    
    cli = _get_osint_cli("agent-reach")
    try:
        cmd = [cli, "search", query]
        if platform:
            cmd = [cli, "read", "--platform", platform, query]
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=45, cwd=str(SCRIPT_DIR)
        )
        output = result.stdout.strip() or result.stderr.strip()
        if len(output) > 4000:
            output = output[:4000] + "\n... [trunchiat]"
        return output or "[Niciun rezultat]"
    except subprocess.TimeoutExpired:
        return "[Timeout] Căutarea a durat prea mult."
    except Exception as e:
        cli_str = " ".join(cli)
        return (
            f"🕵️ Agent Reach e instalat dar necesită configurare.\n\n"
            f"Rulează manual prima dată:\n"
            f"  {cli_str} doctor\n"
            f"  {cli_str} install --env=auto\n\n"
            f"Detalii: {e}"
        )


TOOL_MAP = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_files": tool_list_files,
    "run_command": tool_run_command,
    "run_python": tool_run_python,
    "web_search": tool_web_search,
    "web_get": tool_web_get,
    "deep_search": tool_deep_search,
    "osint_email": tool_osint_email,
    "osint_username": tool_osint_username,
    "osint_social": tool_osint_social,
}

# ═══════════════════════════════════════════════════════════════════════
# MAIN AGENT LOOP
# ═══════════════════════════════════════════════════════════════════════

def check_ollama():
    """Verifică dacă Ollama rulează."""
    try:
        result = ollama_request("tags")
        if "models" in result:
            return True, result["models"]
        return False, str(result)
    except Exception as e:
        return False, str(e)

def print_banner(model, models):
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║     🤖 USB AI AGENT — Agent Portabil pe SSD      ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  Model: {model:<40} ║")
    print(f"║  Modele disponibile: {len(models):<26} ║")
    print(f"║  Ollama: {OLLAMA_HOST:<37} ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  Comenzi speciale:                               ║")
    print("║   /model <nume>  — schimbă modelul               ║")
    print("║   /models        — listează modelele             ║")
    print("║   /memory        — arată memoria                 ║")
    print("║   /clear         — șterge contextul              ║")
    print("║   /save          — salvează conversația          ║")
    print("║   /help          — arată ajutor                  ║")
    print("║   /exit          — închide agentul               ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("Cu ce te pot ajuta?")
    print()

def handle_tool(name, params, memory):
    """Execută un tool și returnează rezultatul."""
    if name in TOOL_MAP:
        print(f"\n  🔧 Execut {name}...", end="", flush=True)
        result = TOOL_MAP[name](params)
        preview = result[:80].replace("\n", " ")
        print(f" ✓ ({preview}...)" if len(result) > 80 else f" ✓ ({preview})")
        return result
    elif name == "remember":
        return tool_remember(params, memory)
    elif name == "recall":
        return tool_recall(params, memory)
    else:
        return f"[Eroare] Instrument necunoscut: {name}"

def main():
    global DEFAULT_MODEL
    
    # Încarcă config
    config = load_config()
    model = config.get("model", DEFAULT_MODEL)
    temperature = config.get("temperature", 0.7)
    memory = load_memory()
    
    # Verifică Ollama
    print("\n🔍 Verific conexiunea la Ollama...", end=" ", flush=True)
    ok, result = check_ollama()
    if not ok:
        print(f"\n❌ Ollama nu rulează! ({result})")
        print(f"   Pornește Ollama mai întâi sau rulează start-agent.bat")
        print(f"   Ollama expected at: {OLLAMA_HOST}")
        sys.exit(1)
    
    available_models = [m["name"] for m in result] if isinstance(result, list) else []
    print(f"✅ Conectat! {len(available_models)} modele găsite.")
    
    # Verifică modelul
    if model not in available_models and available_models:
        # Găsește un model similar
        for am in available_models:
            if model.split(":")[0] in am:
                model = am
                break
        else:
            model = available_models[0]
        config["model"] = model
        save_config(config)
    
    if model not in available_models:
        print(f"\n❌ Modelul '{model}' nu e disponibil!")
        if available_models:
            print(f"   Modele disponibile: {', '.join(available_models)}")
        sys.exit(1)
    
    # Banner
    print_banner(model, available_models)
    
    # Bucla principală
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    while True:
        try:
            user_input = input("\n👤 Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 La revedere!")
            break
        
        if not user_input:
            continue
        
        # Comenzi speciale
        if user_input.startswith("/"):
            cmd_parts = user_input.split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            
            if cmd == "/exit" or cmd == "/quit":
                print("👋 La revedere!")
                break
            elif cmd == "/help":
                print("""
Comenzi disponibile:
  /model <nume>   — schimbă modelul (ex: /model gemma-2-2b)
  /models         — listează toate modelele disponibile
  /memory         — arată ce e salvat în memorie
  /clear          — șterge contextul conversației
  /save           — salvează conversația curentă în chat_data
  /help           — acest mesaj
  /exit           — închide agentul
                """)
                continue
            elif cmd == "/models":
                print("\n📋 Modele disponibile:")
                for m in available_models:
                    marker = " ⬅ (curent)" if m == model else ""
                    print(f"   • {m}{marker}")
                continue
            elif cmd == "/model":
                if len(cmd_parts) > 1:
                    new_model = cmd_parts[1].strip()
                    # Caută modelul
                    found = None
                    for am in available_models:
                        if new_model == am:
                            found = am
                            break
                    if not found:
                        for am in available_models:
                            if new_model in am:
                                found = am
                                break
                    if found:
                        model = found
                        config["model"] = model
                        save_config(config)
                        conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
                        print(f"✅ Model schimbat la: {model}")
                    else:
                        print(f"❌ Modelul '{new_model}' nu a fost găsit.")
                        print(f"   Încearcă /models pentru listă.")
                else:
                    print(f"Model curent: {model}")
                    print("Folosește: /model <nume>")
                continue
            elif cmd == "/memory":
                if memory:
                    print("\n🧠 Memorie agent:")
                    for k, v in memory.items():
                        print(f"   • {k}: {v['value']} ({v['timestamp'][:19]})")
                else:
                    print("\n🧠 Memoria e goală.")
                continue
            elif cmd == "/clear":
                conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
                print("✅ Context șters.")
                continue
            elif cmd == "/save":
                # Salvează conversația în chat_data
                chat_dir = SCRIPT_DIR / "chat_data"
                chat_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                chat_file = chat_dir / f"agent_chat_{timestamp}.json"
                chat_file.write_text(
                    json.dumps(conversation, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"✅ Conversație salvată: {chat_file.name}")
                continue
        
        # Adaugă mesajul utilizatorului
        conversation.append({"role": "user", "content": user_input})
        
        # Trimite la model și procesează tools
        max_tool_iterations = 5
        for iteration in range(max_tool_iterations):
            print(f"\n🤖 {model.split(':')[0]}: ", end="", flush=True)
            
            response = chat_stream(model, conversation, temperature)
            print()  # newline după streaming
            
            if response.startswith("[Eroare"):
                print(response)
                break
            
            # Verifică dacă există un tool call
            tool_name, tool_params, tool_full = parse_tool_call(response)
            
            if tool_name:
                # Execută tool-ul
                tool_result = handle_tool(tool_name, tool_params, memory)
                
                # Adaugă răspunsul modelului și rezultatul tool-ului
                conversation.append({"role": "assistant", "content": response})
                conversation.append({
                    "role": "user",
                    "content": f"[Rezultat instrument {tool_name}]:\n{tool_result}\n\nContinuă pe baza acestui rezultat."
                })
                
                if iteration == max_tool_iterations - 1:
                    print("\n⚠️ Limită de iterații atinsă.")
                # Continuă bucla — modelul va procesa rezultatul
            else:
                # Răspuns normal, afișează și iese din buclă
                conversation.append({"role": "assistant", "content": response})
                break
    
    # Salvează memoria la ieșire
    save_memory(memory)
    print("✅ Memorie salvată.")

if __name__ == "__main__":
    main()
