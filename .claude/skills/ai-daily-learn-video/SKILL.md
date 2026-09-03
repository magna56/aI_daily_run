---
name: ai-daily-learn-video
description: >
  Turn a daily AI Daily Learn session folder into a short 9:16 explainer video
  (slides + visualize.html capture + TTS + captions). First-draft lock: alloy /
  tts-1-hd, ~80 words, engineer beat is one section not the whole video.
  Use when: "make the video", "short video for today's article", "ai-daily-learn-video",
  "session video", "reel", "shorts", "generate video from article".
  Optional id: /ai-daily-learn-video 2026-08-28
argument-hint: "[YYYY-MM-DD]"
verified: llm
---

# Short video from a daily session

Local pipeline. Does **not** deploy the site. Does **not** invent a new format —
`video.js` is the source of truth. This skill only runs it, reports the file, and
commits `media/videos/` when the user asked to push.

## First-draft lock (do not "improve" unless asked)

The accepted draft for 2026-08-28 is the contract:

| Knob | Value |
|------|--------|
| Voice | OpenAI `tts-1-hd` / `alloy` at speed `1.0` |
| Script | News → what changed → cost → **optional engineer beat** → demo → CTA |
| Engineer beat | The **`Engineer's view`** metadata line, which is the article's own engineer translation and is written to explain the mapping in one plain sentence. One beat, not the whole video. (`## For a Software Engineer` was retired on 2026-09-02 and replaced by that box; before that the beat came from the mechanism section's opening sentence, which no longer begins "From a software engineering perspective, …".) |
| Tone | Factual. No "you've done this before", no wry/teammate acting. |
| Length | ~30–45s, ~80 words |
| Captions | Burned-in SRT |
| Output | `videos/<id>/out/short-9x16.mp4`; publish copy under `media/videos/` |

Do not switch to `coral`, `gpt-4o-mini-tts`, or personality `instructions` unless
the user explicitly asks. Those reads as theatrical or condescending.

Full research: `docs/video-market-research.md`. Pipeline: `docs/video-pipeline.md`.

## Prerequisites (once per machine)

```bash
which ffmpeg || echo "install ffmpeg"
which node
make video-setup    # Playwright for visualize.html capture
```

Voiceover needs `OPENAI_API_KEY`, **or** macOS Keychain:

```bash
security add-generic-password -a theaicommit -s openai-api-key-theaicommit -w 'sk-...'
```

`video.js` reads that Keychain item automatically. Never paste keys into chat, `.env`, or git.

## Steps

### 1. Pick the session

- Argument `YYYY-MM-DD` or `YYYY-MM-DD-s2` if given.
- Else the newest daily folder (what `node video.js` does with no id).
- Folder must contain `topic.md`. `visualize.html` is used for the demo beat when present.

### 2. Generate (write `videos/`, gitignored scratch)

```bash
make video ID=<id> MEDIA=1
# same: node video.js <id> --media
```

That writes:

- `videos/<id>/script.json`, `narration.txt`, `captions.srt`
- `videos/<id>/slides/*.png`
- `videos/<id>/capture/demo.mp4` (Playwright, if visualize.html exists)
- `videos/<id>/out/short-9x16.mp4`
- `media/videos/<id>-<slug>-short.mp4` (`--media`)

If TTS is skipped, say so: missing key. Still produce a silent cut.

### 3. Do not rewrite the script by hand

If the user hates a line, change `lib/video/script.js` (or add a later `video.md` override),
re-run the command, do not paste a one-off narration into ffmpeg.

### 4. Push only when asked

Scratch `videos/` stays gitignored.

When they want the draft in git:

```bash
git add media/videos/<file>.mp4
git commit -m "Add short video for <id>"
git push
```

Follow this repo's publish rules: `ai-daily-learn-github` / `ai-daily-learn-publish`
push **main** directly. Do not open a PR unless they are already on a feature branch
and asked to stay there.

### 5. Report

```
Video: media/videos/<file>.mp4
Duration: <ffprobe seconds>
Voice: alloy / tts-1-hd
Session: https://theaicommit.com/<slug>/
```

## Flags

| Flag | Meaning |
|------|---------|
| `--media` | Copy into `media/videos/` (committable) |
| `--capture` | Re-record visualize.html even if demo.mp4 exists |
| `--no-capture` | Slides only |
| `--no-tts` | Silent |
| `--script` | script.json + narration.txt only |
| `--dry-run` | Stop before ffmpeg mux |

```bash
make video                          # newest session
make video ID=2026-08-28 MEDIA=1
make video ID=2026-08-28 VIDEO_FLAGS='--no-tts --dry-run'
```
