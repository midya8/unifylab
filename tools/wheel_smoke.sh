#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cd "$root"
python - "$scratch/expected.json" <<'PY'
import json,sys
from unifylab import solve
from unifylab.subsets import analyze
from unifylab.generalization import generalize
cs=json.load(open('docs/controls.json'))
json.dump([{'input':c['input'],'report':solve(c['input'])} for c in cs],open(sys.argv[1],'w'))
json.dump([{'input':c['input'],'report':analyze(c['input'])} for c in json.load(open('docs/subset-controls.json'))],open(sys.argv[1]+'.subsets','w'))
json.dump([{'input':c['input'],'report':generalize(c['input'])} for c in json.load(open('docs/generalization-controls.json'))],open(sys.argv[1]+'.generalizations','w'))
PY
uv build --wheel --out-dir "$scratch/dist"
uv venv "$scratch/env"
uv pip install --python "$scratch/env/bin/python" "$scratch"/dist/*.whl
cp tools/verify_installed.py "$scratch/verify_installed.py"
cd "$scratch"
PATH="$scratch/env/bin:$PATH" PYTHONPATH= "$scratch/env/bin/python" verify_installed.py "$root" expected.json
