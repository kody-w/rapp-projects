#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
PYTHON=${PYTHON:-python3}
PYTHON=$(command -v "$PYTHON")
BRAINSTEM=${BRAINSTEM_HOME:-"$HOME/.brainstem/src/rapp_brainstem"}
SDK_SOURCE=${RAPP_SDK_SOURCE:-"git+https://github.com/kody-w/rapp-sdk.git@main"}

"$PYTHON" -m pip install "$SDK_SOURCE"
"$PYTHON" -m pip install --no-deps "$ROOT"

mkdir -p "$HOME/.local/bin"
printf '#!/bin/sh\nexec "%s" -m rapp_projects.cli "$@"\n' "$PYTHON" \
  > "$HOME/.local/bin/rapp-projects"
chmod +x "$HOME/.local/bin/rapp-projects"

if [ -d "$BRAINSTEM/agents" ]; then
  cp "$ROOT/agents/rapp_projects_agent.py" "$BRAINSTEM/agents/rapp_projects_agent.py"
  echo "Installed Brainstem adapter: $BRAINSTEM/agents/rapp_projects_agent.py"
fi

echo "Installed RAPP Projects."
echo "Board: $HOME/.rapp/projects-control/BOARD.md"
