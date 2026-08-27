// Skillshare submission worker.
// Receives {repo, notes, name, code} from the website, verifies the crew
// code, and opens the submission issue on GitHub so visitors never leave
// the page. Secrets (set via `wrangler secret put`):
//   FRIEND_CODE  - shared code the friend group knows
//   GH_TOKEN     - fine-grained PAT, issues:write on Coingyy/skillshare only

const REPO = "Coingyy/skillshare";
const ALLOWED_ORIGINS = new Set([
  "https://coingyy.github.io",
  "http://localhost:8080",
]);
const REPO_URL_RE = /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;

function cors(origin) {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGINS.has(origin) ? origin : "https://coingyy.github.io",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
  };
}

function reply(origin, status, obj) {
  return new Response(JSON.stringify(obj), { status, headers: cors(origin) });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    if (request.method !== "POST") {
      return reply(origin, 405, { ok: false, error: "POST only" });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return reply(origin, 400, { ok: false, error: "Invalid JSON" });
    }

    const code = String(body.code || "").trim();
    const repo = String(body.repo || "").trim().replace(/\/+$/, "");
    const notes = String(body.notes || "").trim().slice(0, 1000);
    const name = String(body.name || "").trim().slice(0, 60);

    if (!env.FRIEND_CODE || code !== env.FRIEND_CODE) {
      return reply(origin, 403, { ok: false, error: "wrong-code" });
    }
    if (!REPO_URL_RE.test(repo)) {
      return reply(origin, 400, { ok: false, error: "bad-repo" });
    }
    if (!name) {
      return reply(origin, 400, { ok: false, error: "no-name" });
    }

    const issueBody =
      `### GitHub repo URL\n\n${repo}\n\n` +
      `### What is it? (rough note is fine)\n\n${notes || "(no note given)"}\n\n` +
      `Submitted by: ${name} (via website)`;

    const res = await fetch(`https://api.github.com/repos/${REPO}/issues`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GH_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "skillshare-submit-worker",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: `Skill submission: ${repo.split("/").slice(-1)[0]}`,
        body: issueBody,
        labels: ["skill-submission"],
      }),
    });

    if (!res.ok) {
      const detail = await res.text();
      console.log("GitHub API error", res.status, detail.slice(0, 300));
      return reply(origin, 502, { ok: false, error: "github-failed" });
    }

    const issue = await res.json();
    return reply(origin, 200, { ok: true, issue: issue.html_url });
  },
};
