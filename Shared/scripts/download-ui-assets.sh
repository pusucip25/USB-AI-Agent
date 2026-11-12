#!/bin/bash
# Download optional third-party UI assets used by the offline chat UI.
#
# Called by Linux/install.sh as:  bash download-ui-assets.sh <vendor_dir>
# Everything here is optional - a failure only means the UI falls back to
# the online/CDN copy of that asset, so this script never fails the install.
#
# Usage: bash download-ui-assets.sh /path/to/Shared/vendor

VENDOR_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)/vendor}"
mkdir -p "$VENDOR_DIR" || exit 0

fetch() {
    local url="$1" out="$2"
    if [ -s "$VENDOR_DIR/$out" ]; then
        echo "      [ok] $out already present"
        return 0
    fi
    if command -v curl >/dev/null 2>&1; then
        curl -sL --fail --max-time 120 "$url" -o "$VENDOR_DIR/$out" || { rm -f "$VENDOR_DIR/$out"; return 1; }
    elif command -v wget >/dev/null 2>&1; then
        wget -q -T 120 "$url" -O "$VENDOR_DIR/$out" || { rm -f "$VENDOR_DIR/$out"; return 1; }
    else
        echo "      [skip] no curl/wget available"
        return 1
    fi
    if [ -s "$VENDOR_DIR/$out" ]; then
        echo "      [ok] $out"
        return 0
    fi
    return 1
}

FAILED=0

# Markdown renderer (used by the chat UI if the CDN copy is unreachable)
fetch "https://unpkg.com/marked@12.0.2/marked.min.js" "marked.min.js" || FAILED=$((FAILED + 1))

# HTML sanitiser for rendered markdown
fetch "https://unpkg.com/dompurify@3.1.6/dist/purify.min.js" "purify.min.js" || FAILED=$((FAILED + 1))

if [ "$FAILED" -gt 0 ]; then
    echo "      [warn] $FAILED optional asset(s) could not be downloaded - the UI still works online."
fi
exit 0
