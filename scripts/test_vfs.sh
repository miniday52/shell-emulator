#!/bin/sh
# Stage 3: run the emulator with different VFS variants.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/src"
VFS="$ROOT/examples/vfs"
SCRIPT="$ROOT/examples/scripts/stage3.txt"
PY=python3

echo "===== default in-memory VFS ====="
$PY -m emulator --script "$SCRIPT"

for name in minimal several_files deep; do
    echo "===== $name.xml ====="
    $PY -m emulator --vfs "$VFS/$name.xml" --script "$SCRIPT"
done

for name in missing broken bad_base64; do
    echo "===== error: $name.xml ====="
    $PY -m emulator --vfs "$VFS/$name.xml" --script "$SCRIPT"
    echo "exit code: $?"
done
