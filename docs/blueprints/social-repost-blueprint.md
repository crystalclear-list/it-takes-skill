# THESTEELEZONE — Content Repurposing & Funnel Blueprint

**Brand:** THESTEELEZONE | **Archive:** ~480 videos | **Cadence:** 2×/day | **Horizon:** Rolling 240-day calendar, then loop

---

## Non-Negotiables (Governance Layer)

- No direct OnlyFans links or "OnlyFans" mentions on TikTok, IG captions, or FB posts.
- All CTAs on TikTok/FB must point to IG or `linkfly.to/thesteelezone`, never OF directly.
- No nudity or sexually explicit wording on TikTok/IG/FB; X + OF handle the explicit side.
- Any automation must respect: no repost of the same video on the same platform within 60 days, and `audit_verdict` must be `pass` before dispatch.

---

## 1. Account Architecture

### TikTok: Two-Account Strategy

**Account A — Main (`@thesteelezone`)**
- Personality-forward: couple content, lifestyle, relationship energy, "day in our life" framing.
- Slower cadence (1×/day or 5×/week). Warmer, more parasocial.
- Bio: pushes to IG. Never mentions OF by name. Uses "exclusive content → link in bio" language.
- This account has history and social proof. Protect it.

**Account B — Repost/Growth (`@steelezoneraw` or `@thesteeledrop`)**
- Dedicated repurposing machine. Posts 2×/day from the archive.
- Framed as "behind-the-scenes / extended cuts" of the main account.
- Bio: `📲 Full version → thesteelezone on IG` — funnels to IG, not OF directly.
- If Account B gets restricted, Account A is untouched.
- Warm up: first 7 days post 1×/day with no CTA, just native content. Day 8+ activate full schedule.

### Instagram

**Account: `@thesteelezone` (unified brand handle)**
- This is the **middle of the funnel** — the place TikTok pushes to.
- IG bio holds the money link: `linkfly.to/thesteelezone`
- Feed + Reels mirror the best-performing TikTok clips (reposted 24–48h after TikTok, stripped of TikTok watermark).
- Stories are the upsell layer: PPV teasers, "just dropped on OF," DM CTA.

### X (Twitter)

**Account: `@thesteelezone`**
- Most permissive platform for adult-adjacent content.
- Can include `onlyfans.com/thesteelezone` directly in posts and bio.
- Post 1×/day from the archive, slightly more explicit caption framing than TikTok/IG.
- Use quote-tweets of your own posts to stack engagement on high-performing clips.

### Facebook

**Page: THESTEELEZONE**
- Lowest-ROI platform for this niche. Treat as a syndication layer only.
- Post 3–4×/week, auto-scheduled via n8n, zero manual effort.
- Caption framing: lifestyle/couple energy. CTA: `linkfly.to/thesteelezone`.
- Do not link OF directly. FB will suppress reach on pages that do.

### YouTube Shorts

**Worth it only if:** you have clips with strong hook-in-first-3-seconds that aren't dependent on TikTok sound trends.
- If yes: create a `@thesteelezone` YT channel, post 1 Short/day from the archive's most visually arresting clips.
- YT Shorts can appear in Google search results — long-tail discovery value.
- Description: `More at linkfly.to/thesteelezone` — YT allows link hub references.
- If your archive skews toward audio-driven trends, skip YT Shorts for now.

### Link Hub Structure (`linkfly.to/thesteelezone`)

```
Button 1: 🔥 OnlyFans – Exclusive Content     → onlyfans.com/thesteelezone
Button 2: 📸 Instagram                          → instagram.com/thesteelezone
Button 3: 🎵 TikTok                             → tiktok.com/@thesteelezone
Button 4: 🐦 Twitter / X                        → x.com/thesteelezone
Button 5: 💌 DM Me on IG (Customs/Requests)    → instagram.com/thesteelezone (DM)
```

This structure means every platform CTA can safely point to `linkfly.to/thesteelezone` and the user self-selects into OF from there. No platform sees a direct OF link in your caption.

---

## 2. Posting Schedule System

### Time Slots (n8n scheduler fields)

| Slot ID | Name | UTC Post Time | Rationale |
|---|---|---|---|
| `AM` | Morning Drop | 11:00 UTC | US East morning commute (6–7am EST) / EU lunch |
| `PM` | Night Drop | 22:00 UTC | US prime time (5–6pm PST) / highest engagement window |

These two fixed slots give your n8n cron a clean trigger without complex timezone logic. You can A/B test ±1 hour per slot over time.

### 480-Video Cycling Logic

**Core principle:** treat the archive as a **shuffled deck**, not a queue.

- Divide 480 videos into **8 thematic buckets** of ~60 videos each (see Section 3 for bucket taxonomy).
- Each week, rotate through 4 buckets — 2 buckets per time slot across the week.
- After 240 days (all 480 videos posted once at 2×/day), reshuffle each bucket randomly and start the loop again.
- **Anti-spam shuffle rule:** no video may repeat on the same platform within 60 days of its last post. Track `last_posted_date` per `(video_id, platform)` pair in your DB.
- On the loop, change caption templates for the same video (template rotation field in schema).

### Weekly Pattern (prevents obvious spam)

```
Monday:     Bucket A (AM) + Bucket B (PM)
Tuesday:    Bucket C (AM) + Bucket D (PM)
Wednesday:  Bucket A (AM) + Bucket C (PM)   ← cross-bucket mixing mid-week
Thursday:   Bucket E (AM) + Bucket F (PM)
Friday:     Bucket B (AM) + Bucket G (PM)
Saturday:   Bucket H (AM) + Bucket E (PM)   ← weekend gets "higher energy" buckets
Sunday:     Bucket D (AM) + Bucket H (PM)
```

This pattern means no two consecutive days pull from the same pair, and the weekend skews toward your highest-performing content categories.

### Theme Days (optional but high-value for algorithmic consistency)

TikTok's algorithm rewards accounts that train viewer expectations. Suggested:

- **Monday:** Couple content / "us" energy
- **Wednesday:** Fit check / fashion / confidence era
- **Friday:** POV / "catch me" / playful framing
- **Saturday/Sunday:** "Behind the scenes" / day-in-the-life / vlog-adjacent

These map directly to bucket taxonomy and become a `theme_day` field in your automation schema.

---

## 3. Caption, Tags, and CTA Blueprint

### Caption Formula (universal structure)

```
[Hook line — first 1–2 sentences, front-loaded, platform-specific energy]
[Tease line — creates curiosity gap or FOMO without being explicit]
[CTA — platform-safe, contextual, closes the loop]
[Hashtag block — platform-appropriate quantity and mix]
```

All templates below use `{{hook_line}}` and `{{tease_line}}` as parameterized fields. The example values are reference copy for n8n to render via `caption_template_id`. Hashtag blocks remain literal and are referenced separately via `hashtag_set_id`.

---

### TikTok Caption Templates

**Positioning:** lifestyle, couple energy, flirty but PG-13. Never say "OnlyFans." Push to IG or "link in bio."

**Template T-1 (Couple / Relationship)**
```
▎ {{hook_line}}   ← e.g., "We always get asked how we keep it this good. 🤷‍♀️"
▎ {{tease_line}}  ← e.g., "The version we can't post here lives somewhere else — check my IG if you know, you know."
▎ #couplesoftiktok #relationshipgoals #lifestylevlog #adultlife #thatgirl #fyp #foryou #viralcouple
```
`caption_template_id: T-1` | `hashtag_set_id: TT-H1` | `link_target: linkinbio`

**Template T-2 (Fit Check / Confidence)**
```
▎ {{hook_line}}   ← e.g., "Outfit did exactly what it was supposed to. 💅"
▎ {{tease_line}}  ← e.g., "Full look (and what came after) — link in bio takes you somewhere a lot more fun."
▎ #fitcheck #outfitcheck #fashiontiktok #selfcare #hotgirlsummer #fyp #viralvideo #trending
```
`caption_template_id: T-2` | `hashtag_set_id: TT-H2` | `link_target: linkinbio`

**Template T-3 (POV / Playful)**
```
▎ {{hook_line}}   ← e.g., "POV: you finally found the right corner of the internet."
▎ {{tease_line}}  ← e.g., "There's a whole other side of this on my IG. Go find it."
▎ #pov #fyp #foryoupage #relatable #vibes #couplevlog #lifestyleblogger #niche
```
`caption_template_id: T-3` | `hashtag_set_id: TT-H3` | `link_target: linkinbio`

**Template T-4 (Day-in-Life / Vlog-Adjacent)**
```
▎ {{hook_line}}   ← e.g., "Not every day looks like this but today… yeah, today delivered."
▎ {{tease_line}}  ← e.g., "More of our actual life (and the parts TikTok won't let us post) → IG link in bio."
▎ #dayinmylife #vlog #reallife #lifestyle #couplethings #fyp #foryou #adultlife
```
`caption_template_id: T-4` | `hashtag_set_id: TT-H3` | `link_target: linkinbio`

**Template T-5 (Mysterious / Curiosity Gap)**
```
▎ {{hook_line}}   ← e.g., "Some content just doesn't belong on TikTok. 🙃"
▎ {{tease_line}}  ← e.g., "You'll understand when you get there. → IG link in bio."
▎ #fyp #foryoupage #trending #viralcouple #lifestylevlog #exclusive #realones #thatgirl
```
`caption_template_id: T-5` | `hashtag_set_id: TT-H4` | `link_target: linkinbio`

**TikTok Hashtag Sets (rotate to avoid repetition)**

| Set ID | Hashtags |
|---|---|
| `TT-H1` | #fyp #foryou #foryoupage #viralvideo #trending #lifestyle #couple #thatgirl |
| `TT-H2` | #couplesoftiktok #relationshipgoals #adultlife #fitcheck #hotgirlsummer #selfcare #niche |
| `TT-H3` | #vlog #dayinmylife #reallife #couplethings #pov #aesthetic #lifestyle #mood |
| `TT-H4` | #tiktokgirls #girlsoftiktok #confidence #fyp #vibes #relatable #foryoupage |

Mix 2–3 big tags (#fyp, #trending) with 4–5 niche tags per post. Never use the same set two days in a row on the same account.

---

### Instagram Reels / Feed Caption Templates

**Positioning:** warmer, more explicit about the fact that exclusive content exists. Direct link to `linkfly.to/thesteelezone` or `onlyfans.com/thesteelezone` in CTA is fine.

**Template I-1 (Reels / High-Energy)**
```
▎ {{hook_line}}   ← e.g., "We don't hold back much. 🔥"
▎ {{tease_line}}  ← e.g., "But the real stuff? That's exclusive. Full access at the link in bio — you already know where to find us."
▎ #instagramreels #reelsofinstagram #couplegoals #lifestylecreator #adultcreator #exclusive
```
`caption_template_id: I-1` | `hashtag_set_id: IG-H1` | `link_target: linkfly`

**Template I-2 (Suggestive / Teasy)**
```
▎ {{hook_line}}   ← e.g., "This is the version safe for IG. 😏"
▎ {{tease_line}}  ← e.g., "The version you actually want to see — linkfly.to/thesteelezone in bio."
▎ #instareels #lifestyle #thatgirl #couplelife #fyp #exclusive #contentcreator
```
`caption_template_id: I-2` | `hashtag_set_id: IG-H1` | `link_target: linkfly`

**Template I-3 (Relationship / Parasocial)**
```
▎ {{hook_line}}   ← e.g., "People ask what our relationship is like. This is the surface level."
▎ {{tease_line}}  ← e.g., "Subscribe for the full picture. Link in bio. 🖤"
▎ #reels #couplegoals #realcouple #lifestyleblogger #exclusive #onlyfanscreator
```
`caption_template_id: I-3` | `hashtag_set_id: IG-H2` | `link_target: linkfly`

**Template I-4 (Confidence / Solo)**
```
▎ {{hook_line}}   ← e.g., "Felt like myself today. That's the caption."
▎ {{tease_line}}  ← e.g., "More of this, less filtered — exclusive content at the link in my bio."
▎ #confidence #selfcare #hotgirlera #reels #lifestyle #exclusive #adultcreator
```
`caption_template_id: I-4` | `hashtag_set_id: IG-H2` | `link_target: linkfly`

**Template I-5 (Story-Tease Companion — used alongside a Reel)**
```
▎ {{hook_line}}   ← e.g., "Full vid posted. 🎥"
▎ {{tease_line}}  ← e.g., "But if you want the uncut version, you know where I am. Link in bio."
▎ #reels #exclusive #vip #onlyfans
```
`caption_template_id: I-5` | `hashtag_set_id: IG-H2` | `link_target: linkfly`

**IG Story Strategy (weekly cadence)**

| Day | Story Type | Purpose |
|---|---|---|
| Mon | "New drop" teaser — blurred or cropped frame from OF | Drive clicks to OF link |
| Wed | Poll: "Would you rather see [X] or [Y] next?" | Engagement signal, zero risk |
| Fri | "Dropping something tonight on OF" countdown sticker | Creates anticipation |
| Sat | DM CTA: "Customs open this weekend — DM me" | Upsell |
| Sun | Behind-the-scenes clip from the week | Parasocial warmth |

---

### X (Twitter) Caption Templates

**Positioning:** most permissive. Direct OF link is safe. Slightly more explicit framing is fine. Keep it punchy — X rewards brevity.

**Template X-1**
```
▎ {{hook_line}}   ← e.g., "Some things just film better than they sound in text. 🎥"
▎ {{tease_line}}  ← e.g., "Full access → onlyfans.com/thesteelezone"
```
`caption_template_id: X-1` | `link_target: of_direct`

**Template X-2**
```
▎ {{hook_line}}   ← e.g., "This is the version I can post publicly."
▎ {{tease_line}}  ← e.g., "You can probably guess what the private version looks like. → onlyfans.com/thesteelezone"
```
`caption_template_id: X-2` | `link_target: of_direct`

**Template X-3**
```
▎ {{hook_line}}   ← e.g., "No filter, no edit, no apology. 🖤"
▎ {{tease_line}}  ← e.g., "All of it lives here: onlyfans.com/thesteelezone"
```
`caption_template_id: X-3` | `link_target: of_direct`

**Template X-4**
```
▎ {{hook_line}}   ← e.g., "We shoot a lot. Most of it doesn't end up on TikTok."
▎ {{tease_line}}  ← e.g., "The rest goes here 👇 onlyfans.com/thesteelezone"
```
`caption_template_id: X-4` | `link_target: of_direct`

**Template X-5**
```
▎ {{hook_line}}   ← e.g., "New week. New content drop."
▎ {{tease_line}}  ← e.g., "For the real ones: onlyfans.com/thesteelezone"
```
`caption_template_id: X-5` | `link_target: of_direct`

**X Hashtag Strategy:** use 2–4 tags max. X deprioritizes posts with hashtag stuffing.
Good sets: `#OnlyFans #ContentCreator` / `#AdultContent #CoupleContent` / `#NSFW #Lifestyle`

---

### Facebook Caption Templates

**Positioning:** lifestyle-first. No OF link directly. Push to link hub.

**Template F-1**
> Couple content. Good energy. Unfiltered life. 🖤
> More of this at: linkfly.to/thesteelezone

**Template F-2**
> Not every moment makes it to TikTok. Some of our best stuff lives elsewhere.
> linkfly.to/thesteelezone — all our links in one place.

**Template F-3**
> New video from the archive. Same energy, different day. 🔥
> Find all our content at linkfly.to/thesteelezone

---

## 4. OnlyFans Traffic Optimization

### Funnel Architecture

```
TikTok (Account A + B)
    ↓  "check my IG / link in bio"
Instagram (@thesteelezone)
    ↓  bio: linkfly.to/thesteelezone
Link Hub (linkfly.to/thesteelezone)
    ↓  Button 1: "🔥 Exclusive Content"
OnlyFans (onlyfans.com/thesteelezone)
```

X and FB enter the funnel at the link-hub or OF level directly, bypassing the IG middle step.

### IG Bio Copy (recommended)

```
THESTEELEZONE 🖤
Couple | Lifestyle | Exclusive Content
📲 TikTok → @thesteelezone
🔥 Full Access Below ↓
linkfly.to/thesteelezone
```

Short, benefit-forward, no banned words. The phrase "Full Access" implies OF without triggering filters.

### Caption Frequency for Key Phrases

| Phrase | Platform | Recommended Frequency |
|---|---|---|
| "exclusive content" | IG | Every post |
| "link in bio" | TikTok | Every post |
| "DM for customs" | IG Stories | 1–2×/week |
| "dropping tonight on OF" | IG Stories | 1×/week |
| Direct OF URL | X only | Every X post |
| "VIP access" | IG, FB | 2–3×/week |
| "the version TikTok won't allow" | TikTok | 1×/week (high-performing template) |

### Upsell Cadence (Stories + Captions)

- **Weekly OF drop announcement:** every Friday IG Story — "New content just dropped, link in bio."
- **PPV tease:** blur/crop a frame, post in Stories with "available now" — 1×/week.
- **Customs open window:** announce Saturday morning, close Sunday night. Creates scarcity.
- **Bundle reference in caption:** 1×/week on IG, use phrasing like "vault access" or "full series" rather than "bundle" (sounds more premium).
- **THEDISCOBASS cross-promo (1×/week max):** use clips filmed at events or with strong music energy.
  - TikTok/IG caption: tag @thediscobass, keep it lifestyle/music-first.
  - X caption: optionally add a line like "We play hard, we party harder" + OF link. This keeps the universes linked without over-promoting between brands.

---

## 5. Compliance & Risk Management

### TikTok — Do/Don't

| Do | Don't |
|---|---|
| Use "link in bio" language | Say "OnlyFans" in captions or audio |
| Push to IG explicitly | Post anything with visible nudity even partially |
| Use lifestyle / couple / vlog framing | Use words: suggestive, explicit, adult, NSFW, 18+, OF |
| Keep hook in first 0–2 seconds | Let engagement drop below 5% (signals spam to algo) |
| Post consistently (never miss a scheduled slot) | Post the same video twice within 60 days |
| Use trending audio from TikTok's library | Use original audio on a shadowbanned track |
| Respond to comments within 2h of posting | Leave the comments section unmonitored |

**Shadow-ban prevention:**
- Warm up Account B for 7 days with zero CTAs.
- Never follow/unfollow aggressively from Account B.
- Space posts at least 4 hours apart on the same account.
- If engagement drops >40% over 3 days, pause posting for 48h on that account.

### Instagram — Do/Don't

| Do | Don't |
|---|---|
| Use "exclusive content in bio" | Post anything that would be removed on TikTok |
| Use IG Stories for upsell | Put OF URL in Reel captions (bio link is fine) |
| Enable Instagram's "Sensitive Content" setting (set to "Standard") | Use #OnlyFans or #OF in IG hashtags (flagged) |
| Keep face visible for parasocial trust | Post dark/low-quality reposts without re-export |

### Backup Account Strategy

- **TikTok backup:** create a third TikTok account (`@steelezoneback` or similar) and warm it up immediately, posting 2–3 times/week with zero CTAs. If Account B gets banned, you have a warm replacement within 30 days.
- **IG backup:** create a second IG (`@steelezone.vip` or `@thesteelezone.daily`) and post 2–3 times/week. Keep it lower-key. If main gets restricted, redirect TikTok bio to the backup IG.
- **Warming schedule for any new account:** Week 1: 1×/day, no CTA, native content only. Week 2: 1×/day, soft CTA ("more on my other page"). Week 3+: full posting schedule with CTAs.

### Language Substitution Table (for caption copy)

| Avoided word/phrase | Safe substitute |
|---|---|
| OnlyFans | "my exclusive platform," "subscription content," "VIP page" |
| NSFW / adult | "not for everyone," "exclusive," "private" |
| 18+ | omit entirely from TikTok captions; use in X |
| Sex / sexy | "energy," "vibe," "the real us" |
| Explicit | "unfiltered," "uncensored" (use sparingly) |
| Nude / naked | omit entirely on TikTok/IG |

---

## 6. Automation-Friendly Data Schema

### Master Post Table Schema

| Field | Type | Description |
|---|---|---|
| `post_id` | UUID | Unique per (video × platform × scheduled_date) |
| `video_id` | string | Internal archive ID (e.g., `SZ-0001`) |
| `file_path` | string | Local or cloud path to the video file |
| `bucket_id` | enum | `A`–`H` — thematic bucket assignment |
| `theme_day` | string | `couple`, `fitcheck`, `pov`, `vlog`, `behind_scenes` |
| `platform` | enum | `tiktok_main`, `tiktok_repost`, `ig_reel`, `ig_story`, `x`, `facebook`, `yt_shorts` |
| `scheduled_date` | date | ISO 8601 |
| `time_slot` | enum | `AM` (11:00 UTC), `PM` (22:00 UTC) |
| `caption_template_id` | string | e.g., `T-1`, `I-2`, `X-3`, `F-1` |
| `hook_line` | text | Rendered value for `{{hook_line}}` placeholder |
| `tease_line` | text | Rendered value for `{{tease_line}}` placeholder |
| `caption_rendered` | text | Final rendered caption (template + hook + tease filled in) |
| `hashtag_set_id` | string | e.g., `TT-H1`, `TT-H2` |
| `link_target` | enum | `linkfly`, `of_direct`, `linkinbio`, `ig_handle` |
| `link_url` | string | Resolved URL for this platform |
| `last_posted_date` | date | Per (video_id × platform) — for 60-day repeat guard |
| `loop_number` | integer | 1 = first pass, 2 = second loop, etc. |
| `template_rotation` | integer | Which template variant was used (increments each loop) |
| `status` | enum | `scheduled`, `posted`, `failed`, `skipped` |
| `n8n_run_id` | string | Links back to the governed dispatch run |
| `audit_verdict` | enum | `pass`, `fail`, `pending` |

### n8n Workflow Name Convention (matches governed OS)

Following the `category__name` pattern from the governed n8n integration spec:

| Logical Name | Action |
|---|---|
| `content__tiktok_repost_daily` | Post to TikTok repost account |
| `content__ig_reel_post` | Post to IG Reels |
| `content__ig_story_post` | Post IG Story tease |
| `content__x_post` | Post to X |
| `content__facebook_post` | Syndicate to FB |
| `content__yt_shorts_post` | Post to YouTube Shorts |
| `content__caption_render` | Fill caption template with video-specific hook |
| `infra__60day_repeat_guard` | Query DB, flag videos due for a rest |
| `infra__schedule_builder` | Generate the next 7 days of post_id records |
| `reporting__weekly_summary` | Summarize what posted, what failed, engagement delta |

### 480-Video Calendar Math

```
480 videos ÷ 2 posts/day = 240 days to cycle the full archive (one pass)
240 days ≈ 8 months per loop

Loop 1 (Days 1–240):   Template rotation = 1
Loop 2 (Days 241–480): Template rotation = 2 (different caption template for same video)
Loop 3+:               Caption template rotates again; hashtag set also rotates
```

The `caption_template_id` + `loop_number` combination means a video posted 3 times across 24 months never gets the exact same caption twice.

### Bucket Taxonomy (map your archive to these)

| Bucket | Label | ~Video Count | Example Content |
|---|---|---|---|
| A | Couple Energy | 60 | Us together, date night, candid |
| B | Fit Check / Fashion | 60 | Outfit reveal, mirror selfie video |
| C | POV / Playful | 60 | Camera-forward, direct-address, funny |
| D | Day-in-Life / Vlog | 60 | Real-life moments, routines |
| E | Teasy / Suggestive | 60 | Compliant, hinting at exclusive content |
| F | Confidence / Solo | 60 | Solo content, attitude, energy |
| G | Behind-the-Scenes | 60 | Setup, candid, "what we don't post" framing |
| H | High-Energy / Viral Bait | 60 | Best hooks, most shareable, trend-adjacent |

Bucket H should always contain your strongest performers. Weight the weekend schedule toward H.

### n8n Dispatch Payload Shape (per the governed schema)

When `content__tiktok_repost_daily` fires, the payload passed to the n8n webhook should contain exactly the fields in `allowed_payload_keys`:

```
allowed_payload_keys for content__* endpoints:
  - post_id
  - video_id
  - file_path
  - platform
  - caption_rendered
  - hashtag_set_id
  - link_url
  - scheduled_date
  - time_slot
  - n8n_run_id
```

No PII. No raw secrets. Auth token is resolved server-side from `auth_env_var`.

**Any new field added to the payload must be added to the allowlist and documented here before it can be used by workflows.**

---

## Cross-Platform Consistency Rules

1. **Same video never posts to two platforms on the same day.** Spread it: TikTok AM, IG Reel the next day, X the day after. This staggers discovery and avoids duplicate-content penalties.
2. **Caption rendered for each platform is unique** — even if the video is the same, `caption_rendered` differs by `platform` and `caption_template_id`.
3. **`link_target` resolves automatically by platform:**
   - `tiktok_*` → `linkinbio`
   - `ig_reel`, `ig_story`, `facebook` → `linkfly`
   - `x` → `of_direct`
   - `yt_shorts` → `linkfly`
4. **`audit_verdict` must be `pass` before any post dispatches.** This is enforced by the governed n8n workflow — no caption containing banned terms, no PII in payload, no unresolved auth env var.
