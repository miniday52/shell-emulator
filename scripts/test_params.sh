#!/bin/sh
# Stage 2: test all supported command line options.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/src"
PY=python3

echo "===== 1. help ====="
$PY -m emulator --help

echo "===== 2. no options (stdin is empty) ====="
$PY -m emulator < /dev/null

echo "===== 3. --script only ====="
$PY -m emulator --script "$ROOT/examples/scripts/stage2.txt"

echo "===== 4. --vfs and --script ====="
$PY -m emulator --vfs "$ROOT/examples/vfs/deep.xml" \
    --script "$ROOT/examples/scripts/stage2.txt"

echo "===== 5. missing script file ====="
$PY -m emulator --script "$ROOT/examples/scripts/missing.txt"
echo "exit code: $?"

echo "===== 6. unknown option ====="
$PY -m emulator --bad-option
echo "exit code: $?"
