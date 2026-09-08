"""Review PR data using trusted base-branch code; never execute PR content."""
import json
import os
import subprocess
from pathlib import Path
from catalog import normalize_legacy, validate
from process_submission import collect, check_budget
from review_submission import call_ai, validate_review

def check(before,after):
    normalized={**after,'schemaVersion':2,'skills':[normalize_legacy(s) for s in after['skills']]}
    validate(normalized)
    Path('normalized-catalog.json').write_text(json.dumps(normalized,indent=2)+'\n')
    # Existing issue submissions migrate automatically; direct PR authors receive a repair artifact.
    if normalized!=after:
        raise ValueError('Legacy PR entry: use normalized-catalog.json artifact to add explicit unverified metadata, or submit the repo URL through the website for full AI enrichment')
    previous={s['id']:s for s in before['skills']}
    changed=[s for s in after['skills'] if previous.get(s['id'])!=s]
    if len(changed)>1:
        raise ValueError('Automatic AI review accepts one changed entry per PR to bound costs. Split submissions; catalog-wide migrations need maintainer review.')
    if changed: check_budget()
    for s in changed:
        prior=previous.get(s['id'],{})
        if prior.get('repo')!=s['repo']: prior={}
        for field,unknown in (('security','unverified'),('aiReview','not-reviewed')):
            if s[field]!=prior.get(field) and s[field]['status']!=unknown:
                raise ValueError('New scan/AI attestations must come from the submission pipeline, not PR-authored claims: '+field)
        evidence=collect(s['repo'])
        # Review the actual PR's prose/commands as well as the upstream repo.
        # Otherwise an attacker could attach malicious instructions to a benign repo.
        evidence['proposedEntry']=s
        if evidence['scan']['result']=='blocked':
            Path('pr-review.json').write_text(json.dumps(evidence,indent=2))
            raise ValueError('HIGH findings in '+s['repo'])
        review,usage=call_ai(evidence)
        platforms=validate_review(review,evidence)
        Path('pr-review.json').write_text(json.dumps({'evidence':evidence,'review':review,'usage':usage},indent=2))
        for platform,support in s['platforms'].items():
            if support['status']=='documented' and platforms[platform]['status']=='unverified':
                raise ValueError('PR claims unsupported compatibility: '+s['id']+'/'+platform)
            if support['status']=='tested' and (not previous.get(s['id']) or support!=previous[s['id']].get('platforms',{}).get(platform)):
                raise ValueError('New self-tested claim requires a maintainer to inspect test evidence; AI cannot attest it')
    print(f'Validated catalog and reviewed {len(changed)} changed entries')

if __name__=='__main__':
    before=json.loads(Path('skills.json').read_text())
    head=os.environ['PR_HEAD_SHA']
    if len(head)!=40 or any(c not in '0123456789abcdef' for c in head): raise ValueError('Invalid PR SHA')
    subprocess.run(['git','fetch','--no-tags','origin',head],check=True)
    result=subprocess.run(['git','show',head+':skills.json'],check=True,capture_output=True,text=True,encoding='utf-8')
    check(before,json.loads(result.stdout))
