"""Run the existing rule set on research candidates; no installs or executions."""
import concurrent.futures
import json
from pathlib import Path
from security_scan import scan_repo

CANDIDATES = ['openai/plugins', 'microsoft/playwright-mcp', 'upstash/context7',
 'github/github-mcp-server', 'vercel-labs/agent-skills', 'google-labs-code/stitch-skills',
 'CoplayDev/unity-mcp', 'Coding-Solo/godot-mcp', 'ahujasid/ableton-mcp',
 'microsoft/markitdown', 'czlonkowski/n8n-mcp', 'VoltAgent/awesome-codex-subagents',
 'PrefectHQ/fastmcp', 'openai/openai-apps-sdk-examples', 'f/prompts.chat',
 'SOCHI-Co/storage-cleanup', 'SOCHI-Co/skills']

def scan(repo):
    dest=Path('.research')/(repo.replace('/','__')+'.scan.json')
    if dest.exists(): return repo+' cached'
    evidence={'repo':'https://github.com/'+repo}
    try:
        findings=scan_repo(evidence['repo'],evidence=evidence)
        evidence['findings']=findings
        evidence['result']='blocked' if any(f[0]=='HIGH' for f in findings) else ('warnings' if findings else 'passed')
    except Exception as exc:
        evidence.update(result='error',error=str(exc))
    dest.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    return repo+' '+evidence['result']+' '+str(len(evidence.get('findings',[])))

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(scan,CANDIDATES): print(result,flush=True)
