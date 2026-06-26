#!/usr/bin/env bash
# Atualiza o repositório descartando alterações locais conflitantes.
set -euo pipefail
cd "$(dirname "$0")/.."
git fetch origin main
git reset --hard origin/main
echo "Atualizado para: $(git log -1 --oneline)"
pip install -r requirements.txt
PYTHONPATH=. python3 -m pytest tests/ -v
