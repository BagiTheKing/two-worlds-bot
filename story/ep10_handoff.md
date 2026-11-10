# Episode 10 (the finale): handoff brief

For the session that builds the finale. Read this first, then the files it
points to. **Do not start building until the creator has shared their
references** (see "Wait for the references" below).

## The project in one paragraph

**Two Worlds · One Glitch** (channel @GLITCHBOUND2469) is a YouTube Shorts
animated series: Minecraft's Steve and a Roblox Noob, whose worlds are
colliding, plus Patch (a small floating glitch detector) and Null (the
villain who deletes reality). Episodes 0–9 are published. Everything is made
by this repo:
- **3D:** Blender 5.2.3 as a Python module (`pip install bpy`), Cycles on the
  CPU.
- **Voices:** Gemini TTS, from the episode files.
- **Sound:** synthesised effects and code-composed music.
- **Rendering:** sharded across GitHub Actions runners.
- **Output:** the finished Short is pushed to a `preview-<episode id>`
  branch.

The working branch is **`lookdev-steve`** (repo `BagiTheKing/two-worlds-bot`).

## Read these, in this order

1. `story/bible.md`: the story canon (cast, the secret, the series devices,
   the Season 1 arc). Its rules override any draft.
2. `story/playbook.md`: what YouTube's numbers and the creator's eye have
   taught us. **Check every cut against it**, especially section 1, the
   first-frame and length lessons; section 2, the creator's eye; and the
   checklist at the end.
3. `story/ep10_finale_novel.md`: **the approved finale story (v2, about 45
   s)**. It's the plan to build. Earlier, longer drafts are in its git
   history; don't revive them.
4. `story/ep09_script.md` and `episodes/ep09_before_finale.json`: the last
   episode. Its new-look section is the starting point for the finale's
   renderer.
5. `src/lookdev/README.md`: the new-look characters and the world, file by
   file.
6. `README.md`: the pipeline (episode file → voices and timeline → frames →
   assembly).

## What the creator decided for the finale

- **Length: 40–45 seconds.** Not longer. Episode 9 ran 2:59, YouTube never
  gave it a test audience (58 views in 45 h, against about 1,200–1,500 for
  every 30-second episode), and most viewers left within 20 s. The playbook
  has the numbers.
- **Everything in the upgraded look**: characters, environment, Null. No
  old-look kit shots.
- **Episode 0 comes back only as a quick sped-up event** (a fast-forward of
  about 4 s: Null through the portal, the chase, the bridge, the grab), not
  a replay.
- **Focus on the one big event**: on the ledge, the trap is revealed (412
  loops), the Noob says sorry, Null can't copy it, the catch ("No tool?" /
  "I'm a Roblox player."), the 3% island, and the stinger "You weren't
  supposed to survive."
- It picks up from Episode 8's last frame: the first portal in the forest
  lights up by itself and Null's copied smile comes through it. Episode 9's
  ending (the upgraded chase) is the same moment.

## Wait for the references

The creator has **preferences for some scenes and will share reference
images before you build**, in particular:
- **the portal entrance** (how Null comes through the first portal);
- **the details of Null's cells** (the small cubes he is made of, each with
  a tiny smile, seen close up).

So: read, learn the pipeline, ask questions, and propose a plan. But **don't
model, render or record anything for those scenes until the references
arrive**, and then match them. If the plan depends on a reference, say so
and wait.

## The pipeline, the parts you will touch

- **Episode file** (`episodes/*.json`): cast (voices and acting notes),
  `events` (lines and beats in order), `overlays`, `music`, `sfx`,
  `skip_render`.
  - Times anywhere are references resolved by `src/kit/timeref.py`: `"name"`,
    `"name.end"`, `"name+0.5"`, absolute seconds.
  - **Gotcha:** a bare `"end"` means the episode's end, but `"end+0.4"` means
    *the beat named* `end`.
- **Voices:** `src/audio.py`. Gemini scene TTS with a voice cache. A scene
  is consecutive lines with at most 2 voices. Per-line keys:
  - `cut_at` pins cut times within a scene recording; `scene_start` fences a
    scene so regrouping doesn't invalidate pins.
  - `solo_text` / `solo_only` record a solo take, best of 3 by a Whisper
    score. Use it when an acting note gets read aloud or a line is in the
    wrong voice.
  - `trim` / `trim_fade` stop bleed into the next line; `tighten`; `speed`
    (it blurs consonants above about 1.1); a negative `pad` gives an instant
    interruption.
  - The mix chain:
    - `level_line`: every line to −18 dB;
    - `keep_under`: the background 15 dB under the voice;
    - `master`: speech at −16 dBFS, with a limiter;
    - `clean_tail`: removes Gemini's end-of-take noise burst.
- **Hearing check:** `tools/hearing_check.py` runs Whisper on the final mix,
  line by line, in CI prep. It reports missing or extra words.
- **New-look renderer:** `src/lookdev/ep09_new.py` is the model to follow
  for `ep10_new.py`.
  - Everything is a function of time, applied in a frame handler, so any
    frame renders alone.
  - `build()` sets up the world and characters; the `Choreo` class sets the
    shots and positions; `_acting()` holds the pose and face keys per line;
    `apply()` sets up one frame; `finish()` adds haze and grade.
  - It has `--times` for previews and `--list` for the frames it owns.
  - Shared builders are in `stage.py`; the world is `world.py`; Null is
    `null.py`.
- **Thumbnail:** `src/lookdev/ep09_thumb.py` renders a still from the
  episode scene (its own camera, faces and lights), and
  `tools/thumb_title.py` adds a one-line title. `tools/thumb_text.py` is the
  older series template; don't overwrite it.
- **Assembly:** `src/assemble.py` does the overlays (REALITY meter,
  achievement, end strip, captions) and the encode. `tools/merge_frames.py`
  merges kit and new-look frames. The finale is all new-look, so kit frames
  may not be needed at all; check how `skip_render` and `parts` interact
  before relying on it.
- **CI:** `.github/workflows/render_episode.yml`, inputs:
  - `episode`, `res`, `samples`, `voice`;
  - `voices_only`: sound preview only;
  - `new_look`: the renderer path; `new_samples`; `parts`: all, old or new;
  - `prep_from`: reuse an approved soundtrack;
  - `assemble_from`: overlay-only fixes;
  - `shots` / `reuse_run_id`.
  
  The new look renders on 40 shards. The MCprep block textures are
  downloaded from the creator's Google Drive inside CI.
- **Assets:**
  - Steve's rig and skins are in `assets/rigs/` (in the repo).
  - The MCprep resource pack is **not** in the repo and must never be
    committed (Minecraft textures). Locally, download it the way the
    workflow does (Drive id `19RXVH0N1BIs_4OxtOooqqLpZ5jK_F1ZC`), into a
    folder outside the repo, and pass it as the assets path
    (`<assets>/mcprep/resourcepacks/...`).
  - `src/textures.py build/tex` draws the remaining textures.

## Working rules (from the creator, standing)

- **Send the sound preview (`voices_only`) before the final render.** The
  creator listens and gives notes on timing and words first.
- **Comedy timing matters.** Interruptions are instant ("It's beauti—" /
  "Don't."); punchlines get room; nothing is spoken over the big laugh.
- **Playbook musts:**
  - the title's promise is in frame 1, with action already happening and a
    first line within about 0.2 s;
  - no backs to the camera;
  - no jump cuts;
  - brightness as bright as the original, even with Null on screen;
  - one premise, a build-up, one twist;
  - an end strip over the last shot, never a dark end card;
  - the last frame loops into the first;
  - never confirm or deny a viewer theory.
- **Cuts:** cut only what earlier episodes already said; keep the
  explanations a stranger needs and the good jokes.
- **Check before delivering:**
  - contact sheets of frames across the whole video (frame 1, every shot's
    first and last frames, the loop, captions, overlays);
  - Whisper's hearing report;
  - the length.
- **Git:**
  - commit and push to `lookdev-steve`;
  - never put a model name or ID in commits, code comments or anything
    pushed;
  - end commit messages with the attribution lines your session gives you.
- **Credits:** the Steve rig is "Minecraft Rig Steve" by EpicPiggy_1401356
  (BlendSwap, CC-BY). It stays in every description. Credit viewers whose
  ideas are used (@youssefakram7493 is a loyal regular).
- **Don't** try to push to the MCprep repository (that access was refused on
  purpose), and don't commit its textures.

## Hard-won lessons (so you don't repeat them)

- **Frames:**
  - Cancel stuck CI runs with
    `gh api -X POST repos/BagiTheKing/two-worlds-bot/actions/runs/<id>/force-cancel`.
    A normal cancel can leave dozens of jobs blocking the queue.
  - Downloading artifacts from this sandbox is blocked. Read results from the
    `preview-<id>` branch instead; MP4s over 95 MB are split into
    `episode.mp4.part-*`, so join them with `cat`.
  - Use `ffmpeg -nostdin` inside `while read` loops.
  - Render small (`--times`, low samples) and look at the frames before any
    full CI render. A full new-look render takes about 1 hour of wall time.
  - On the local CPU (4 cores), a 1080x1920 still at 48 samples takes about
    3 minutes.
- **Voices:**
  - Gemini sometimes reads the acting note aloud, or speaks a line in the
    other character's voice. Use `solo_text`.
  - Re-grouping scenes invalidates pinned cuts; use `scene_start`.
  - Check every changed line in the sound preview.
- **Story:**
  - A stranger must understand every beat (95% of viewers are new).
  - Carry the link to the last episode in the picture, not in dialogue.

## Your first reply to the creator

Confirm you've read the brief and the files above. Restate the finale plan
in a few lines, list the new 3D pieces you'll need, and ask for the
references. Then wait.
