"""Check installer delegation without changing the host's Claude configuration."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAMES = [p['name'] for p in json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())['plugins']]
with tempfile.TemporaryDirectory() as work:
    temp = Path(work)
    fake = temp / 'claude'
    fake.write_text('''#!/usr/bin/env python3
import json,os,sys
args=sys.argv[1:]
if args==['plugin','marketplace','list','--json']:
 print(os.environ['FAKE_MARKETPLACES']);sys.exit(0)
with open(os.environ['FAKE_LOG'],'a') as f:f.write(json.dumps(args)+'\\n')
if os.environ.get('FAKE_FAIL') and args==['plugin','install',os.environ['FAKE_FAIL']]:sys.exit(7)
''')
    fake.chmod(0o755)
    log = temp / 'calls'
    env = dict(os.environ, PATH=str(temp) + os.pathsep + os.environ['PATH'], FAKE_LOG=str(log))
    def run(markets, *args, fail=''):
        log.write_text('')
        result = subprocess.run(['bash', str(ROOT / 'scripts/install-plugins.sh'), *args], env=dict(env, FAKE_MARKETPLACES=json.dumps(markets), FAKE_FAIL=fail), capture_output=True, text=True)
        return result.returncode, [json.loads(x) for x in log.read_text().splitlines()]
    present = [{'name': 'vmware-skills', 'source': 'github', 'repo': 'vmware-skills/marketplace'}]
    rc, calls = run(present, '--all')
    assert rc == 0 and calls == [['plugin', 'install', n + '@vmware-skills'] for n in NAMES]
    rc, calls = run([])
    assert rc == 0 and calls == [['plugin', 'marketplace', 'add', 'vmware-skills/marketplace'], ['plugin', 'install', 'vmware-monitor@vmware-skills']]
    rc, calls = run([{'name': 'vmware-skills', 'source': 'github', 'repo': 'other/repository'}], '--all')
    assert rc != 0 and calls == []
    rc, calls = run(present, '--all', fail=NAMES[0] + '@vmware-skills')
    assert rc == 7 and len(calls) == 1
    rc, calls = run(present, '--invalid')
    assert rc == 2 and calls == []
print('5 installer integration scenarios passed; no host installation performed')
