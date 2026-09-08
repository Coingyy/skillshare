"""AI review with no tools, bounded input, strict output, and no fail-open path."""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
import jsonschema
from catalog import PLATFORMS, ROOT, unknown_platform

MODEL = 'gpt-5.4-mini-2026-03-17'
MAX_INPUT_BYTES = 100_000
MAX_OUTPUT_TOKENS = 5000

def object_schema(properties):
    return {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties)}

def review_schema():
    catalog = json.loads((ROOT/'schema/skills.schema.json').read_text())['properties']['skills']['items']['properties']
    text = {'type':'string'}
    support = object_schema({'platform':{'enum':list(PLATFORMS)},'status':{'enum':['documented','unverified']},
        'source':text,'quote':text,'installationQuote':text,'instructions':text,'prerequisites':{'type':'array','items':text}})
    warning = object_schema({'index':{'type':'integer'},'assessment':text,'acceptable':{'type':'boolean'}})
    return object_schema({'decision':{'enum':['approve','review','reject']},'reason':text,
        'proposedEntryAcceptable':{'type':'boolean'},
        'name':text,'tagline':text,'description':text,'category':{'enum':catalog['category']['enum']},
        'type':{'enum':catalog['type']['enum']},'tags':{'type':'array','items':text},
        'platforms':{'type':'array','items':support},'warnings':{'type':'array','items':warning}})

def make_payload(evidence):
    prompt = (ROOT/'scripts/review_prompt.txt').read_text(encoding='utf-8')
    raw=json.dumps(evidence,ensure_ascii=False)
    if len(raw.encode('utf-8')) > MAX_INPUT_BYTES:
        raise ValueError('Review evidence exceeds the input limit; manual review required')
    return {'model':MODEL,'store':False,'instructions':prompt,'input':raw,
        'max_output_tokens':MAX_OUTPUT_TOKENS,'reasoning':{'effort':'low'},
        'text':{'format':{'type':'json_schema','name':'submission_review','strict':True,'schema':review_schema()}}}

def parse_response(response):
    if response.get('status') != 'completed':
        raise ValueError('AI review incomplete or refused; no entry accepted')
    content=[]
    for item in response.get('output',[]):
        for part in item.get('content',[]):
            if part.get('type')=='refusal': raise ValueError('AI review refused')
            if part.get('type')=='output_text': content.append(part['text'])
    if not content: raise ValueError('AI returned no review')
    result=json.loads(''.join(content))
    jsonschema.validate(result,review_schema())
    return result

def call_ai(evidence):
    key=os.environ.get('OPENAI_API_KEY')
    if not key: raise RuntimeError('OPENAI_API_KEY is missing; AI review is required and cannot be bypassed')
    request=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(make_payload(evidence)).encode(),
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    # One call only. No automatic retry on uncertain/time-out responses that could be billable.
    try:
        with urllib.request.urlopen(request,timeout=180) as response: result=json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'OpenAI review unavailable (HTTP {exc.code}); retry through the workflow after resolving access, credit or rate limits') from None
    review=parse_response(result)
    return review, result.get('usage',{})

def validate_review(review,evidence):
    jsonschema.validate(review,review_schema())
    if review['decision']!='approve': raise ValueError('AI requires review or rejects this submission: '+review['reason'][:400])
    if 'proposedEntry' in evidence and not review['proposedEntryAcceptable']:
        raise ValueError('AI did not approve the proposed PR content')
    if any(f[0]=='HIGH' for f in evidence['scan']['findings']): raise ValueError('HIGH findings cannot be overridden by AI')
    expected={i for i,f in enumerate(evidence['scan']['findings']) if f[0]=='WARN'}
    warnings=review['warnings']
    if len(warnings)!=len(expected) or {w['index'] for w in warnings}!=expected or not all(w['acceptable'] and w['assessment'].strip() for w in warnings):
        raise ValueError('Every warning requires a distinct, acceptable AI assessment')
    supports=review['platforms']
    if len(supports)!=3 or {s['platform'] for s in supports}!=set(PLATFORMS):
        raise ValueError('AI must assess all three platforms exactly once')
    docs={}
    for d in evidence['documents']:
        docs[d['url']]=docs.get(d['url'],'')+'\n'+d['text']
    platforms={p:unknown_platform() for p in PLATFORMS}
    aliases={'claude-code':['claude code','claude-code'],'codex':['codex'],'chatgpt':['chatgpt']}
    for s in supports:
        if s['status']=='unverified': continue
        text=docs.get(s['source'],'')
        if len(s['quote'])<15 or s['quote'] not in text or not any(a in s['quote'].lower() for a in aliases[s['platform']]):
            raise ValueError('Platform evidence must quote fetched provider documentation naming the host')
        if len(s['installationQuote'])<15 or s['installationQuote'] not in text:
            raise ValueError('Documented support needs an exact installation excerpt')
        platforms[s['platform']]={'status':'documented','instructions':s['instructions'],
             'prerequisites':s['prerequisites'],'sources':[s['source']]}
    return platforms
