"""Trusted submission pipeline. Repositories and AI output are data, never code."""
import argparse
import base64
import copy
import datetime as dt
import json
import os
import re
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from catalog import canonical_repo, validate
from security_scan import scan_repo
from review_submission import MODEL, call_ai, validate_review

REPOSITORY=os.environ.get('GITHUB_REPOSITORY','Coingyy/skillshare')
MAX_DAILY_RUNS=10
MAX_RUN_ATTEMPTS=1

def check_budget():
    # Count both billable entry points. Reruns are separately bounded below.
    total=0
    for workflow in ('process-submission.yml','security-check.yml'):
        runs=api(f'repos/{REPOSITORY}/actions/workflows/{workflow}/runs?created={now()[:10]}&per_page=1')
        total+=runs['total_count']
    if total>MAX_DAILY_RUNS or int(os.environ.get('GITHUB_RUN_ATTEMPT','1'))>MAX_RUN_ATTEMPTS:
        raise RuntimeError('Daily processing/attempt limit reached; retry later')

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()

def api(path,method='GET',body=None):
    req=urllib.request.Request('https://api.github.com/'+path,
        data=None if body is None else json.dumps(body).encode(),method=method,
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json',
                 'Content-Type':'application/json','User-Agent':'skillshare-review'})
    with urllib.request.urlopen(req,timeout=40) as res:
        raw=res.read()
        return json.loads(raw) if raw else None

def comment(issue,state,message):
    return api(f'repos/{REPOSITORY}/issues/{issue}/comments','POST',
       {'body':f'<!-- skillshare-state:{state} -->\n**{state.replace("-"," ").capitalize()}**\n\n{message}'})

def parse_submission(body):
    sections={}
    for m in re.finditer(r'^### ([^\r\n]+)\r?\n+([\s\S]*?)(?=^### |\Z)',body,re.M):
        sections.setdefault(m[1].strip(),m[2].strip())
    if 'GitHub repo URL' in sections:
        repo=sections['GitHub repo URL'].splitlines()[0].strip() if sections['GitHub repo URL'] else ''
    else:
        links=re.findall(r'https://github\.com/[^\s<>]+',body)
        repo=links[0] if len(links)==1 else ''
    canonical_repo(repo)
    return {'repo':repo.rstrip('/').removesuffix('.git'),
            'suggestions':{k:v[:1000] for k,v in sections.items() if k!='GitHub repo URL'}}

def read_main():
    item=api(f'repos/{REPOSITORY}/contents/skills.json?ref=main')
    return json.loads(base64.b64decode(item['content']))

def collect(repo):
    canonical_repo(repo)
    metadata=api('repos/'+repo.split('github.com/')[1])
    if metadata['archived'] or metadata.get('disabled'):
        raise ValueError('Repository is archived or disabled; maintainer review required')
    name=metadata['full_name'];repo=metadata['html_url']
    revision=api('repos/'+name+'/commits/'+urllib.parse.quote(metadata['default_branch'],safe=''))['sha']
    scan={};texts=[]
    findings=scan_repo(repo,revision=revision,evidence=scan,review_text=texts)
    scan['findings']=findings
    scan['result']='blocked' if any(f[0]=='HIGH' for f in findings) else ('warnings' if findings else 'passed')
    if scan['result']!='blocked' and not scan.get('filesScanned'):
        raise ValueError('No readable source text was scanned; maintainer review required')
    docs=[];used=0
    texts.sort(key=lambda x: ('finding' not in x, x['path'].lower()!='readme.md',x['path']))
    for item in texts:
        length=len(item['text'].encode('utf-8'))
        if used+length>65000: continue
        used+=length
        docs.append({'url':f'https://github.com/{name}/blob/{revision}/'+urllib.parse.quote(item['path'],safe='/'),**item})
    return {'repo':repo,'observedAt':now(),'metadata':{k:metadata.get(k) for k in ['full_name','description','stargazers_count','pushed_at','archived']},
        'scan':scan,'documents':docs,'reviewCoverage':{'selectedExcerpts':len(docs),'availableExcerpts':len(texts),
        'note':'Bounded documentary review, not execution or a complete dependency audit.'}}

def build_entry(review,evidence,report_url,ids):
    platforms=validate_review(review,evidence)
    repo=evidence['repo'];base=re.sub('[^a-z0-9-]+','-',repo.rsplit('/',1)[1].lower()).strip('-') or 'offering'
    slug=base;counter=2
    while slug in ids: slug=f'{base}-{counter}';counter+=1
    entry={k:review[k] for k in ['name','tagline','description','category','type','tags']}
    scan=evidence['scan'];stamp=now();date=stamp[:10]
    sources=[{'url':d['url'],'title':('Provider '+d['path'])[:150],'checkedAt':date} for d in evidence['documents']
             if any(d['url'] in p['sources'] for p in platforms.values())]
    sources=list({s['url']:s for s in sources}.values())
    sources += [{'url':repo,'title':'Provider repository','checkedAt':date},
                {'url':'https://api.github.com/repos/'+evidence['metadata']['full_name'],'title':'GitHub metadata','checkedAt':date}]
    entry.update(id=slug,repo=repo,addedAt=date,submittedBy='anonymous',status='verified',platforms=platforms,sources=sources,
       review={'status':'active','checkedAt':date,'canonicalRepo':repo,'pushedAt':evidence['metadata']['pushed_at'],
          'notes':'Repository documentation reviewed by AI. No functional platform tests performed.'},
       popularity={'stars':evidence['metadata']['stargazers_count'],'observedAt':evidence['observedAt'],
          'source':'https://api.github.com/repos/'+evidence['metadata']['full_name']},
       security={'status':scan['result'],'checkedAt':scan['checkedAt'],'revision':scan['revision'],'high':0,
          'warnings':len(scan['findings']),'report':report_url,'notes':'Static text scan. Dependencies and runtime behavior are not tested.'},
       aiReview={'status':'approved','model':MODEL,'checkedAt':stamp,'report':report_url,'summary':review['reason'][:2000]})
    return entry

def ensure_append_only(before,after,expected_repo):
    validate(after)
    if len(after['skills'])!=len(before['skills'])+1 or after['skills'][:-1]!=before['skills']:
        raise ValueError('Must append one entry; existing entries may not change')
    if {k:v for k,v in before.items() if k not in ('skills','updated')}!={k:v for k,v in after.items() if k not in ('skills','updated')}:
        raise ValueError('Top-level settings may not change')
    if canonical_repo(after['skills'][-1]['repo'])!=canonical_repo(expected_repo):
        raise ValueError('Submitted repository changed')

def publish_entry(issue,review,evidence,report):
    run=uuid.uuid4().hex[:12]
    # Reassemble on conflict without repeating the billable AI call.
    for attempt in range(3):
        branch=f'codex/submission-{issue}-{run}-{attempt}'
        main=api(f'repos/{REPOSITORY}/git/ref/heads/main')['object']['sha']
        item=api(f'repos/{REPOSITORY}/contents/skills.json?ref='+main)
        before=json.loads(base64.b64decode(item['content']));blob=item['sha']
        if any(canonical_repo(s['repo'])==canonical_repo(evidence['repo']) for s in before['skills']): return 'already-listed'
        after=copy.deepcopy(before)
        entry=build_entry(review,evidence,report,{s['id'] for s in before['skills']})
        after['skills'].append(entry);after['updated']=now()[:10]
        ensure_append_only(before,after,evidence['repo'])
        # Never reset an existing branch: a maintainer may have edited it.
        api(f'repos/{REPOSITORY}/git/refs','POST',{'ref':'refs/heads/'+branch,'sha':main})
        created=api(f'repos/{REPOSITORY}/contents/skills.json','PUT',{'branch':branch,'sha':blob,
            'message':'Add offering: '+entry['name'],
            'content':base64.b64encode((json.dumps(after,indent=2,ensure_ascii=False)+'\n').encode()).decode()})
        head=created['commit']['sha']
        prs=api(f'repos/{REPOSITORY}/pulls?head='+urllib.parse.quote(REPOSITORY.split('/')[0]+':'+branch,safe=''))
        pr=prs[0] if prs else api(f'repos/{REPOSITORY}/pulls','POST',{'title':'Add offering: '+entry['name'],'head':branch,'base':'main',
          'body':f'Related submission #{issue}. Scanner and OpenAI review: {report}\n\nPublication is confirmed separately after Pages deployment.'})
        actual=api(f'repos/{REPOSITORY}/contents/skills.json?ref='+head)
        ensure_append_only(before,json.loads(base64.b64decode(actual['content'])),evidence['repo'])
        files=api(f'repos/{REPOSITORY}/pulls/{pr["number"]}/files')
        if [f['filename'] for f in files]!=['skills.json']: raise ValueError('Unexpected PR file change')
        api(f'repos/{REPOSITORY}/statuses/{head}','POST',{'state':'success','context':'scan',
             'description':'Entry validated; static scan and OpenAI review completed','target_url':report})
        try:
            merged=api(f'repos/{REPOSITORY}/pulls/{pr["number"]}/merge','PUT',{'sha':head,'merge_method':'squash'})
            if merged.get('merged'): return pr['html_url']
        except urllib.error.HTTPError as exc:
            # Only a changed main branch merits rebuilding. Protection/setup
            # failures need maintainer action, not more duplicate pull requests.
            latest=api(f'repos/{REPOSITORY}/git/ref/heads/main')['object']['sha']
            if exc.code not in (405,409,422) or latest==main: raise
    raise RuntimeError('Merge failed after three attempts; maintainer action required')

def process(issue):
    item=api(f'repos/{REPOSITORY}/issues/{issue}')
    if 'pull_request' in item or 'skill-submission' not in [x['name'] for x in item['labels']]:
        raise ValueError('Expected an issue labeled skill-submission')
    if item['state']!='open': return
    submission=parse_submission(item.get('body') or '')
    if any(canonical_repo(s['repo'])==canonical_repo(submission['repo']) for s in read_main()['skills']):
        comment(issue,'merged','Already in the main catalog. Website publication is checked by the deployment workflow.');return
    check_budget()
    comment(issue,'scanning','Received. Scanner and AI review must both finish before acceptance. Not published yet.')
    evidence=collect(submission['repo']);evidence['suggestions']=submission['suggestions']
    Path('submission-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    scan=evidence['scan']
    if scan['result']=='blocked': raise ValueError('HIGH findings block acceptance. See workflow evidence; AI cannot override them')
    comment(issue,'ai-review',f'Scanned commit `{scan["revision"]}`: {len(scan["findings"])} warning(s), no HIGH findings. AI review is pending; no compatibility test was run.')
    review,usage=call_ai(evidence)
    Path('submission-review.json').write_text(json.dumps({'model':MODEL,'usage':usage,'review':review},indent=2),encoding='utf-8')
    validate_review(review,evidence)
    text=json.dumps({'scan':scan,'model':MODEL,'usage':usage,'review':review},indent=2)
    report=comment(issue,'reviewed','Scanner and AI review completed. No safety guarantee or tested compatibility.\n\n<details><summary>Review evidence</summary>\n\n```json\n'+text[:45000].replace('```','~~~')+'\n```\n</details>\n\nFull reports: workflow artifacts.')['html_url']
    result=publish_entry(issue,review,evidence,report)
    comment(issue,'merged',f'Entry is in main ({result}). Website deployment is pending; not yet a published notification.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--issue',type=int,required=True);args=parser.parse_args()
    if args.issue<1: parser.error('Positive issue number required')
    try: process(args.issue)
    except Exception as exc:
        message=str(exc)[:600]
        print('Submission not completed: '+message,file=sys.stderr)
        try: comment(args.issue,'needs-attention',message+'\n\nPublication is not confirmed. The issue remains open. Fix the cause, then use Run workflow with this issue number.')
        except Exception: pass
        sys.exit(1)
