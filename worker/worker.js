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

function issueRepository(body) {
  const match = String(body || "").match(/^### GitHub repo URL\r?\n+([^\r\n]+)/m);
  const value = match ? match[1].trim() : "";
  return REPO_URL_RE.test(value) ? value.replace(/\/+$/, "").replace(/\.git$/, "").toLowerCase() : "";
}

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

    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return reply(origin, 400, { ok: false, error: "Invalid JSON object" });
    }
    const repo = String(body.repo || "").trim().replace(/\/+$/, "").replace(/\.git$/, "");
    const notes = String(body.notes || "").trim().slice(0, 1000);
    const platforms = body.platforms ?? [];
    const type = body.type || "";
    const source = String(body.source || "").trim();
    if (!Array.isArray(platforms) || platforms.length > 3 ||
        platforms.some(p => !["claude-code", "codex", "chatgpt"].includes(p)) ||
        !["", "skill", "plugin", "mcp", "tool", "collection", "reference", "workflow"].includes(type) ||
        (source && (!/^https:\/\/[^\s]+$/.test(source) || source.length > 500))) {
      return reply(origin, 400, { ok: false, error: "bad-metadata" });
    }

    if (!REPO_URL_RE.test(repo)) {
      return reply(origin, 400, { ok: false, error: "bad-repo" });
    }

    const gh = {
      "Authorization": `Bearer ${env.GH_TOKEN}`,
      "Accept": "application/vnd.github+json",
      "User-Agent": "skillshare-submit-worker",
    };

    // Global daily intake cap — protects review capacity and Actions from
    // being flooded when the link makes the rounds publicly.
    const DAILY_CAP = 40;
    try {
      const today = new Date().toISOString().slice(0, 10);
      const q = encodeURIComponent(`repo:${REPO} label:skill-submission created:>=${today}`);
      const res = await fetch(`https://api.github.com/search/issues?q=${q}&per_page=1`, { headers: gh });
      if (!res.ok) throw new Error('Daily cap unavailable');
      if (res.ok) {
        const data = await res.json();
        if (data.total_count >= DAILY_CAP) {
          return reply(origin, 429, { ok: false, error: "daily-limit" });
        }
      }
    } catch (e) {
      console.log("daily cap check failed", String(e));
      return reply(origin, 503, { ok: false, error: "intake-unavailable" });
    }

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
        const existing = issues.find((i) => !i.pull_request && issueRepository(i.body) === repo.toLowerCase());
        if (existing) {
          return reply(origin, 409, { ok: false, error: "already-submitted", issue: existing.html_url });
        }
      }
    } catch (e) {
      console.log("issue check failed", String(e));
    }

    const issueBody =
      `### GitHub repo URL\n\n${repo}\n\n` +
      `### Suggested platforms\n\n${[...new Set(platforms)].join(", ") || "Not sure"}\n\n` +
      `### Offering type\n\n${type || "Not sure"}\n\n` +
      `### Provider documentation\n\n${source || "Not provided"}\n\n` +
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
    return reply(origin, 202, { ok: true, state: "received", issue: issue.html_url });
  },
};
