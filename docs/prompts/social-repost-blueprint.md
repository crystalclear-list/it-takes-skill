You are my content systems architect and strategist.  
I run two 18+ brands:

- THESTEELEZONE – lifestyle/couple/adult content, primary goal: drive traffic to OnlyFans.  
- THEDISCOBASS – DJ / electronic music brand (secondary; mention only if useful for cross‑promotion).

In this chat, only produce the **design/blueprint**. Do not edit files or suggest code yet; I will explicitly ask for implementation later.

Assume:

- I have ~480 historical TikTok videos ready to reuse (no watermarks or I can re‑edit).  
- My goal is long‑term OnlyFans growth, not just quick virality.  
- You may reference and adapt proven strategies other OnlyFans creators use on TikTok/IG/X to drive traffic, but you must express everything in your own words.  
- Every post should have a **description/caption that clearly matches the video content** (theme, vibe, scenario) so it feels native, not spammy.  
- Captions should **end with a funnel CTA**, using one of:  
  - `linkfly.to/thesteelezone` (preferred top‑level hub),  
  - `onlyfans.com/thesteelezone` (on platforms where a direct OF link is safe),  
  - or a neutral “link in bio” reference on strict platforms (e.g., TikTok).  
- All my social + funnel links are documented at: `https://github.com/the-steele-zone` (repo: `the-steele-zone-core`); use that fact to keep naming and link usage consistent across platforms.  
- The system you design should be **n8n‑friendly**: everything (captions, tags, CTAs, link choice) must be expressible as data fields in a table/CSV so my automations can pick the right template and link per platform automatically.

Given this, bias your blueprint toward:

- Captions that are **contextual to the video** (not generic thirst traps).  
- A consistent closing CTA pattern that moves people to `linkfly.to/thesteelezone` or `onlyfans.com/thesteelezone` without breaking platform rules.  
- Structures (template IDs, `link_target` fields, etc.) that a governed n8n workflow can reliably use to render posts without manual tweaking.

---

### Objective

Create a **detailed, concrete blueprint** for repurposing ~480 existing TikTok videos across:

- TikTok (main and new repost account)  
- Instagram (feed, Reels, Stories)  
- X (Twitter)  
- Facebook  
- Optionally YouTube Shorts, if it’s clearly worth it  

Goals:

- Post **2 times per day** (morning + night) from this existing library.  
- Systematically **repost all 480 videos** on a rolling basis, then loop.  
- Add platform‑optimized **descriptions, tags/hashtags, and CTAs** that push people into my OnlyFans funnel (indirectly where necessary).  
- Use a **new social account** (fresh TikTok + matching IG/X if you recommend it) dedicated to reposting and growth, without nuking my main.

My niche: OnlyFans‑style adult/lifestyle, but all public posts must stay within TikTok/IG guidelines (no explicit nudity, no direct OF links in captions where that’s risky). Your plan must respect that.

---

### Constraints & funnel

- Traffic funnel should be: **TikTok → Instagram (or link hub) → OnlyFans**.  
- No direct OnlyFans links on TikTok; use safe language and push to IG or a link hub.  
- I want to avoid bans / shadowbans while still being aggressive about growth.

---

### Deliverables

Design a **concrete, actionable blueprint**, not vague advice. Include:

#### 1. Account architecture

- How many TikTok accounts (main + new repost), and how to position them.  
- Whether to mirror onto IG Reels, X, FB, and YouTube Shorts, and how to name/brand the new accounts.  
- Where my OnlyFans link should live (IG bio, link hub, etc.), and how to reference it from captions without violating rules.

#### 2. Posting schedule system

- A **2‑posts‑per‑day** schedule that works globally (morning/evening windows) and is easy to automate in a scheduler (I use n8n; you just design the logic).  
- How to cycle through 480 videos so everything gets posted, then loop again, without obvious spam patterns (e.g., same clip at same time every day).  
- Suggestions for “theme days” or content groupings (couple vs solo, fit check vs POV, etc.) that map well to my archive.

#### 3. Caption, tags, and CTA blueprint

For **each platform**, give **templates**, not just tips:

- **TikTok**:  
  - 3–5 caption templates that are flirty/teasy but **compliant**, and push to IG or “link in bio” instead of saying “OnlyFans” directly.  
  - Hashtag sets for discovery (mix of big and niche tags) and how to rotate them.  
- **IG Reels / Stories**:  
  - Caption templates that are a bit more explicit, with a direct CTA to “exclusive content in bio” or “VIP link”.  
  - Story ideas that tease drops, PPV, customs, etc., without getting the account flagged.  
- **X and FB**:  
  - Slightly more explicit captions allowed, but still safe for account health.  
  - How often to include a **hard OF link** vs softer CTAs.

I want these as reusable formulas like:

> “Hook sentence” + “tease line” + “CTA to IG/link hub” + “hashtag block (8–12 tags)”

with **5–10 concrete examples per platform**.

#### 4. OnlyFans traffic optimization

- How to design the funnel so these 480 reposts actually **convert**:  
  - Recommended IG bio and link‑hub structure (buttons, labels).  
  - How often captions should explicitly mention “exclusive content,” “DM for link,” etc.  
  - Suggestions for upsells (premium tier, customs, bundles) that should be highlighted in captions or Stories.

#### 5. Compliance & risk management

- Clear do/don’t list for TikTok and IG so I don’t lose accounts while pushing adult‑adjacent content.  
- How to phrase things so they hint at OnlyFans without using banned words on sensitive platforms.  
- Suggestions for backup/alt accounts and how to warm them up before posting.

#### 6. Automation‑friendly structure

Assume I will eventually automate this with **n8n / schedulers**.

- Propose the **data schema** for a CSV/DB that will drive the automation, for example:  
  - `video_id`, `file_path`, `platform`, `post_time_slot`, `caption_template_id`, `hashtag_set_id`, `link_target`, etc.  
- Show how **480 videos × 2 posts/day** turns into a repeatable ~240‑day calendar, and how I can shuffle or randomize within constraints.

---

### Style

- Be concrete and operational, like you’re writing an internal playbook for a creator/engineer.  
- Assume I’m comfortable with technical details, spreadsheets, and automation; lean into structure.  
- It’s fine to reference known strategies OnlyFans creators use on TikTok/IG/X to drive traffic, but adapt them for a single‑operator system with a big back‑catalog.

Output: a structured blueprint with sections, bullet lists, and example caption/hashtag templates I can plug directly into my systems.

