# Short-video market research (paused)

Written after the 2026-08-28 agent-loop clip was judged **too slow/monotone**, then **too fast and shallow**. This is a spec, not a new render.

Audience: software engineers who read theaicommit.com (daily lab, agents, APIs). Goal: discovery → article click, not entertainment virality.

---

## What we shipped vs what research recommends

| Version | Length | Words | Voice | Feel |
|---------|--------|-------|-------|------|
| v1 | ~43s | ~123 | `onyx` @ 1.0× | Monotone, lecture |
| v2 | ~34s | same audio sped 1.28× | still `onyx` | Faster but still flat |
| **v3 (current)** | **~14s** | **~45** | `nova` @ **1.18×** | Rushed, no depth |
| **Target** | **32–45s** | **70–95** | `nova` or `sage` @ **1.0×** | Explainer, not hype |

v3 overcorrected. Entertainment shorts reward 11–18s clips; **educational how-tos do not**. Zella (2026): tutorials and educational how-tos win at **40–90 seconds** on saves, even though viral tips win at 7–20s.

---

## 1. Content

**What works in this niche**

- One *system* question per clip, not a recap of the article.
- Problem in plain language → name the change → one number → screen proof → handoff.
- B2B viewers stay for *understanding*, not punchlines. Blitzcut: 45–90s is viable in B2B because the viewer is there to learn something specific.
- Technical buyers punish fluff and overselling. Authority over hype (iStudios B2B script audits).

**What does not work**

- Article title as opening line.
- Compressing Implementing It / code into 15s.
- ELI5 analogy as the whole middle (too slow *and* too shallow if that's all you show).
- v3's 45-word dump: hook + title-like frame + one line + demo — no "why it matters" beat.

**Recommended 5 beats (keep), with more meat in 2–3**

| Beat | Job | Spoken target |
|------|-----|----------------|
| Cold open | Pain / break | 8–12 words, ~3s |
| Topic frame | *What this is* | 12–18 words, ~6s |
| Mechanism | *Why it matters* + one number | 25–40 words, ~12s |
| Demo | Visual proof (visualize.html) | 15–25 words over ~12s of screen |
| CTA | Article, not "follow" | 8–12 words, ~4s |

The ELI5 restaurant analogy stays in the **article**. In the short, replace it with one concrete consequence ("three tools = four requests, context billed every time").

---

## 2. Pace

Natural speech is **120–160 WPM**. Genre matters more than platform:

| Genre | WPM | TTS speed (OpenAI) |
|-------|-----|---------------------|
| Tutorial / how-to | 115–125 | **1.0×** |
| Educational explainer | **120–130** | **1.0–1.05×** |
| Shorts entertainment | 140–160 | 1.1–1.25× |
| News recap / hype | 155+ | 1.18×+ |

Sources: Channel Farm voiceover genre guide (Mar 2026); Avocado on-camera study (comprehension drops above ~180 WPM); Simple STT: *if the Short covers complex information, 1.0× is safer than 1.25×*.

**v3 used educational content at entertainment speed.** That is why it felt rushed.

Also: speed up **edits**, not **speech**. Cut dead air in the demo capture; leave 200–400ms pauses *after* the number and *before* the demo.

---

## 3. Voice

- **Onyx @ 1.0×** — credible, too flat for shorts (v1 complaint).
- **Nova @ 1.18×** — energetic, sounds like it's late for a meeting (v3 complaint).
- **Target:** `nova` or OpenAI `sage` at **1.0×**, medium energy, high warmth, narrow emotional range (Channel Farm: "helpful professor, not motivational speaker").
- ElevenLabs is closer to human prosody if we later pay ~$22/mo; OpenAI is fine if speed stays at 1.0× and the script has short sentences + pause punctuation.

Script-level pacing beats a speed slider: short sentences on the hook, slightly longer on the mechanism, a beat of silence before the demo.

---

## 4. Hook

Consensus across Pexo, Kompozy, Grow Creator, VidCognition:

- Decision window is **0–3 seconds**, not 0–10.
- Pattern interrupt (0–0.8s) → identity ("if you build agents / call OpenAI") → open loop ("your code owns the loop now — here's the cost").
- Tech/AI audiences respond to **a number or a break**, not "let me show you".
- LinkedIn: skip "stop scrolling"; state the claim plainly.
- Shorts/TikTok: more contrast on frame one (big text + spoken pain).

**Do not** put the article title in second 0–3. Title belongs on beat 2 (frame) or the end card.

---

## 5. Length

Zella (2026), Kapwing stats, YouTube community analyses:

| Platform | Ideal length | Best for reach | Hard cap |
|----------|--------------|----------------|----------|
| TikTok | 21–34s | 11–18s (virality) | 10 min+ |
| Instagram Reels | 7–30s | 7–15s | minutes |
| YouTube Shorts | **25–45s** | 15–30s | 3 min |
| LinkedIn video | **45–90s** B2B | 15–30s completion | 10 min |

Completion rate, not duration, is what ranks. Sub-15s clips finish (~90%) but teach almost nothing. Past 60s, completion falls unless the idea is genuinely a tutorial.

**theaicommit default: 35–45s master cut.** Trim to ~28s for Reels; leave 40–50s for LinkedIn if the demo earns it.

---

## 6. Images / visuals

Muted viewing is the default (often cited ~80–85% on Reels/LinkedIn). Bitmap title cards (our current 5×7 font slides) fail the mute test: they look like a 1990s OG card, not a Reel.

What performs:

1. **Burned-in captions** (word-timed). Highest-leverage missing feature.
2. **On-screen claim** in the first frame (large type, 4–8 words), independent of TTS.
3. **Screen recording of the real UI** (`visualize.html`) as the longest beat — Blitzcut: screen demos are the most-saved B2B format.
4. Cut every 2–4s on slides; Ken Burns / punch-in on static cards.
5. Identity kicker: "If you ship agents" / category, not a logo sting.

What to avoid: 8 seconds of a static PNG with no zoom, no captions, no UI.

---

## 7. Reachability (where *this* audience actually is)

Raw reach ≠ useful reach.

| Platform | Reach | Audience quality for this site | Role |
|----------|-------|--------------------------------|------|
| **YouTube Shorts** | High discovery + **search** | Strong for "how does X API work" queries | **Primary** — evergreen, compounds |
| **LinkedIn** | Lower raw views | Highest: engineers in work mode | **Primary** — clicks and trust |
| Instagram Reels | High inside Meta | Weak for API-migration content | Optional, same 9:16 file |
| TikTok | Highest lottery reach | Entertainment-first; B2B conversion is poor | Test only, don't optimize for it |

Montage (B2B comparison): LinkedIn native video ~5× text posts; a 10k LinkedIn view in front of practitioners beats a 1M TikTok in front of students. YouTube Shorts is the long-term search asset (6–18 month compounding). TikTok is a cheap experiment, not the core channel.

Posting windows (Sprout, tech/software on LinkedIn): weekdays, roughly 10:00–16:00 local, especially Tue–Thu. Weekends are dead for this crowd.

---

## 8. Reels vs Shorts vs TikTok

Same file can ship everywhere. **Don't** make three different stories; **do** change packaging.

| | TikTok | Reels | Shorts |
|---|--------|-------|--------|
| Algorithm cares most | Completion + rewatch | **Sends/DMs** + saves | Watch time + satisfaction |
| Tone | Casual, fast, text-heavy | Polished, captioned | Searchable, evergreen title |
| Caption style | Karaoke / huge type | Clean, readable | Readable + keyword title |
| Title / filename | Hook in first line of on-screen text | Same | **Keyword title**: "OpenAI Assistants shutdown: you own the tool loop now" |
| First frame | Pattern interrupt | Same, slightly cleaner | Same + searchable overlay |
| CTA | Profile / site | Profile / site | Spoken + description link (Shorts can attach a related video/article) |
| theaicommit fit | Low | Medium | **High** |

YouTube Shorts is decoupled from long-form ranking (2025–26). A Short will not automatically lift the article page on YouTube; it *will* search-surface if the spoken + on-screen text matches queries like "Assistants API shutdown" / "Responses API tool loop".

---

## Recommended master spec (next render, when we un-pause)

- **Length:** 38s ± 5s  
- **Script:** 75–90 words  
- **TTS:** `nova` or `sage`, **speed 1.0**, per-beat files with 0.25–0.4s pad after mechanism  
- **Hook:** pain + identity in 3s, topic named by second 7  
- **Middle:** one number (4× / three tools) explained in two sentences, then demo  
- **Visuals:** captions burned in; demo is the longest shot; slides only as 2–3s bumpers  
- **Ship:** YouTube Shorts + LinkedIn first; identical 9:16 to Reels; skip TikTok-specific edits  
- **Success:** 3s retention >70%; completion >50% on a 40s clip; clicks to the article (not view count)

## Sources

- [Zella — how long should a TikTok/Reel/Short be (2026)](https://zellahq.com/blog/how-long-should-a-tiktok-reel-or-short-be/)
- [Kapwing — short-form stats 2026](https://www.kapwing.com/resources/short-form-video-statistics-tiktok-reels-and-shorts-by-the-numbers-in-2026/)
- [Channel Farm — AI voiceover speed by YouTube genre](https://channel.farm/blog/how-to-choose-ai-voiceover-speed-tone-youtube-video-genres)
- [Blitzcut — B2B/SaaS Reel hooks 2026](https://blitzcutai.com/blog/b2b-saas-reel-hooks-2026)
- [Montage — Shorts vs Reels vs LinkedIn for B2B](https://montage.app/blog/blog-youtube-shorts-vs-reels-vs-linkedin-b2b)
- [Pexo — social explainer videos](https://pexo.ai/blog/explainer-video-for-social-media-6536)
- [Grow Creator — tech/AI Shorts hook patterns](https://growcreator.pro/blog/tech-youtube-shorts-hook-tips)
- [Neal Schaffer — LinkedIn video 2026](https://nealschaffer.com/linkedin-videos/)
