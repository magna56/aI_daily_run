---
name: ai-daily-learn-video
description: >
  Turn a daily session folder into a short 9:16 explainer (slides, visualize
  capture, TTS, captions). Use when: "make the video", "short video",
  "ai-daily-learn-video", "reel", "shorts", "generate video from article".
  Optional id: /ai-daily-learn-video 2026-08-28
---

# Short video (Cursor)

Same pipeline as Claude's `/ai-daily-learn-video`. Spec is the Claude skill so
the two tools cannot drift.

## Read first (mandatory)

1. [SKILL.md](../../../.claude/skills/ai-daily-learn-video/SKILL.md) — lock, commands, push rules
2. [docs/video-pipeline.md](../../../docs/video-pipeline.md)
3. [docs/video-market-research.md](../../../docs/video-market-research.md)

## Run

```bash
make video-setup   # once: Playwright
make video ID=YYYY-MM-DD MEDIA=1
```

Omit `ID` for the newest daily folder. `video.js` reads `OPENAI_API_KEY` or
macOS Keychain `openai-api-key-theaicommit` (account `theaicommit`).

**First-draft lock:** `tts-1-hd` + `alloy` at 1.0×. Engineer mapping is one beat,
not the whole video. Do not switch to coral / mini-tts instructions unless asked.

Push `media/videos/*.mp4` only when the user asked to commit. Scratch stays in
`videos/` (gitignored).
