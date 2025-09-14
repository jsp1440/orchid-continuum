// functions/deploy-info.js
// Cloudflare Pages Function: GET /api/deploy-info
export async function onRequestGet({ env }) {
  // These are provided by Cloudflare Pages at runtime
  const info = {
    ok: true,
    project: env.CF_PAGES_PROJECT_NAME || null,
    url: env.CF_PAGES_URL || null,
    branch: env.CF_PAGES_BRANCH || null,
    commit_sha: env.CF_PAGES_COMMIT_SHA || null,
    commit_msg: env.CF_PAGES_COMMIT_MSG || null,
    // convenience: a short 7-char SHA for display
    commit_short: (env.CF_PAGES_COMMIT_SHA || '').slice(0, 7) || null,
    deployed_at: new Date().toISOString(),
  };
  return new Response(JSON.stringify(info, null, 2), {
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}
