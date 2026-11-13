# The movie: handoff brief

For the session(s) that rework **Two Worlds · One Glitch** (Episodes 0-10)
into **one long-form landscape video** for the channel. Read this first, then
the files it points to. It sums up how the finale was made with the creator,
so a fresh session can work the same way.

## What the creator asked for

- **One long movie** for the channel (long-form, not a Short), made from the
  whole series, Episode 0 to the finale.
- **Landscape, one screen size** (16:9, 1920x1080) for the whole movie; the
  Shorts were vertical (1080x1920).
- **Everything in the upgraded ("new") look**: Episodes 0-8 were made in the
  old kit look and must be rebuilt in the new look, like Episodes 9-10.
- **The beginning and the end belong together: "one core, two
  perspectives".** Episode 0 (the first portal, Null coming through, the
  chase, the bridge) and the finale's ending are the same story seen from two
  sides. That is already true of the episodes as made: the movie keeps
  them as they are, in order, so the ending answers the opening.
- **Work it part by part**, the creator giving notes on each part, as in the
  finale.
- **A remake of what already exists**: same story, lines and sound; only the
  picture changes (see below).

**Decided by the creator: this is a remake, not a new story.** Nothing
about the story, the script or the sound is open:
- **Same story, same order, same lines.** Episodes 0 to the finale, as
  published. No new scenes, no new bridges, no new bookends, no rewritten
  lines, no new interpretation of the scenario.
- **No new voices, no new sound.** Reuse each episode's finished soundtrack
  and timing as they are (the final mix and `timeline.json` on each
  `preview-<episode id>` branch, or the CI run that made them). Nothing is
  re-recorded and nothing goes to the TTS.
- **"One core, two perspectives" already exists.** Episode 0 is the bridge
  moment seen the first time (Steve and the Noob running, the fall); the
  finale lives the same moment again from inside the loop (the "Noob, RUN!"
  deja vu, "412 times", "I built a trap"). The beginning and the ending are
  already written and rendered; the movie only has to keep them as they are
  so they answer each other.
- **What changes is only the picture:** landscape 16:9 and the new look.
  Episodes 0-8 are re-staged in the new look, shot for shot on their
  existing timing and sound; Episode 9 and the finale are reframed for
  landscape and re-rendered.
- **The Shorts packaging is dropped** (it isn't content): "FINALE n/5"
  badges, to-be-continued cards, end cards, "next episode" cards, episode
  number cards. Everything inside the story stays, captions included (in a
  landscape layout). The episode titles become YouTube chapters in the
  description.

So **don't ask the creator about story, perspectives, length, cuts, captions
or music**: those are settled above. Ask only about something genuinely
technical that this brief and the files can't answer, and propose your own
answer with the question.

## Read these, in this order

0. **`story/creator_notes.md`: everything the creator has asked for and
   insisted on, from the first episode to the finale. Follow it.**
1. `story/bible.md`: the canon. Its rules override any draft.
2. `story/playbook.md`: the creator's eye and YouTube's numbers. Most of it is
   about Shorts; the "creator's eye" rules (section 2) and the checklist still
   apply to long form.
3. `story/ep10_handoff.md`: the pipeline, file by file, and the working rules.
   Everything in it still holds.
4. `story/ep10_finale_novel.md` and `episodes/ep10_p*.json`: the finale as
   built (14 parts).
5. `src/lookdev/README.md`: the new-look characters and world.

## How the finale was made (copy this loop for every movie part)

The finale was built as **14 parts of about 7-17 s each**, one renderer per
part (`src/lookdev/ep10_pN_*.py`), one episode file per part
(`episodes/ep10_pN_*.json`). For each part:

1. **Story beats** for the part, agreed with the creator in words.
2. **Episode file**, then **voices only** on CI (`voices_only=true`). Send the
   creator the **sound preview** (an m4a) and wait for notes on words and
   timing. Never render frames before the sound is approved.
3. **Renderer**, then **local test stills** (`--times`, `--res 720`,
   `--samples 12`) at the key beats: look at them before anything else.
4. **CI preview** (`res=720`, `new_samples=20`), sent to the creator.
5. Creator's notes, fixes, a new preview if needed.
6. **Full render** on approval (`res=1080`, `new_samples=64`,
   `prep_from=<the approved voices run>`).
7. **The review gate** (see `CLAUDE.md`): `tools/review_part.py`, then the
   `part-reviewer` agent with the creator's request word for word. Send only
   on PASS, with the reviewer's summary; the creator gives the final
   approval.

**The creator's notes from the finale. Treat them as rules:**
- **No sudden turns.** Characters turn like people: head, then shoulders, then
  hips, with a step; nobody snaps round (when grabbed, when put down).
- **Nothing appears from nowhere.** A prop is seen arriving (the duck walks
  over before the Noob picks it up); the robot arms *transform* out of Patch,
  piece by piece ("mechanic, Gundam-style"), they don't just appear.
- **Bodies never go inside walls or the ground.** Hanging characters hang
  clear of the wall, from their raised arm; feet land on the ground.
- **Poses must read:** sitting legs bent and planted, not squashed; a
  one-handed turn while hanging hangs straight from the raised arm.
- **Faces carry the scene:** anger means knitted brows (pulled together and
  down); crying faces go in the middle of the frame, lit, not at the edges in
  the dark.
- **No backs to the camera.** The camera never loses the characters, never
  ends up inside grass or a wall.
- **No black between parts**, no dead air at the joins.
- **Comedy timing:** instant interruptions, room for punchlines.

## Technical notes from the finale

- **Renderers:** `apply(E, t)` sets up one frame from time alone, so any frame
  renders in any shard. Anything measured once (for example a neck height)
  goes in a `prepare(E)` that runs on the first frame of *every* shard; a late
  shard that relies on state set by an earlier frame crashes.
- **Reuse between parts:** a part can import the previous part's builder
  (P12 -> P13 -> P14). `ep10_p7_reveal.cast` takes hooks (`steve_pose_hook`,
  `steve_face`, `noob_face_hook`, `force_shot`, `lip_frame` and more), so later
  parts change the acting without copying the scene.
- **CI** (`.github/workflows/render_episode.yml`, 40 shards, about 20 running
  at once):
  - `prep_from=<run id>` reuses that run's approved sound and timing.
  - `reuse_run_id=<run id>` with `new_range=a-b` re-renders only seconds
    a-b of a new-look part and keeps the rest of that earlier run's frames.
  - `assemble_from` re-runs just the assembly.
  - A shard that dies (a lost runner): wait for the run to end, then
    `gh run rerun <id> --failed`.
  - Stuck runs: `gh api -X POST repos/BagiTheKing/two-worlds-bot/actions/runs/<id>/force-cancel`.
  - Results: artifact downloads are blocked here; read
    `git show FETCH_HEAD:episode.mp4` from the `preview-<episode id>` branch.
  - Wait for runs with a background until-loop (`run_in_background`, timeout
    7200000); a background task is stopped after 2 hours, so restart it if a
    run is still going.
- **Cost:** one ~13 s part = 40 shards x about 1 hour = about 40 runner-hours
  at 1080p/64 samples. A 10-minute movie is roughly 1,500-2,000 runner-hours:
  at 20 at a time, about 4 days of non-stop rendering. Plan the order so the
  creator has something to review while the rest renders, and re-render only
  ranges (`new_range`) after notes.
- **Joining:** `tools/finale_join.py` cuts each part's silent tail and any
  trailing black, brings every part to -15 LUFS, and adds the badge and the
  to-be-continued card. For the movie, the same joining without the badge and
  card (`--no-card`, and drop the badge), or a movie version of it.
- **Thumbnails:** `tools/thumb_finale_series.py` (the series image with new
  lettering), `tools/thumb_finale.py`, `src/lookdev/ep10_thumb1.py` (a still
  staged from a part's scene). A long-form thumbnail is 1280x720 landscape.

## What changes for landscape (16:9)

Everything below assumes a vertical frame and needs a landscape mode:
- **Render size:** renderers set `resolution_x = res * 9 // 16`,
  `resolution_y = res` (`ep09_new.py`, `ep10_entrance.py` and the parts
  built on them). Add an aspect switch (for example `--aspect 16:9`) rather than
  forking the files.
- **Cameras:** every shot was framed for a tall frame (two characters stacked
  with Null above them, close-ups filling the height). In 16:9 each shot needs
  reframing: wider lens or further back, side-by-side staging, and the sky and
  world now fill the sides. Expect to revisit every camera, part by part.
- **Assembly:** `src/assemble.py` is fixed at `W, H = 1080, 1920`; captions sit
  at `caption_y` 1420; the watermark, badges and cards are placed for vertical.
  It needs a landscape layout.
- **Episodes 0-8** were made with the old kit (`src/kit/`, the Episode 0 rig).
  In the new look they are new renderers, as Episode 9's new-look section and
  the finale parts are. Their episode files (`episodes/ep00_the_end.json` to
  `ep08_steve_hiding.json`) still hold the lines, the timing and the sound
  design to start from.

## The plan

1. **Landscape pipeline, proved on one finale part:** the renderer aspect
   switch, the 16:9 assembly (captions, watermark), the part reframed shot
   for shot on its existing sound. Show the creator that part.
2. **Chapter by chapter, in story order** (Episode 0 first), each on its
   existing soundtrack: stills, preview, the creator's notes, full render,
   with the review gate before each send. Episodes 0-8 need new-look
   staging of their existing shots; Episode 9 and the finale are reframed.
3. **Join** the chapters in order (the Shorts packaging removed), one
   loudness pass, YouTube chapters, thumbnail, upload text.

Work one chapter per session where possible: each session reads this brief
and the chapter's files, so it starts clean instead of carrying a long
conversation. Update this brief at the end of each session with what changed
and what was learned.
