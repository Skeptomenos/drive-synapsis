#!/bin/bash
export PYTHONPATH="/Users/davidhelmus/Repos/drive-synapsis/src"
exec /Users/davidhelmus/Repos/drive-synapsis/.venv/bin/python -m drive_synapsis.main_server "$@" 2>/tmp/drive-synapsis-error.log
