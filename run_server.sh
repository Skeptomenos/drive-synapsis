#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/src"
exec "${SCRIPT_DIR}/.venv/bin/python" -m drive_synapsis.server "$@"
