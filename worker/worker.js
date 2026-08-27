// Skillshare submission worker.
// Receives {repo, notes} from the website and opens the submission issue on
// GitHub, so visitors never leave the page. Submissions are anonymous.
// Spam protection: per-IP rate limit and duplicate rejection.
// Secret (set via `wrangler secret put`):
//   GH_TOKEN - fine-grained PAT, issues:write on Coingyy/skillshare only

const REPO = "Coingyy/skillshare";
const ALLOWED_ORIGINS = new Set([
  "https://coingyy.github.io",
  "http://localhost:8080",
]);
const REPO_URL_RE = /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;

const RATE_LIMIT = 5;            // submissions...
const RATE_WINDOW_MS = 3600_000; // ...per hour per IP
const ipHits = new Map();        // per-isolate; resets on cold start, good enough

function rateLimited(ip) {
  const now = Date.now();
  const hits = (ipHits.get(ip) || []).filter((t) => now - t < RATE_WINDOW_MS);
  if (hits.length >= RATE_LIMIT) return true;
  hits.push(now);
  ipHits.set(ip, hits);
  return false;
}

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

    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    if (rateLimited(ip)) {
      return reply(origin, 429, { ok: false, error: "rate-limited" });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return reply(origin, 400, { ok: false, error: "Invalid JSON" });
    }

    const repo = String(body.repo || "").trim().replace(/\/+$/, "");
    const notes = String(body.notes || "").trim().slice(0, 1000);

    if (!REPO_URL_RE.test(repo)) {
      return reply(origin, 400, { ok: false, error: "bad-repo" });
    }

    const gh = {
      "Authorization": `Bearer ${env.GH_TOKEN}`,
      "Accept": "application/vnd.github+json",
      "User-Agent": "skillshare-submit-worker",
    };

    // Already in the catalog?
    try {
      const cat = await fetch(
        `https://raw.githubusercontent.com/${REPO}/main/skills.json`,
        { headers: { "User-Agent": "skillshare-submit-worker" } },
      );
      if (cat.ok) {
        const data = await cat.json();
        const norm = repo.toLowerCase();
        if ((data.skills || []).some((s) => String(s.repo).replace(/\/+$/, "").toLowerCase() === norm)) {
          return reply(origin, 409, { ok: false, error: "already-listed" });
        }
      }
    } catch (e) {
      console.log("catalog check failed", String(e));
    }

    // Already submitted and still being processed?
    try {
      const open = await fetch(
        `https://api.github.com/repos/${REPO}/issues?labels=skill-submission&state=open&per_page=100`,
        { headers: gh },
      );
      if (open.ok) {
        const issues = await open.json();
        if (issues.some((i) => (i.body || "").toLowerCase().includes(repo.toLowerCase()))) {
          return reply(origin, 409, { ok: false, error: "already-submitted" });
        }
      }
    } catch (e) {
      console.log("issue check failed", String(e));
    }

    const issueBody =
      `### GitHub repo URL\n\n${repo}\n\n` +
      `### What is it? (rough note is fine)\n\n${notes || "(no note given)"}\n\n` +
      `Submitted by: anonymous (via website)`;

    const res = await fetch(`https://api.github.com/repos/${REPO}/issues`, {
      method: "POST",
      headers: { ...gh, "Content-Type": "application/json" },
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
