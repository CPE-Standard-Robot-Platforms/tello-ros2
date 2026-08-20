#!/bin/bash
# Build the tello-ros2 packages with colcon.
#
# Expects this repository to be checked out as <ros2_ws>/src/tello-ros2 and a
# virtualenv (see scripts/setup_venv.sh) to already be activated, with colcon
# resolving from inside it.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT_DIR="$(dirname "$REPO_ROOT")"

if [ "$(basename "$PARENT_DIR")" != "src" ]; then
    echo "error: expected this repository at <ros2_ws>/src/tello-ros2, found it at $REPO_ROOT" >&2
    exit 1
fi

WORKSPACE_ROOT="$(dirname "$PARENT_DIR")"

if ! command -v colcon >/dev/null 2>&1; then
    echo "error: colcon not found, run scripts/setup_venv.sh and activate the virtualenv first" >&2
    exit 1
fi

cd "$WORKSPACE_ROOT"
colcon build --symlink-install --packages-select tello tello_control tello_msg
