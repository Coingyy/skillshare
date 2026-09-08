"""Only report published when the deployed catalog actually contains the repo."""
import json
import os
import time
import urllib.request
from process_submission import api, comment, parse_submission, REPOSITORY
from catalog import canonical_repo

def confirm(site_url,expected,notify=True):
    with urllib.request.urlopen(site_url.rstrip('/')+'/skills.json?v='+str(time.time_ns()),timeout=30) as res:
        live=json.load(res)
    # A deploy success alone is insufficient: verify the artifact's full catalog.
    if live!=expected: raise RuntimeError('Website catalog does not match the deployed artifact yet')
    if not notify: return
    listed={canonical_repo(s['repo']) for s in live['skills']}
    page=1
    pending=[]
    while True:
        issues=api(f'repos/{REPOSITORY}/issues?labels=skill-submission&state=open&per_page=100&page={page}')
        pending.extend(issues)
        if len(issues)<100: break
        page+=1
    # Read all pages before closing issues, otherwise pagination skips entries.
    for item in pending:
        if 'pull_request' in item: continue
        try: repo=canonical_repo(parse_submission(item.get('body') or '')['repo'])
        except ValueError: continue
        if repo not in listed: continue
        comment(item['number'],'published',f'Confirmed in the deployed catalog: {site_url}. Scanner and AI review are separate from tested platform compatibility.')
        api(f'repos/{REPOSITORY}/issues/{item["number"]}','PATCH',{'state':'closed','state_reason':'completed'})

if __name__=='__main__':
    from pathlib import Path
    expected=json.loads(Path('skills.json').read_text())
    last=None
    for attempt in range(6):
        try: confirm(os.environ['SITE_URL'],expected,notify=os.environ.get('NOTIFY_SUBMITTERS')=='true');break
        except (OSError,RuntimeError) as exc:
            last=exc
            if attempt==5: raise
            time.sleep(10)
