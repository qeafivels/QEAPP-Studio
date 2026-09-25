#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHONPATH="$PWD" python3 -m unittest discover -s studio/tests -v
PYTHONPATH="$PWD" python3 -m unittest discover -s tests -v
