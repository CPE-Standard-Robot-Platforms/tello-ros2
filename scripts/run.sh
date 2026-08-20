#!/bin/bash
# Source the workspace install and launch the full tello-ros2 stack.
#
# Expects this repository to be checked out as <ros2_ws>/src/tello-ros2 and
# scripts/build.sh to have already been run.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_ROOT="$(dirname "$(dirname "$REPO_ROOT")")"

# shellcheck disable=SC1091
source "$WORKSPACE_ROOT/install/setup.bash"

ros2 launch tello tello.launch.py
