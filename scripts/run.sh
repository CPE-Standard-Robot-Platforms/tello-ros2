#!/bin/bash
# Source the workspace install and launch the full tello-ros2 stack.
#
# Expects this repository to be checked out as <ros2_ws>/src/tello-ros2 and
# scripts/build.sh to have already been run.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_ROOT="$(dirname "$(dirname "$REPO_ROOT")")"

# colcon's generated setup.bash references variables such as COLCON_TRACE
# without a default, which trips "set -u". Relax it just for the source.
set +u
# shellcheck disable=SC1091
source "$WORKSPACE_ROOT/install/setup.bash"
set -u

ros2 launch tello tello.launch.py
