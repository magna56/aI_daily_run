# Short-video pipeline (sketch)

Turn a daily session folder into a **60–90 second vertical explainer** (9:16) suitable for Shorts, Reels, or TikTok. The reader site is unchanged; output lives under `videos/<id>/` and is not deployed by `make deploy`.

## Goals

- **One command** per article: `make video ID=2026-08-28`
- **Reuse session artifacts** — `topic.md`, `journal.md`, `visualize.html`, `diagram.excalidraw`
- **Dependency-free Node** for scripting and assembly (same as `build.js`); only **ffmpeg** required on PATH
- **Optional OpenAI TTS** when `OPENAI_API_KEY` is set; otherwise emit `narration.txt` for manual recording or external TTS
- **Human in the loop** for the interactive demo beat until automated browser capture lands

## Non-goals (for now)

- No avatar / stock-footage APIs
- No auto-publish to YouTube or social
- No changes to `build.js` or the reader SPA
- Learn and Frontier tracks (daily sessions only in v0)

## Pipeline stages

```
topic.md + journal.md
        │
        ▼
  ┌───────────┐
  │  script   │  lib/video/script.js — beats: hook, setup, insight, demo cue, CTA
  └─────┬─────┘
        ▼
  ┌─────────────┐
  │ storyboard  │  lib/video/storyboard.js — timing, visual source per beat
  └──────┬──────┘
        ├──────────────────┐
        ▼                  ▼
  ┌───────────┐     ┌────────────┐
  │  slides   │     │    TTS     │  lib/video/slides.js, lib/video/tts.js
  │  (PNG)    │     │  (optional)│
  └─────┬─────┘     └──────┬─────┘
        │                  │
        │    ┌─────────────┴──────────────┐
        │    │  capture/ (manual v0)      │  Screen record visualize.html → demo.mp4
        │    └─────────────┬──────────────┘
        ▼                  ▼
  ┌─────────────────────────────────────┐
  │           assemble (ffmpeg)         │  lib/video/assemble.js
  └─────────────────┬───────────────────┘
                    ▼
         videos/<id>/out/short-9x16.mp4
```

## Output layout

```
videos/2026-08-28/
  script.json          # structured beats + full narration text
  narration.txt        # plain text for TTS or voice recording
  storyboard.json      # timeline the assembler reads
  slides/
    beat-01-hook.png
    beat-02-setup.png
    ...
  audio/
    narration.mp3      # when OPENAI_API_KEY is set
  capture/
    demo.mp4           # you drop this in (v0); future: Playwright recorder
  out/
    short-9x16.mp4     # final render
```

## Beat template (default)

| # | Beat | Source | Visual | Target duration |
|---|------|--------|--------|-----------------|
| 1 | Hook | `topic.md` `**Hook**` | Title slide | ~8s |
| 2 | Setup | First ~2 sentences of ELI5 or The Problem | Text slide | ~15s |
| 3 | Insight | `journal.md` Key insight (trimmed) | Text slide | ~12s |
| 4 | Demo | Fixed cue line | `capture/demo.mp4` if present, else diagram or viz placeholder | ~25s |
| 5 | CTA | Title + canonical URL | Branded end card | ~8s |

Durations scale with word count (~2.5 words/sec) when TTS audio is absent. When `audio/narration.mp3` exists, beat lengths follow the audio file (split evenly across beats in v0; word-timestamps in v1).

## Commands

```bash
make video ID=2026-08-28              # script → storyboard → slides → TTS? → assemble
node video.js 2026-08-28 --script     # script.json + narration.txt only
node video.js 2026-08-28 --dry-run    # stop before ffmpeg
OPENAI_API_KEY=sk-... make video ID=2026-08-28
```

### Automated demo capture (v0)

When `visualize.html` exists, `make video` records it headlessly with Playwright
(slider 1 → 6, drop-call bug, Conversations API, reset) into `capture/demo.mp4`.
Requires a one-time install:

```bash
npm install --prefix .video-deps playwright
npx playwright install chromium
```

To skip: `node video.js <id> --no-capture`. To re-record: `node video.js <id> --capture`.

### Manual demo capture (fallback)

1. `make serve` and open the session's Visualize tab, or open `2026-08-28/visualize.html` locally.
2. Record **20–30s** at 1080×1920 (or 1080×1920 crop): slide the tool-count slider, toggle a replay bug.
3. Save as `videos/2026-08-28/capture/demo.mp4`.
4. Re-run `make video ID=2026-08-28` — assembler splices the demo into beat 4.

## Cost model (1–2 videos/day)

| Piece | Tool | Approx. cost |
|-------|------|----------------|
| Script | This pipeline (local) | $0 |
| Voice | OpenAI `tts-1` | ~$0.01–0.03/video (~200 words) |
| Voice | ElevenLabs Creator | ~$22/mo flat |
| Slides + assembly | ffmpeg (local) | $0 |
| Demo capture | QuickTime / OBS / Screen Studio | $0 (your time) |
| Edit polish | CapCut / Descript | $0–24/mo |

**Typical cash burn:** under **$3/day** at 1–2 videos if you use OpenAI TTS or an existing subscription. Time dominates: **30–45 min/video** once the workflow is familiar.

## Roadmap

| Version | Deliverable |
|---------|-------------|
| **v0 (this sketch)** | Script + storyboard + slide PNGs + ffmpeg concat; Playwright capture of `visualize.html` |
| **v1** | Playwright presets per session (which sliders/buttons to hit) |
| **v2** | Word-level TTS timestamps → accurate captions (SRT) burned in |
| **v3** | `video.md` override file per session (custom beats, B-roll notes) |
| **v4** | Optional publish hook (upload API / `yt-dlp` metadata sidecar) |

## Environment

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Enable TTS (`tts-1`, voice `onyx`) |
| `VIDEO_VOICE` | Override TTS voice (default `onyx`) |
| `VIDEO_WPM` | Narration pacing for duration estimates (default `150`) |
| `PUBLIC_URL` | Site origin for CTA links (default `https://theaicommit.com`) |

## Integration notes

- **Do not** add videos to `site/` or `deploy.sh` until hosting and CDN cost are decided.
- Reuse `slugify` rules from `build.js` so CTA URLs match canonical reader paths.
- `make check` is unchanged; a future `make check-video` can validate `videos/<id>/out/` exists for flagged sessions.
