#!/usr/bin/env bash
# Build a root-path copy and serve it at http://127.0.0.1:8899/.
set -euo pipefail
cd "$(dirname "$0")"

SITE_URL=http://127.0.0.1:8899 BASE_PATH= python3 build.py
echo
echo "Serving http://127.0.0.1:8899/  (Ctrl-C to stop)"
python3 -m http.server 8899 --directory dist
