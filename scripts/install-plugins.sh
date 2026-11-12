#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode=monitor
dry=false
for arg in "$@"; do
  case "$arg" in
    --all) mode=all ;;
    --dry-run) dry=true ;;
    --help|-h) echo 'Usage: bash scripts/install-plugins.sh [--all] [--dry-run]'; exit 0 ;;
    *) echo 'Unknown option; use --help.' >&2; exit 2 ;;
  esac
done
plugins="$(python3 - "$root/.claude-plugin/marketplace.json" "$mode" <<'PY'
import json,re,sys
with open(sys.argv[1],encoding='utf-8') as f:data=json.load(f)
names=[p['name'] for p in data['plugins']]
if not names or len(names)!=len(set(names)) or not all(isinstance(n,str) and re.fullmatch(r'[a-z0-9-]+',n) for n in names):
    raise SystemExit('Invalid plugin catalog')
if sys.argv[2]!='all':
    if 'vmware-monitor' not in names:raise SystemExit('Monitor is missing')
    names=['vmware-monitor']
print('\n'.join(names))
PY
)"
if ! "$dry"; then
  command -v claude >/dev/null || { echo 'Install Claude Code before running this helper.' >&2; exit 1; }
  state="$(claude plugin marketplace list --json | python3 -c '
import json,sys
data=json.load(sys.stdin)
if not isinstance(data,list):raise SystemExit("Unexpected marketplace list response")
entries=[x for x in data if isinstance(x,dict) and x.get("name")=="vmware-skills"]
if len(entries)>1:raise SystemExit("Duplicate vmware-skills marketplace names")
if entries and (entries[0].get("source")!="github" or entries[0].get("repo")!="vmware-skills/marketplace"):
    raise SystemExit("Existing vmware-skills marketplace has a different source; review its configuration")
print("present" if entries else "absent")
')"
  if [[ "$state" == absent ]]; then claude plugin marketplace add vmware-skills/marketplace; fi
else
  echo 'claude plugin marketplace add vmware-skills/marketplace'
fi
while IFS= read -r plugin; do
  if "$dry"; then printf 'claude plugin install %s@vmware-skills\n' "$plugin";
  else claude plugin install "$plugin@vmware-skills"; fi
done <<< "$plugins"
