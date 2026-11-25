# The movie: handoff brief

> **Open corrections (2026-11-23): read `story/movie/fixes_2026-11-23.md`
> first.** The creator's fix list for chapters 0-2 (Ep0's fall restored, Ep1's
> walk cut, Ep2's zombies, block, tree and a new dragon ending) and what it
> changes in chapter 3.


> **Episode 2 is done (v6, 2026-11-25): read "Episode 2: how it was made and what it taught us" at the end of
> this file before Episode 3.** Work continues from branch `claude/episode-2-sound-preview-b8mxtd` (it holds
> lookdev-steve plus all of Episode 2).


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

**Start with Episode 0, now.** No pilot on a finale part, no proposal round:
the creator wants the movie built in story order, Episode 0 first, then
Episode 1, Episode 2 and so on to the finale. The landscape setup is built
as part of Episode 0 itself.

1. *(removed: there is no separate landscape test.)*
2. **Episode by episode, in story order, starting with Episode 0**, each on its
   existing soundtrack. **Before building anything for an episode or part,
   study the published version frame by frame:**
   - get it from its `preview-<episode id>` branch (`git show
     FETCH_HEAD:episode.mp4`, and its `timeline.json`);
   - look at every frame of it: contact sheets at 8 frames a second or more,
     time-stamped (`tools/review_part.py <dir> <mp4> --every 0.125` makes
     them, plus the first and last frame of every shot), and full-size frames
     wherever the action is fast;
   - write a **shot list** in the repo (`story/movie/<episode>_shots.md`):
     for every shot, its start and end time, who is in frame and where, what
     they do, the line being said, the faces, the camera (distance, angle,
     movement), the props and effects, and the sound cues;
   - build the remake to that shot list, shot for shot on the same timing,
     and compare your stills with the original frames side by side before
     sending anything.
   Then: stills, preview, the creator's notes, full render, with the review
   gate before each send (the reviewer gets the shot list and the original
   frames too). Episodes 0-8 need new-look
   staging of their existing shots; Episode 9 and the finale are reframed.
3. **Join** the chapters in order (the Shorts packaging removed), one
   loudness pass, YouTube chapters, thumbnail, upload text.

Work one chapter per session where possible: each session reads this brief
and the chapter's files, so it starts clean instead of carrying a long
conversation. Update this brief at the end of each session with what changed
and what was learned.


## Episode 2: how it was made and what it taught us (2026-11-25)

**State.** Ep2 v6 preview (720p, 68.1 s): run 45519397363, branch `preview-movie_ep02_v6` (`episode.mp4`).
Sound and timing: `movie/ep02_v6` (audio.flac, voice.flac, timeline.json, voice_log.txt). Earlier versions kept
in `movie/ep02` (v4) and `movie/ep02_v5`. Renderer `src/lookdev/movie_ep02.py`; episode file
`episodes/movie_ep02_the_plan.json`. The creator's notes on it are in `story/movie/fixes_2026-11-23.md` (all of
them, word for word) and the standing rules they set are in `story/creator_notes.md` ("Notes from the Episode 2
v5 previews"). The faults caught on the way: `review/ep02_v5_failures/`. Awaiting the creator's verdict on v6.

**Still open, before Episode 3 is joined:**
- Episode 1's last shot shows the sky rift; its edge is now magenta (`movie_ep01._crack`, shared): re-render Ep1's
  last ~2 s so the Ep1 to Ep2 join still matches.
- Episode 3's opening must pick up Episode 2's new ending: Steve and the Noob dive into the swirling portal (it
  stays open), the dragon (scale 0.95, wings folded) plunges in after them, a violet ripple on the surface, cut on
  the swirl. Ep3's "Through" opening becomes only the tumble and the landing on the Noob's side, the dragon
  bursting through after them ("It used our portal"). Ep3's sound must carry on Ep2's last cue: `dread`
  (smooth, seed 7, gain 0.24), already 6.46 s in at the cut (`offset: 6.46`), not Null's theme (gone from Ep2).

**How we work now (the creator, 2026-11-25):**
- Credits matter: build carefully, render once, send the video. No reviewer passes unless the creator asks; the
  creator watches every preview themselves (send each preview video, even a failed one; never hide one behind
  a verdict). Re-render only what changed (`reuse_run_id` + `new_range`).
- Before any CI render: local test stills (Blender is pip-installable here: `pip install bpy`; the MCprep pack
  comes from Google Drive, so switch this session's network to the creator's "two-worlds-bot" environment).
  360p, 8 samples is about 15 s a frame; `tools/contact_sheet.py <frames_dir> <out.png> 3` makes a labelled sheet.
- Sound first (voices_only, ~4 min), then the picture.
- When the creator gives solutions, use them; push back only where one can't work, and say why.

**Pipeline additions (src/audio.py, src/music.py, the workflow):**
- `voices_from` may be a repo folder (e.g. `movie/ep02_v6`): every finished line reused exactly. A line marked
  `"new_take": true` is re-recorded (Gemini) even if the folder has it; nothing else is.
- Gemini reads `[directions]` aloud on short shouted lines: record them `solo_only` with `solo_text` in capitals
  (e.g. "DON'T!", "INTO THE PORTAL! NOW!") and `"shout": 3-4` (rumble cut, 2.5-4 kHz presence, a little drive,
  louder). Check the voice log's hearing check after every voices run.
- `"voice_air": 0.12` (episode): a short outdoor reflection on the voices (no dry studio sound).
- `"deess": 6` (line): harsh s sounds softened. `clean_tail` now removes end-of-take bursts split by digital
  silence (the "tchch").
- Foley (sfx kinds): `gstep` (grass step, `heavy` for creatures), `zgroan` (zombie groan, voice-like),
  `clink` (pickaxe), `shatter` (stone and plastic breaking), `wingbeat` (huge wings), `droar` (the dragon's roar,
  breathed). Old synth sounds (`whir`, `growl`, `roar`, `flaps`) read as a "distorted synth buzz": don't use them.
- Music: `drone` cue (a serious low bed); `dread` with `"smooth": true` (no square-wave buzz). Rules: no upbeat
  track under a serious line, silence for comic pauses, tension (not a bouncy groove) for a chase.

**Renderer lessons (every one cost a render):**
- `apply(E, t)` must depend on time alone: anything remembered from an earlier frame (a grab position, a toss
  start, a last yaw) breaks on CI shards. Compute such things from time once (see `_cling_root_at_grab`,
  `_toss_from`).
- Call `bpy.context.view_layer.update()` after posing a rig whose matrices others read in the same frame (the
  dragon's head for the held zombie, the looks, the cameras).
- Cameras: never follow a character's facing or a moving head (they jump when the character turns, or end up
  inside the body). Anchor close-ups to fixed spots (where they stand, where the target is at the shot's start).
  Check every camera for backs, blockers (another character's head, a bush, a column) and the 180-degree line.
- Staging: place characters so that nobody stands in another's line to what they look at; keep them 1.4 m apart;
  check clearances numerically (`tools/clearance_ep02.py` checks a creature's oriented part boxes against the
  trees, the portal, the characters and the ground); fold wings near trees and openings.
- Path keys must not reverse direction where the heading comes from the velocity (the dragon flipped 180 degrees
  at the snatch); hold a heading explicitly for such moments.
- Lighting: when a camera looks at the sky, aim the key at the characters (else faces go dark red); after the
  portal opens, keep its violet light off faces; a soft camera-side fill keeps skin its own colour.
- Life: `life()` adds drift, accents on stressed syllables (from the lip-sync), blinks; never a stiff A-pose;
  walking speed matched to the stride (feet planted); impacts get anticipation, a 3-frame snap, a 2-frame
  hit-stop and a camera shake.
- Clarity: one event at a time (stagger by 0.5 s); props that matter readable (less motion blur: shutter 0.28);
  materials matte and textured like the world.
