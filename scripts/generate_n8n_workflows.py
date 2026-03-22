"""
generate_n8n_workflows.py

Generates importable n8n workflow JSON files into n8n/workflows/.
Run once, then import each file into n8n via:
  n8n UI → Workflows → Import from file

Outputs:
  n8n/workflows/steelezone_post_dispatcher.json  ← main daily driver
  n8n/workflows/steelezone_caption_renderer.json ← caption fill
  n8n/workflows/steelezone_weekly_report.json    ← weekly summary
"""

import json, os, uuid

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "n8n", "workflows")
os.makedirs(OUT, exist_ok=True)

def nid(): return str(uuid.uuid4())

# ── helpers ────────────────────────────────────────────────────────────────

def webhook_node(node_id, name, path, x, y):
    return {
        "id": node_id, "name": name,
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [x, y],
        "webhookId": str(uuid.uuid4()),
        "parameters": {
            "httpMethod": "POST",
            "path": path,
            "responseMode": "responseNode",
            "options": {}
        }
    }

def respond_node(node_id, name, x, y, body_expr):
    return {
        "id": node_id, "name": name,
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1,
        "position": [x, y],
        "parameters": {
            "respondWith": "json",
            "responseBody": body_expr,
            "options": {"responseCode": 200}
        }
    }

def code_node(node_id, name, x, y, code):
    return {
        "id": node_id, "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, y],
        "parameters": {"jsCode": code, "mode": "runOnceForAllItems"}
    }

def switch_node(node_id, name, x, y, field, rules):
    """rules = list of {"value": "...", "outputIndex": N}"""
    return {
        "id": node_id, "name": name,
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3,
        "position": [x, y],
        "parameters": {
            "mode": "rules",
            "rules": {
                "values": [
                    {
                        "conditions": {
                            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                            "combinator": "and",
                            "conditions": [{"leftValue": f"={{{{ $json.{field} }}}}", "rightValue": r["value"], "operator": {"type": "string", "operation": "equals"}}]
                        },
                        "renameOutput": True,
                        "outputKey": r["value"]
                    }
                    for r in rules
                ]
            },
            "options": {}
        }
    }

def sticky(node_id, content, x, y, w=400, h=200):
    return {
        "id": node_id, "name": "Sticky Note",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
        "parameters": {"content": content, "width": w, "height": h}
    }

def auth_check_code(token_env="N8N_WEBHOOK_TOKEN"):
    return f"""
// Auth check — validates Bearer token from Authorization header
const auth = $input.first().json.headers?.authorization || '';
const token = process.env.{token_env} || '';
if (!token) throw new Error('Env var {token_env} is not set');
if (auth !== 'Bearer ' + token) {{
  throw new Error('Unauthorized: invalid or missing Bearer token');
}}
return $input.all();
""".strip()

def platform_post_code(platform):
    return f"""
// ── {platform.upper()} POSTING LOGIC ──────────────────────────────────────
// This node is a placeholder. Replace with your {platform} node(s).
//
// Available fields from payload:
//   $json.post_id        — unique post identifier
//   $json.video_id       — e.g. SZ-0001
//   $json.caption_rendered — full caption text (fill via caption_render webhook first)
//   $json.hashtag_set_id — e.g. TT-H1
//   $json.link_url       — resolved CTA link for this platform
//   $json.scheduled_date — ISO date
//   $json.time_slot      — AM | PM
//
// Steps to complete this node:
//   1. Delete this Code node
//   2. Add a {platform} node (or HTTP Request node) with your credentials
//   3. Map the fields above into the posting action
//   4. Connect its output to the Respond node

console.log('[{platform}] post triggered:', $json.post_id, $json.video_id);
return [{{ json: {{ status: 'placeholder — add your {platform} node here', ...$json }} }}];
""".strip()


# ══════════════════════════════════════════════════════════════════════════
# 1. POST DISPATCHER  (main daily driver — handles all 4 platforms)
# ══════════════════════════════════════════════════════════════════════════

def build_dispatcher():
    wh_id    = nid()
    auth_id  = nid()
    sw_id    = nid()
    tt_id    = nid()
    ig_id    = nid()
    x_id     = nid()
    fb_id    = nid()
    ok_id    = nid()
    err_id   = nid()
    note_id  = nid()

    platforms = ["tiktok_repost", "ig_reel", "x", "facebook"]

    nodes = [
        sticky(note_id,
            "## THESTEELEZONE — Post Dispatcher\n\n"
            "Receives all scheduled posts from `config/post_schedule.csv` via the governed OS.\n\n"
            "**Webhook path:** `/webhook/steelezone-dispatch`\n"
            "**Auth:** Bearer token → set `N8N_WEBHOOK_TOKEN_DISPATCH` in n8n env vars\n\n"
            "**To activate:**\n"
            "1. Set `N8N_WEBHOOK_TOKEN_DISPATCH` in n8n Settings → Environment Variables\n"
            "2. Replace each platform placeholder node with your real posting nodes\n"
            "3. Toggle workflow Active → ON",
            -200, -200, 700, 260),

        webhook_node(wh_id,  "Receive Post",      "steelezone-dispatch", 260, 300),
        code_node(auth_id,   "Auth Check",         460, 300, auth_check_code("N8N_WEBHOOK_TOKEN_DISPATCH")),
        switch_node(sw_id,   "Route by Platform",  660, 300, "platform",
                    [{"value": p} for p in platforms]),

        code_node(tt_id, "TikTok Repost",  900, 100,  platform_post_code("TikTok")),
        code_node(ig_id, "IG Reel Post",   900, 260,  platform_post_code("Instagram Reel")),
        code_node(x_id,  "X Post",         900, 420,  platform_post_code("X / Twitter")),
        code_node(fb_id, "Facebook Post",  900, 580,  platform_post_code("Facebook")),

        respond_node(ok_id,  "Respond OK",
                     1100, 300,
                     '={{ JSON.stringify({status:"ok", post_id:$json.post_id, platform:$json.platform}) }}'),
        respond_node(err_id, "Respond Error",
                     660, 500,
                     '={{ JSON.stringify({status:"error", message:$json.message}) }}'),
    ]

    connections = {
        "Receive Post":     {"main": [[{"node": "Auth Check",        "type": "main", "index": 0}]]},
        "Auth Check":       {"main": [[{"node": "Route by Platform", "type": "main", "index": 0}]]},
        "Route by Platform": {"main": [
            [{"node": "TikTok Repost", "type": "main", "index": 0}],
            [{"node": "IG Reel Post",  "type": "main", "index": 0}],
            [{"node": "X Post",        "type": "main", "index": 0}],
            [{"node": "Facebook Post", "type": "main", "index": 0}],
        ]},
        "TikTok Repost": {"main": [[{"node": "Respond OK", "type": "main", "index": 0}]]},
        "IG Reel Post":  {"main": [[{"node": "Respond OK", "type": "main", "index": 0}]]},
        "X Post":        {"main": [[{"node": "Respond OK", "type": "main", "index": 0}]]},
        "Facebook Post": {"main": [[{"node": "Respond OK", "type": "main", "index": 0}]]},
    }

    return {"name": "THESTEELEZONE — Post Dispatcher",
            "nodes": nodes, "connections": connections,
            "active": False, "settings": {"executionOrder": "v1"},
            "versionId": nid(), "id": nid(), "tags": [{"name": "steelezone"}]}


# ══════════════════════════════════════════════════════════════════════════
# 2. CAPTION RENDERER
# ══════════════════════════════════════════════════════════════════════════

def build_caption_renderer():
    wh_id   = nid()
    auth_id = nid()
    code_id = nid()
    ok_id   = nid()
    note_id = nid()

    render_code = """
// Caption renderer — fills {{hook_line}} and {{tease_line}} into a template
// and appends the hashtag block.
//
// Template map (matches docs/blueprints/social-repost-blueprint.md)
const templates = {
  "T-1": "{{hook_line}}\\n{{tease_line}}\\n#couplesoftiktok #relationshipgoals #lifestylevlog #adultlife #thatgirl #fyp #foryou #viralcouple",
  "T-2": "{{hook_line}}\\n{{tease_line}}\\n#fitcheck #outfitcheck #fashiontiktok #selfcare #hotgirlsummer #fyp #viralvideo #trending",
  "T-3": "{{hook_line}}\\n{{tease_line}}\\n#pov #fyp #foryoupage #relatable #vibes #couplevlog #lifestyleblogger #niche",
  "T-4": "{{hook_line}}\\n{{tease_line}}\\n#dayinmylife #vlog #reallife #lifestyle #couplethings #fyp #foryou #adultlife",
  "T-5": "{{hook_line}}\\n{{tease_line}}\\n#fyp #foryoupage #trending #viralcouple #lifestylevlog #exclusive #realones #thatgirl",
  "I-1": "{{hook_line}}\\n{{tease_line}}\\n#instagramreels #reelsofinstagram #couplegoals #lifestylecreator #adultcreator #exclusive",
  "I-2": "{{hook_line}}\\n{{tease_line}}\\n#instareels #lifestyle #thatgirl #couplelife #fyp #exclusive #contentcreator",
  "I-3": "{{hook_line}}\\n{{tease_line}}\\n#reels #couplegoals #realcouple #lifestyleblogger #exclusive #onlyfanscreator",
  "I-4": "{{hook_line}}\\n{{tease_line}}\\n#confidence #selfcare #hotgirlera #reels #lifestyle #exclusive #adultcreator",
  "I-5": "{{hook_line}}\\n{{tease_line}}\\n#reels #exclusive #vip #onlyfans",
  "X-1": "{{hook_line}}\\n{{tease_line}}",
  "X-2": "{{hook_line}}\\n{{tease_line}}",
  "X-3": "{{hook_line}}\\n{{tease_line}}",
  "X-4": "{{hook_line}}\\n{{tease_line}}",
  "X-5": "{{hook_line}}\\n{{tease_line}}",
  "F-1": "{{hook_line}}\\n{{tease_line}}",
  "F-2": "{{hook_line}}\\n{{tease_line}}",
  "F-3": "{{hook_line}}\\n{{tease_line}}",
};

const { caption_template_id, hook_line = '', tease_line = '', link_url = '' } = $json;
const tmpl = templates[caption_template_id] || '{{hook_line}}\\n{{tease_line}}';
let rendered = tmpl
  .replace(/\\{\\{hook_line\\}\\}/g,  hook_line)
  .replace(/\\{\\{tease_line\\}\\}/g, tease_line)
  .replace(/\\{\\{link_url\\}\\}/g,   link_url);

return [{ json: { ...$json, caption_rendered: rendered } }];
""".strip()

    nodes = [
        sticky(note_id,
            "## Caption Renderer\n\n"
            "Fills `{{hook_line}}` and `{{tease_line}}` into the named template.\n"
            "Call this **before** the Post Dispatcher to generate `caption_rendered`.\n\n"
            "**Webhook:** `/webhook/caption-render`\n"
            "**Auth:** `N8N_WEBHOOK_TOKEN_CAPTION`",
            -200, -100, 500, 180),
        webhook_node(wh_id,  "Receive Caption Request", "caption-render", 260, 300),
        code_node(auth_id,   "Auth Check",               460, 300, auth_check_code("N8N_WEBHOOK_TOKEN_CAPTION")),
        code_node(code_id,   "Render Caption",           660, 300, render_code),
        respond_node(ok_id,  "Respond with Caption",     860, 300,
                     '={{ JSON.stringify({status:"ok", caption_rendered:$json.caption_rendered, post_id:$json.post_id}) }}'),
    ]

    connections = {
        "Receive Caption Request": {"main": [[{"node": "Auth Check",      "type": "main", "index": 0}]]},
        "Auth Check":              {"main": [[{"node": "Render Caption", "type": "main", "index": 0}]]},
        "Render Caption":          {"main": [[{"node": "Respond with Caption", "type": "main", "index": 0}]]},
    }

    return {"name": "THESTEELEZONE — Caption Renderer",
            "nodes": nodes, "connections": connections,
            "active": False, "settings": {"executionOrder": "v1"},
            "versionId": nid(), "id": nid(), "tags": [{"name": "steelezone"}]}


# ══════════════════════════════════════════════════════════════════════════
# 3. WEEKLY REPORT
# ══════════════════════════════════════════════════════════════════════════

def build_weekly_report():
    wh_id   = nid()
    auth_id = nid()
    code_id = nid()
    ok_id   = nid()
    note_id = nid()

    report_code = """
// Weekly summary placeholder
// Replace with your reporting logic:
//   - Query n8n execution history
//   - Count successes / failures per platform
//   - Write summary to a Google Sheet, Notion, or email
const { report_period, trigger_reason } = $json;
console.log(`Weekly report triggered: ${report_period} — ${trigger_reason}`);
return [{ json: { status: 'report_placeholder', report_period, trigger_reason } }];
""".strip()

    nodes = [
        sticky(note_id,
            "## Weekly Summary\n\n"
            "Generates weekly post performance report.\n"
            "Replace the Code node with your actual reporting logic.\n\n"
            "**Webhook:** `/webhook/weekly-summary`\n"
            "**Auth:** `N8N_WEBHOOK_TOKEN_REPORTING`",
            -200, -100, 500, 180),
        webhook_node(wh_id,  "Receive Report Request", "weekly-summary", 260, 300),
        code_node(auth_id,   "Auth Check",              460, 300, auth_check_code("N8N_WEBHOOK_TOKEN_REPORTING")),
        code_node(code_id,   "Build Report",            660, 300, report_code),
        respond_node(ok_id,  "Respond OK",              860, 300,
                     '={{ JSON.stringify({status:"ok", ...$json}) }}'),
    ]

    connections = {
        "Receive Report Request": {"main": [[{"node": "Auth Check",   "type": "main", "index": 0}]]},
        "Auth Check":             {"main": [[{"node": "Build Report", "type": "main", "index": 0}]]},
        "Build Report":           {"main": [[{"node": "Respond OK",   "type": "main", "index": 0}]]},
    }

    return {"name": "THESTEELEZONE — Weekly Report",
            "nodes": nodes, "connections": connections,
            "active": False, "settings": {"executionOrder": "v1"},
            "versionId": nid(), "id": nid(), "tags": [{"name": "steelezone"}]}


# ── write files ────────────────────────────────────────────────────────────

workflows = [
    ("steelezone_post_dispatcher.json",    build_dispatcher()),
    ("steelezone_caption_renderer.json",   build_caption_renderer()),
    ("steelezone_weekly_report.json",      build_weekly_report()),
]

for filename, wf in workflows:
    path = os.path.join(OUT, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2)
    print(f"  wrote {path}")

print(f"\nDone — {len(workflows)} workflow files in n8n/workflows/")
print("\nTo import:")
print("  n8n UI → Workflows → ⋮ menu → Import from file → pick each JSON")
