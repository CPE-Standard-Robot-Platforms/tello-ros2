#!/bin/bash
# Create (or update) a virtualenv with everything tello-ros2 needs on top of a
# system ROS 2 Jazzy install, including colcon itself.
#
# Usage:
#   ./scripts/setup_venv.sh [venv_path]
#
# venv_path defaults to ".venv" at the repository root. Activate it afterwards
# with "source <venv_path>/bin/activate" before running colcon build or ros2 run.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${1:-$REPO_ROOT/.venv}"

if [ ! -d "$VENV_PATH" ]; then
    echo " - Creating virtualenv at $VENV_PATH"
    python3 -m venv "$VENV_PATH"
fi

# shellcheck disable=SC1091
source "$VENV_PATH/bin/activate"

echo " - Installing Python dependencies"
pip install --upgrade pip
pip install -r "$REPO_ROOT/requirements.txt"

echo " - Virtualenv ready: $VENV_PATH"
echo " - Activate it with: source $VENV_PATH/bin/activate"
echo " - colcon now resolves to: $(command -v colcon)"
