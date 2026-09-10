#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
exec python3 gemini_web2api.py --config config/config.json "$@"