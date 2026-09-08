import assert from 'node:assert/strict';
import test from 'node:test';
import worker from '../worker/worker.js';

let serial=0;
async function send(body,respond) {
  const old=globalThis.fetch,requests=[];
  globalThis.fetch=async (url,options={})=>{
    requests.push({url,options});
    const override=respond?.(url,options);
    if (override) return override;
    if (url.includes('/search/issues')) return Response.json({total_count:0});
    if (url.includes('raw.githubusercontent.com')) return Response.json({skills:[]});
    if (options.method==='POST') return Response.json({html_url:'https://github.com/Coingyy/skillshare/issues/999'});
    return Response.json([]);
  };
  try {
    const response=await worker.fetch(new Request('https://worker.example/',{
      method:'POST',headers:{Origin:'https://coingyy.github.io','CF-Connecting-IP':String(++serial),'Content-Type':'application/json'},body:JSON.stringify(body)}),{GH_TOKEN:'test-only'});
    return {response,json:await response.json(),requests};
  } finally {globalThis.fetch=old;}
}
test('legacy and enriched forms create received issues, not publication claims',async()=>{
  for(const body of [{repo:'https://github.com/example/repo',notes:'Legacy form'},
    {repo:'https://github.com/example/repo.git/',platforms:['codex','claude-code'],type:'skill',source:'https://example.com/setup'}]) {
    const r=await send(body);assert.equal(r.response.status,202);assert.equal(r.json.state,'received');
    const issue=JSON.parse(r.requests.find(r=>r.options.method==='POST').options.body);
    assert.match(issue.body,/### GitHub repo URL\n\nhttps:\/\/github.com\/example\/repo\n/);
    assert.deepEqual(issue.labels,['skill-submission']);
  }
});
test('malformed payload, unsafe repo and invalid platform never write GitHub',async()=>{
  for(const body of [null,[],{repo:'https://evil.test/a/b'},
     {repo:'https://github.com/a/b',platforms:['made-up']},
     {repo:'https://github.com/a/b',source:'javascript:alert(1)'}]) {
    const r=await send(body);assert.equal(r.response.status,400);assert.equal(r.requests.length,0);
  }
});
test('duplicate catalog and open issue stop writes',async()=>{
  let r=await send({repo:'https://github.com/example/repo'},url=>url.includes('raw.githubusercontent.com')?Response.json({skills:[{repo:'https://github.com/EXAMPLE/REPO/'}]}):null);
  assert.equal(r.response.status,409);assert.equal(r.json.error,'already-listed');
  r=await send({repo:'https://github.com/example/repo'},url=>url.includes('/issues?labels=')?Response.json([{body:'### GitHub repo URL\n\nhttps://github.com/example/repo'}]):null);
  assert.equal(r.json.error,'already-submitted');assert.ok(!r.requests.some(r=>r.options.method==='POST'));
});
test('daily limit and unavailable quota checks fail closed',async()=>{
  let r=await send({repo:'https://github.com/a/b'},url=>url.includes('/search/issues')?Response.json({total_count:40}):null);
  assert.equal(r.response.status,429);
  r=await send({repo:'https://github.com/a/b'},url=>url.includes('/search/issues')?new Response('unavailable',{status:503}):null);
  assert.equal(r.response.status,503);assert.ok(!r.requests.some(r=>r.options.method==='POST'));
});
test('a repository name prefix is not a duplicate submission',async()=>{
  const r=await send({repo:'https://github.com/example/repo'},url=>url.includes('/issues?labels=')?Response.json([{body:'### GitHub repo URL\n\nhttps://github.com/example/repository'}]):null);
  assert.equal(r.response.status,202);
});
test('GitHub failure is never reported as accepted',async()=>{
  const r=await send({repo:'https://github.com/a/b'},(_url,options)=>options.method==='POST'?new Response('upstream error',{status:500}):null);
  assert.equal(r.response.status,502);assert.equal(r.json.ok,false);
});
