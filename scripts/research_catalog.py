"""Collect dated public GitHub evidence; never execute repository content."""
import concurrent.futures
import datetime as dt
import json
import subprocess
from pathlib import Path

EXTRA = [
    'openai/plugins', 'openai/skills', 'openai/codex-action',
    'microsoft/playwright-mcp', 'upstash/context7', 'github/github-mcp-server',
    'modelcontextprotocol/servers', 'executeautomation/mcp-playwright',
    'remotion-dev/skills', 'vercel-labs/agent-skills', 'google-labs-code/stitch-skills',
    'jlowin/fastmcp', 'PrefectHQ/fastmcp', 'punkpeye/awesome-mcp-servers',
    'idosal/mcp-ui', 'openai/openai-apps-sdk-examples', 'openai/openai-cookbook',
    'ColeMurray/claude-code-unity', 'CoplayDev/unity-mcp', 'Coding-Solo/godot-mcp',
    'ahujasid/ableton-mcp', 'justasabra/ableton-mcp', 'microsoft/markitdown',
    'n8n-io/n8n', 'czlonkowski/n8n-mcp', 'VoltAgent/awesome-codex-subagents',
    'davila7/claude-code-templates', 'f/awesome-chatgpt-prompts',
    'SOCHI-Co/storage-cleanup', 'SOCHI-Co/skills',
]

def api(path):
    r = subprocess.run(['gh', 'api', path], capture_output=True, encoding='utf-8')
    if r.returncode:
        raise RuntimeError(r.stderr[:250])
    return json.loads(r.stdout)

def collect(repo):
    dest = Path('.research') / (repo.replace('/', '__') + '.json')
    if dest.exists():
        return repo + ' cached'
    result = {'requested': repo, 'observedAt': dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        data = api('repos/' + repo)
        result['metadata'] = {k:data.get(k) for k in ['full_name','html_url','description','archived','disabled','stargazers_count','pushed_at','updated_at','default_branch','license','fork','parent']}
        readme = api('repos/' + data['full_name'] + '/readme')
        import base64
        result['readme'] = base64.b64decode(readme['content']).decode('utf-8', errors='replace')
        result['readmeUrl'] = readme['html_url']
        result['readmeSha'] = readme['sha']
    except Exception as exc:
        result['error'] = str(exc)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return repo + (' ERROR ' + result['error'] if 'error' in result else ' OK')

if __name__ == '__main__':
    Path('.research').mkdir(exist_ok=True)
    existing = [s['repo'].removeprefix('https://github.com/') for s in json.loads(Path('skills.json').read_text())['skills']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(collect, dict.fromkeys(existing + EXTRA)):
            print(result, flush=True)
