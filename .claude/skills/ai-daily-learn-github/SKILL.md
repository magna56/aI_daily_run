---
name: ai-daily-learn-github
description: >
  Runs a full AI Daily Learn session AND pushes it to GitHub main — but does NOT deploy the site.
  Same topic selection, same five artifacts in ~/ai_learning/YYYY-MM-DD/, same commit-straight-to-
  main behavior as ai-daily-learn-publish, minus the last step: it never calls deploy.sh, so
  theaicommit.com, the gh-pages mirror, and the newsletter are all untouched. Use when the user
  wants the session's source of truth on GitHub without going live yet — "push to github but
  don't deploy", "commit today's session, skip the site", "publish to github only",
  "ai-daily-learn-github". Use ai-daily-learn-publish instead when they want it live, or plain
  ai-daily-learn when they want it saved locally only, not even committed. Accepts optional topic
  argument: /ai-daily-learn-github "vision transformers".
argument-hint: "[optional-topic]"
# Same rule as ai-daily-learn-publish: this commits straight to main, so the session becomes
# the published source of truth even though the site is not deployed. Always the most capable
# model. The override lasts for this turn only, which covers the nested ai-daily-learn run.
model: opus
verified: llm
---

# AI Daily Learn — GitHub-Only Variant

This skill is **`ai-daily-learn-publish` minus its last step.** It runs the identical session
workflow and pushes to `main` the identical way — same gate, same commit shape, same idempotent
script pattern — and then stops. It deliberately does not restate the session workflow either, so
none of the three skills in this family can drift apart from each other.

**Why this exists, not just "publish but skip a step":** the full publish path treats "on GitHub"
and "live" as one event, because for the automated daily job they always should be. A manual run
sometimes wants them apart — stage a session on `main` to review the diff, fix something before it
reaches a reader, or batch several sessions and deploy once. This skill is that half.

## Which track

Same as `ai-daily-learn-publish` — both tracks, same contract, only the folder and cadence differ.

| | **Daily lab** (default) | **Frontier** |
| --- | --- | --- |
| Invoked by | `/ai-daily-learn-github` | `/ai-daily-learn-github --frontier` (or "frontier session") |
| Folder | `YYYY-MM-DD/` | `frontier/YYYY-MM-DD/` |
| Cadence | **Never a blank day** | **Skip a thin day** |
| `journal.md` | Gets a block | No block — Frontier is not in the daily index |
| Audience gate | Applies | **Not applicable** — the track is excluded from `--mix` by design |
| Site / newsletter | **Never touched by this skill**, either track | same |

**A Frontier run that publishes nothing is a successful run.** Say what you looked at and why none
of it was worth an article, and stop. The daily lab has the opposite rule: **never end a lab run
with the day empty.** Both exactly as in `ai-daily-learn-publish` — see that skill's Error Handling
if either edge case comes up; it is not repeated here.

## Step A: Run the full session

Execute the entire `ai-daily-learn` workflow, Steps 1 through 12, exactly as written:

```
Skill(skill="tp-mcp-config:ai-daily-learn", args="<the topic argument, if the user gave one>")
```

If the Skill tool is unavailable, read this checkout first:

```
./.claude/skills/ai-daily-learn/SKILL.md
./.claude/skills/ai-daily-learn/selection.md
./.claude/skills/ai-daily-learn/visualize.md
./.claude/skills/ai-daily-learn/contract.md
```

Fall back to `~/.claude/plugins/tp-mcp-config/skills/ai-daily-learn/SKILL.md` or
`~/tp_claude/plugins/tp-mcp-config/skills/ai-daily-learn/SKILL.md` only if those are missing.

Note the exact session directory name it produced — `YYYY-MM-DD`, or `YYYY-MM-DD-s2` for a second
session on the same day. Steps A½ and B need it.

## Step A½: Gate the session before it lands on main

`main` is this repo's own source of truth, read by every future session, every skill, and anyone
who clones it — a session that quietly missed a content rule belongs there just as little as it
belongs on a live site, even though nothing here will put it in front of a reader today. Re-run the
lint here rather than trusting that Step A finished clean:

```bash
cd ~/ai_learning && node build.js --check 2>&1 | grep "YYYY-MM-DD"
```

**A content-contract warning naming today's id blocks the push.** Fix the session and re-run;
never fix it by loosening the spec. The blocking ones:

- `no "## Implementing It" section` — the write-up never shows the code the reader has to write.
- `no fenced code block` — the section exists but defers to `code_example.py`, which most readers
  never open and nobody reading on a phone will run.
- anything about `visualize.html` — a session without a working visualizer has no Visualize tab.
- **the readability warnings** — a paragraph over 110 words, a sentence over 45, a single-block
  `The Problem`, **a British spelling**, **a mean sentence over 18 words**, or **any section outside its word band** (floors block as well as caps), plus the
  structural checks: section order, a retired section, a bad `TLDR`, a missing `Engineer's view`. Landing an unreadable session on
  `main` is worse than it sounds: it becomes the example every future session is written against.
  Fix **in the section named** — over its cap, cut it there; under its floor, it is owed words
  back rather than trimmed further — and correct `**Time to read**` to
  match what you shipped.

Then the **audience gate** — did this session take a slot that was already at cap?

```bash
cd ~/ai_learning && node build.js --mix YYYY-MM-DD    # exit 3 = it ignored what was due
```

This asks about the one session, not the trailing average: was its tier, or its `**For**` layer,
already at cap in the ten sessions before it? **Non-blocking here too** — `publish_github.sh`
treats it as a loud warning, never a refusal, for the same reason `ai-daily-learn-publish` does:
regenerating for the due category is cheap while the article is still new; holding a finished
session off `main` is not the fix for a mix problem.

Other warnings are advisory and do not block: a `code_example.py` that exits non-zero is a
*rendered traceback* by design, not a broken build.

Then confirm by eye the two things no linter can see (`ai-daily-learn` Step 11 has the same pair):
`## Implementing It` gives code for **every role the change touches**, and the title has been read
cold as the engineer scrolling past it, not just checked against the shape rules.

## Step B: Push to GitHub — and stop there

```bash
PUB=""
for CAND in \
  ./.claude/skills/ai-daily-learn-github/scripts/publish_github.sh \
  "${AI_LEARNING_DIR:-$HOME/ai_learning}/.claude/skills/ai-daily-learn-github/scripts/publish_github.sh" \
  ~/.claude/plugins/tp-mcp-config/skills/ai-daily-learn-github/scripts/publish_github.sh \
  ~/tp_claude/plugins/tp-mcp-config/skills/ai-daily-learn-github/scripts/publish_github.sh \
  ~/.claude/skills/ai-daily-learn-github/scripts/publish_github.sh ; do
  [ -f "$CAND" ] && { PUB="$CAND"; break; }
done
[ -n "$PUB" ] || echo "publish_github.sh not found — see Manual fallback below"

bash "$PUB" YYYY-MM-DD            # the exact session dir name from Step A
bash "$PUB" frontier/YYYY-MM-DD  # a Frontier session
```

`publish_github.sh` is `ai-daily-learn-publish`'s `publish.sh` with exactly one thing removed: the
call to `deploy.sh` at the end. Everything before that is identical — it initialises the repo and
remote if missing, runs the same content gate, commits the session directory plus `journal.md`,
rebases if the remote moved, and pushes to `main`. **Never open a PR** — this is a personal notes
repo and the daily job (and this skill) are its only writers.

**What this deliberately does not do:** no `deploy.sh` call means no Cloudflare Pages rebuild, no
`gh-pages` push, and no newsletter send. `feed.xml`, `sitemap.xml`, and the session's Open Graph
card are all *build* outputs written by `deploy.sh`'s own `make site` step — since that step never
runs here, none of them are regenerated, and the live reader keeps serving whatever it was already
serving. The session exists on `main` and nowhere else a reader would see it.

**If you want it live too**, either run `/ai-daily-learn-publish` from the start instead of this
skill, or — once this skill has pushed — run `cd ~/ai_learning && make deploy` (or `bash
.claude/skills/ai-daily-learn-publish/scripts/publish.sh YYYY-MM-DD`, which is idempotent and will
find nothing new to commit but will still run the site deploy). Either finishes the job this skill
intentionally left half-done.

### Manual fallback

If the script is missing entirely:

```bash
cd ~/ai_learning
git add YYYY-MM-DD journal.md
git commit -m "YYYY-MM-DD: <topic title>"
git push origin HEAD:main
```

## Step C: Confirm the push landed, then report

There is no live site to check — that is the whole point of this skill — so Step C is shorter than
`ai-daily-learn-publish`'s: confirm the commit is really on `origin/main`, not that a reader can
see it.

```bash
cd ~/ai_learning && git log --oneline -1
git rev-parse HEAD
git ls-remote origin main | cut -f1
```

The last two should match. If they do not, the push did not land — see Error Handling below rather
than reporting the session as pushed.

Print what is due next, same as `ai-daily-learn-publish` does — this is a purely local read of
`topic.md` files and is unaffected by whether anything deployed:

```bash
cd ~/ai_learning && node build.js --mix
```

Include its **DUE NEXT** line in the summary.

Then report. Use the same summary block as `ai-daily-learn` Step 12, but replace its "Read it"
block with the GitHub commit, and say plainly that the site was not touched:

```
Pushed to GitHub: https://github.com/magna56/aI_daily_run/commit/<short-sha>
Source:           https://github.com/magna56/aI_daily_run

Site not deployed. theaicommit.com and the gh-pages mirror are unchanged, and no newsletter
was sent. Run 'make deploy' (or /ai-daily-learn-publish) when you want this live.
```

## Publish-Only Mode

If the user asks to push a session that already exists — "push yesterday's to github, don't
deploy", "commit the 2026-08-18 session" — **skip Step A entirely** and run Step B against that
directory. Do not regenerate a session that is already on disk. Step A½ still applies and
`publish_github.sh` still runs its own gate, but sessions predating the content contract are
exempt by date in `build.js`, so republishing the back catalog never trips it.

## Error Handling

- Push rejected / no network / VPN down → say so in the Step C summary and tell the user to
  re-run `bash "$PUB" YYYY-MM-DD` later. **Never** force-push, and never open a PR instead.
- Rebase conflict in `~/ai_learning` → the script aborts the rebase and stops; resolve by hand.
- Session generation failed in Step A → do not push a partial session. Report the failure.
- `publish_github.sh` aborted with `content gate` → the session does not meet `contract.md`. Fix
  it in place — usually: write the `## Implementing It` section with real code in `topic.md` —
  and re-run. This is a five-minute edit, not a reason to stop.
- `audience gate` warning in the log → the session's tier or `**For**` layer was already at cap.
  It still pushed. Name the miss in the summary and correct it in tomorrow's pick.
- A **Frontier** run that found nothing worth publishing → report it as done, name what you
  checked, and stop. Not an error, not a retry, not a thinner article.
- The user asks why the site did not update after running this skill → it was never supposed to.
  Point at `make deploy` or `/ai-daily-learn-publish`; this is not a bug in this skill.

There is no "site deploy failed" case here, unlike `ai-daily-learn-publish` — there is no deploy
attempt to fail. Everything else that can go wrong is on the GitHub side, covered above.

## Scope

Unlike `ai-daily-learn-publish`, this skill is not what the scheduled 11:00 job runs — that job
needs the session live, which is exactly the step this skill omits. It has no LaunchAgent, no
`install_schedule.sh`, and nothing here should be scheduled to run unattended: an unattended job
that only ever pushes to `main` without deploying would let commits and the live site drift apart
silently, which is the opposite of what the daily cadence is for.
