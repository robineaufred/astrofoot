#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -d ve ] || { python3 -m venv ve && ve/bin/pip install -q -r requirements.txt; }
exec ve/bin/uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
