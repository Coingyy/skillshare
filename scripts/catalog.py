"""Shared catalog validation and conservative legacy migration."""
import copy
import json
import re
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ('claude-code', 'codex', 'chatgpt')
REPO_RE = re.compile(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?\Z')

def canonical_repo(url):
    if not isinstance(url, str) or not REPO_RE.fullmatch(url):
        raise ValueError('Expected a public GitHub repository URL')
    return url.rstrip('/').removesuffix('.git').lower()

def unknown_platform():
    return {'status': 'unverified', 'instructions': 'No platform-specific setup verified. Consult the provider documentation before installing.',
            'prerequisites': [], 'sources': []}

def normalize_legacy(entry):
    """Old submissions still work. Never turn old Verified into compatibility evidence."""
    entry = copy.deepcopy(entry)
    entry.setdefault('type', 'tool')
    entry.setdefault('platforms', {p: unknown_platform() for p in PLATFORMS})
    entry.setdefault('sources', [])
    entry.setdefault('security', {'status': 'legacy' if entry.get('status') == 'verified' else 'unverified',
                                  'notes': 'Historical label only; no dated scan evidence attached.'})
    entry.setdefault('aiReview', {'status': 'not-reviewed', 'summary': 'No recorded AI review.'})
    entry.setdefault('review', {'status': 'unverified', 'notes': 'Legacy submission; repository metadata needs review.'})
    return entry

def validate(data):
    schema = json.loads((ROOT/'schema/skills.schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(data)
    ids, repos = set(), set()
    for s in data['skills']:
        if s['id'] in ids: raise ValueError('Duplicate id: '+s['id'])
        repo = canonical_repo(s['repo'])
        if repo in repos: raise ValueError('Duplicate repository: '+repo)
        ids.add(s['id']); repos.add(repo)
        sources = {x['url'] for x in s['sources']}
        for platform, support in s['platforms'].items():
            if not set(support['sources']).issubset(sources):
                raise ValueError(f'{s["id"]}/{platform}: source missing from entry')
            if support['status'] != 'unverified' and not support['sources']:
                raise ValueError('Documented/tested support requires sources')
        if s['status'] == 'verified' and s['security']['status'] not in ('passed', 'warnings', 'legacy'):
            raise ValueError('Verified legacy field contradicts scan result')
        scan=s['security']
        if scan['status'] in ('passed','warnings') and scan['high']!=0:
            raise ValueError('Accepted scan cannot contain HIGH findings')
        if scan['status']=='passed' and scan['warnings']!=0:
            raise ValueError('Passed scan cannot contain warnings')
        if scan['status']=='warnings' and scan['warnings']<1:
            raise ValueError('Warnings status requires warning evidence')
    return data

if __name__ == '__main__':
    import sys
    data=json.loads(Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'skills.json').read_text(encoding='utf-8'))
    validate(data)
    print(f'Catalog valid: {len(data["skills"])} entries')
