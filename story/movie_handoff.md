# The movie: handoff brief

> ## START HERE (a new chat, 2026-11-27 evening): the next job is Episode 8 (Episodes 6 and 7 are being finished in parallel)
>
> **Three chats are working at once.** Ep6 is finished on `claude/movie-ep06`, Ep7 on `claude/movie-ep07` (cut
> from Ep6). **Episode 8 works on its own branch, `claude/movie-ep08`, cut from `claude/movie-ep07`.** Before each
> push: `git fetch origin claude/movie-ep07` and merge it in (Ep7 merges Ep6 in, so you get both). Never push to the
> Ep6 or Ep7 branches. **Files you own:** `episodes/movie_ep08_*.json`, `src/lookdev/movie_ep08.py`,
> `story/movie/ep08_shots.md`, `movie/ep08*`. Shared sound code (`src/audio.py`, `src/music.py`) and tools: add to
> them, never change what an existing option does. One CI run at a time across all chats (`preview-logs` is
> overwritten by every voices run: copy what you need out of it as soon as your run ends).
>
> 1. Read the rules below (the Ep6 START HERE still holds for every episode: the loop, local stills, the
>    environment, no model names), then "Episode 7: how it was made" at the end of this file (**"What Episode 8
>    picks up"**), `story/movie/ep07_shots.md`, and the creator's Ep7/Ep8 notes
>    `story/movie/ep07_ep08_notes_2026-11-27.md` (points 1-3 are Ep8's).
> 2. **Ep8's published takes:** `movie/ep08_published` (rescued raw, prep of run **41851020512**; the published
>    episode is `episodes/ep08_steve_hiding.json`). Make it a `voices_from` folder first:
>    `git worktree add <dir> $(gh api repos/BagiTheKing/two-worlds-bot/actions/runs/41851020512 --jq .head_sha)`,
>    `python tools/rebuild_published_voices.py episodes/ep08_steve_hiding.json movie/ep08_published <dir>`.
>    The tool now lifts every line that is not in the scenes (`solo_only`, `solo_text` and `own_scene` lines) and
>    widens a solo's lift over the gaps beside it. Ep8 has four solos: the two screams (`steve_scream`,
>    `noob_scream`: probably cut, see below), "You had a PORTAL?!", and Steve's "I wanted to see the other side..."
>    (check `published_voice_log.txt`). Scene lines should come out near -80 dB residual, solos corr ~1.0. Commit
>    `voice.flac` only (delete `_work` and `timeline.json.rebuilt`).
> 3. **The creator's Ep8 fixes (from the Ep7 notes, 2026-11-27):** Ep7 ends with Patch's emergency warp dropping
>    them onto the grass in front of **Steve's hidden mossy obsidian portal**, which "eliminates Ep8's goofy
>    0:00-0:01 scream next to Null": cut the published screams; never show Null (his silhouette stays a surprise
>    until `ep10_part1_null_entrance`). The place and light match `video_2.mp4`: a moody Minecraft forest (tall
>    grass, lush foliage, distant snow-capped mountains), **late golden sunset** during Steve's confession, the sky
>    darkening and the sun dropping below the horizon right as the portal self-ignites at the end (0:27), lit by the
>    portal's magenta/violet bounce. No stray BTools hammer (the Noob lost it in Ep6) and Steve has no pickaxe (it was
>    erased in Ep6). No cheerful `:)` at 0:10 before "So all of this is your fault?". At 0:26, when they spin toward
>    the igniting portal: no harsh front light; dim ambient, the rim light only from the portal's purple emission.
>    **Sound:** the Memory Grid's dialogue was in a digital hall (`voice_hall`); Ep8 opens dry and outdoors (forest
>    wind and rustling leaves) so it feels "startlingly physical"; carry Ep7's warp chime tail over the cut.
> 4. Start by writing the 16:9 shot-by-shot plan for Ep8 (`story/movie/ep08_shots.md`) from the published episode
>    and these fixes, then the episode file, the voices-only CI run, the sound preview, then the renderer (import
>    `movie_ep07` once it is on the Ep7 branch, as Ep7 imports Ep6/Ep5).
> 5. Working rules (the creator's, 2026-11-26/27): don't ask the creator to approve steps (decide, say what you
>    chose, send each preview as soon as it is ready); keep the original takes for existing lines, new takes only for
>    added lines (`solo_only` + `new_take`); cheap local stills (360p, 8 samples, one per shot) before any CI render;
>    one CI run at a time; keep a turn running while a CI run renders and send the video when it lands.

> ## (earlier) START HERE: Episode 6 (Episode 5 was being finished in parallel)
>
> **Two chats are working at once.** Chat A finishes Episode 5 (its sound preview, stills, CI preview, notes). Chat B
> (you, if you were asked to build Episode 6) builds Episode 6. Rules so you don't collide:
> - **Branch:** Episode 6 works on its **own branch, `claude/movie-ep06`, cut from `claude/episode-3-sound-preview-kwg1rk`**
>   (which holds everything through Episode 4 plus Episode 5 so far). Before each push, `git fetch origin
>   claude/episode-3-sound-preview-kwg1rk` and merge it in, so you always build on Episode 5's latest picture and sound.
>   Never push to the Episode 5 branch. Never put a model name in commits or files.
> - **CI:** `preview-logs` is overwritten by every voices run, and the runner queue is shared. Start one run at a time,
>   and copy anything you need out of `preview-logs` (the sound preview) as soon as your run finishes.
> - **Files you own:** `episodes/movie_ep06_*.json`, `src/lookdev/movie_ep06.py`, `story/movie/ep06_shots.md`, `movie/ep06*`.
>   Shared code (`src/audio.py`, `src/music.py`, the rigs): add to it, never change what an existing option does.
>
> 1. Read, in order: `CLAUDE.md`, `story/creator_notes.md`, this file's last sections ("Episode 4: how it was made",
>    "Episode 5: how it was made", ending in **"What Episode 6 picks up"**), `story/movie/ep05_shots.md`.
> 2. The creator's standing rules for the movie now (2026-11-26): no reviewer-agent passes unless asked (CLAUDE.md's
>    gate is superseded by this); build carefully, render once, send every preview video as soon as it is ready;
>    re-render only what changed (`reuse_run_id` + `new_range`); a sound-only change with the same timing goes onto the
>    existing picture with ffmpeg (no render); cheap local test stills (360p, 8 samples, one per shot) before any CI
>    render; switch the session's network to the creator's **"two-worlds-bot"** environment and `pip install bpy
>    soundfile scipy`; never ask the creator to approve steps (decide, say what you chose; push back only if an idea
>    can't work); keep the original voice takes of lines that already existed, new takes only for added lines.
> 3. Local stills need the MCprep pack (allowed host in that environment):
>    `curl -sSL -o mcprep.zip "https://drive.usercontent.google.com/download?id=19RXVH0N1BIs_4OxtOooqqLpZ5jK_F1ZC&export=download&confirm=t"`,
>    unzip it, `ln -s <unzipped>/MCprep_addon/MCprep_resources <assets>/mcprep`; `python src/textures.py <tex>`; then
>    `python src/lookdev/movie_epNN.py <timeline.json> <voice.wav> <tex> <assets> <out> --times 1.0,5.0 --res 360 --samples 8`
>    (~50 s to build the scene, ~20 s a still). A timeline for stills before CI: build the sound locally (below).
> 4. The loop for an episode: the published Short (`preview-<id>` branch, `episodes/<id>.json`) and the creator's notes
>    -> the movie episode file `episodes/movie_epNN_<name>.json` -> voices-only CI run (`voices_from` = the rescued
>    takes) -> send the sound preview (m4a) -> the renderer `src/lookdev/movie_epNN.py` (import the previous chapter's,
>    as Ep5 imports Ep4) -> local stills -> one CI preview -> send it -> notes -> fixes by range -> a section here.
> 5. **The original voice takes** are no longer in the CI voice cache; they live in the repo. Episodes 4 and 5 are
>    finished `voices_from` folders (`movie/ep04_published`, `movie/ep05_published`). **Episodes 6-8 are rescued raw**
>    (`movie/ep06_published` .. `ep08_published`: the scene recordings, the published mix, timeline, voice log), saved
>    2026-11-27 straight from the Actions API before their preps expired. To make one a `voices_from` folder:
>    `git worktree add <dir> <the published run's head commit>` (Ep6: run 41223595607; get its `head_sha` with
>    `gh api repos/BagiTheKing/two-worlds-bot/actions/runs/41223595607 --jq .head_sha`), then
>    `python tools/rebuild_published_voices.py episodes/ep06_deleting_itself.json movie/ep06_published <dir>`. It runs
>    the published run's own sound code with the speech service replaced by the rescued scenes, places lines at their
>    exact times, and lifts the solo lines from the mix minus the exactly rebuilt bed. Check its report: the scene
>    lines' residual should be about -80 dB. If a line is missing from the scenes and is not `solo_only` (Ep6 has
>    Null's "...Hi?": check `published_voice_log.txt`), lift it the same way (add it to the solo handling).
>    **Local sound builds** (no speech key here): `VOICES_FROM=movie/ep0N_published` and stub `audio.gemini_solo` for
>    added lines (see `tools/` or the Ep5 section); the real new takes come from the CI voices run.
> 6. **CI was stuck on 2026-11-27** (runs queued for over an hour with no runner: GitHub's side). If runs are still
>    queued, keep working locally and check them again (`gh api repos/BagiTheKing/two-worlds-bot/actions/runs?per_page=6`).

> **Open corrections (2026-11-23): read `story/movie/fixes_2026-11-23.md`
> first.** The creator's fix list for chapters 0-2 (Ep0's fall restored, Ep1's
> walk cut, Ep2's zombies, block, tree and a new dragon ending) and what it
> changes in chapter 3.


> **Episode 4 is built (preview, 2026-11-27): read "Episode 4: how it was made" at the end of this file before Episode 5.**
> **Episode 3 is built (v3, 2026-11-26): read "Episode 3: how it was made" at the end of this file before Episode 4.**
> Work continues from branch `claude/episode-3-sound-preview-kwg1rk` (it holds everything through Episode 3).

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


## Episode 3: how it was made and what it taught us (2026-11-25)

**State.** Ep3 v2 (the creator's notes on the published Short, 2026-11-25; the story in `story/movie/ep03_shots.md`,
"v2"). Sound approved: `movie/ep03_v2` (58.3 s; voices run 45628706087 + 45631569353). Renderer
`src/lookdev/movie_ep03.py`; episode file `episodes/movie_ep03_the_dragon.json`. Preview: CI run 45649852160 (`preview-movie_ep03_v2`), its
first 0.5 s re-rendered by the next run (`preview-movie_ep03_v2b`: the one to use). With it: Ep2 v7 (the v6 picture, the buzz-free sound `movie/ep02_v7`, the dragon's new skin
and the lens flare from 48.7 s, reusing run 45519397363) and Ep1 v9 (the rift with its magenta edge from 24.9 s,
reusing run 43968500715, `preview-movie_ep01_v9`; the v8 cut of the walk, 3.0-5.0 s, re-applied locally with ffmpeg
(a 60 ms audio crossfade), 28.8 s). Ep2 v7: `preview-movie_ep02_v7`. All sent to the creator; awaiting their notes.

**The join Ep2 -> Ep3.** Ep2 ends on a violet-white flare washing the lens as the dragon's head enters the portal
(`movie_ep02.lens_wash`/`set_wash`, 0.72 at most); Ep3 opens on the same wash clearing in 0.45 s into the tumble
through the swirl. Ep2's last cue now runs to the cut (`"sustain": true`; it used to die 2.6 s after its hit, so the
run and the dive had no music); Ep3 carries it on exactly (`dread`, smooth, seed 7, `offset` 6.46, `hit_at` 0.05,
`rise_over` 6.46: the same heartbeat and the same rise). Ep3's last cue is `open_tail` for Ep4.

**Sound lessons.**
- The "buzz" the creator kept hearing was the creature voices: `zgroan` and `droar` were stacks of 30-40 harmonics on a
  low pitch. Both are now breath through a throat (formant-filtered noise, a faint sine voice): no buzz. The square
  plucks/lead of `chase` and the saw `braam` hits have buzz-free versions (`"smooth": true` on `chase`, `dread`,
  `rumble_rise`; `music.boom`). Check a spectrogram for wavy harmonic stacks before sending.
- New: `glass` (crystal shatter), `"stutters"` (the whole mix freezes: a 70 ms slice repeated, then silence; the voices
  kept), `"cut"` on any sfx (stopped dead at a moment: anything still sounding at a freeze). `sfx_glitch` has a 1.5 s
  tail: cut it for a short tick.
- `own_scene` acted takes read their direction aloud for short Noob lines ("Cheerful wave, then puzzled..."): record
  short lines `solo_only` with plain `solo_text` instead. Mark lines taken in a run with `taken_in`, not `new_take`, or
  every rebuild calls the voice service.
- A sound-only fix to a chapter with unchanged timing goes straight onto the existing picture with ffmpeg (no render).

**Picture lessons.**
- Measure the rig before staging it: the dragon's head is 3.6 m ahead of its root (not 5); its wingspan is ~15 m; its
  heading vector is `(sin(yaw), -cos(yaw))` for this codebase's yaw (0 faces -y). Probe positions with a small script
  (`build` + `apply` at the key times, print the head, the seat, the cameras) before rendering: one probe found both a
  wrong heading and the wrong head offset.
- Contact moments are keyed from the contact: the wall hit, each crystal, the kill and the landing on its back are
  solved from where the head or the seat must be at that time (`_seat_at` poses the dragon at the landing time).
- A character looking at something on the far side of the set shows its back to every camera on the near side:
  shoot those moments as a reverse angle from the thing looked at (the frozen player's view from the ledge).
- Keep the scenery clear of the cameras' side (the course ahead was first in front of two cameras) and keep anything
  that flies (kicked cobblestones) clear of close cameras.
- A world for the obby: `part()` (studded plastic, `rbx_neon` for kill bricks and checkpoints), `_far_world` (towers,
  trusses, spinners, kill paths, checkpoints in the haze), `_clouds` (puffs round it, a sea below); mist from 30 m.
- The freeze reads in-world: full beats and a roar, then a stutter back twice (`freeze_time`), wings locked mid-flap,
  debris hanging, the camera's handheld stopped, the sound stuttering into silence.
- 360p, 8 samples is ~15-20 s a frame here; one still per shot (33) is ~10 min. Two or three rounds of stills caught
  every staging fault before the CI render.

**v3 (2026-11-26).** The creator prefers the old takes of the old lines (BOSS FIGHT!, It used our portal. Hide!,
Tutorial says jump!, Don't-, Checkpoint!, Worlds don't lag.); the four added lines keep their new takes. Sound
`movie/ep03_v3` (built locally with `--keep-timeline movie/ep03_v2/timeline.json`: the same beats, the old takes placed
at the v2 line starts), the six line spans re-rendered for lip sync on top of run 45667919167 (`preview-movie_ep03_v3`).
Rule from this: **a line that existed before keeps its original take unless the creator asks for a new one**; "more
energy" notes go to new lines, music and foley, not to re-recording approved lines.

**What Episode 4 picks up.** Ep3 ends on the frozen dragon flickering into the missing texture over the spawn pad,
the Noob lying on its neck, Steve below looking up, REALITY 92%, the portal still flickering behind them. The last cue
(`dread`, minimal, smooth, hit at `glitch`, `open_tail`) is silent from 2.6 s after its hit: Ep4 opens on that
silence and the sub drop's tail (carrying it on is `offset` 3.0, nothing left to hear). The published Ep4 ("This Block
Shouldn't Exist", `episodes/ep04_the_block.json`, `preview-ep04_the_block`) opens with the dark block "fell off the
dragon": show it falling off the frozen, glitching dragon at Ep3's place (the obby world of `movie_ep03.py`, which Ep4's
renderer can import: `build`, `part`, `_far_world`, the cast). Patch arrives in Ep4: he must be seen coming from
somewhere (nobody from nowhere). The dragon's fate after the freeze is open: decide it on screen, don't leave it hanging.


## Episode 4: how it was made and what it taught us (2026-11-27)

**State.** Sound `movie/ep04` (53.2 s; voices run 45910763547; all 15 lines pass the hearing check), sent to the
creator. Renderer `src/lookdev/movie_ep04.py`; episode file `episodes/movie_ep04_the_block.json`; shot list
`story/movie/ep04_shots.md` (the decisions, the places, every shot). Picture preview: CI run 45915425874 (720p, 20
samples) -> `preview-movie_ep04`. With it, the creator's two Ep3 seam notes as range re-renders on Ep3 v3 (run
45907642735): the missing texture held over Ep3's last 8 frames (Ep4 opens on it) and the cloud behind the dragon's
head lifted in the burst shot only: run 45915682288 -> `preview-movie_ep03_v3b`. If those runs are still queued
or failed when you arrive, check them (`list_workflow_runs`), rerun failed shards, and send the videos.

**The story as built (the creator's ~60 s blueprint, 2026-11-26).** Ep3's last instant goes on; one last
missing-texture shudder; the block rips out of the dragon's chest (sparks), lands on the blue terrace; the Noob is
flung off and belly-flops onto a spawn ring that lights (a checkpoint). The dragon's fate: the glitch crystal that
held the frozen players seals it in the sky. "A secret block!" / "It fell off the dragon. Don't touch it." Two
touches (poke; "Again!" karate chop): zap, burst, one dark cube drifting off (the bible's planting rule: kept, one
per death, off-centre), respawn with squash and stretch, a tether from the ring into the cube, a shockwave, the cube
0.45 -> 0.85 -> 1.45 m, REALITY 92 -> 89 -> 85 (one drop per respawn), the hum deeper each time. Patch squeezes out
of the portal (a cyan warp: seen coming from somewhere), stops between the fist and the cube: "Please stop doing
that." Steve jumps back into a guard; "A talking cube!"; "I'm Patch. I find glitches." (added: he is named); the
scan from the front right (a clear line, nobody in the beam); "It's feeding on your respawn loop." (the creator's
line) "It grows every time you come back." "So I'm helping!" "No." (music cut dead). The twist in silence: Patch's
eye dilates with a scanline glitch, "Wait. I know you." "...You do?" "From a world that got deleted." (a low swell,
one high note, ringing into Ep5); hold on the Noob's stunned face, Steve's glance.

**Sound lessons.**
- **The voice cache forgets.** Ep4's published takes had gone from the CI cache (the run stopped with
  `voices_cache_only`, as it should, instead of recording new ones). The published run's `prep` artifact (30-day
  retention) held the raw scene recordings (`build/scenes/<first line>.wav`), the mix and the timeline, but no
  voices-only stem (that came on Nov 7). It was saved an hour before expiry: the workflow now copies any
  `voices_from` prep into `preview-logs` (`prev_prep/`), so a voices run with `voices_from=<old run id>` rescues it.
  Episodes 5-8's preps must be rescued the same way into `movie/ep0N_published` (raw): see START HERE for the run
  ids and the deadlines.
- **Rebuilding finished takes from a rescued prep** (`movie/ep04_published`, made locally): run `audio.build` on the
  *published* episode file with `--keep-timeline`-style `keep=<its timeline>`, `gemini_speak` patched to return the
  matching `scenes/<first line>.wav` (lines with `cut_at` are cut exactly as published), `split_scene`/`cut_lines`
  stubbed (Whisper's model host is blocked here; pinned cuts don't need it). Solo takes are not in the scenes: lift
  them from the published mix and subtract the bed (rebuild it with the same code and timeline, placeholder voices
  of the right spans, capture `keep_under`'s output, fit its gain on voice-free windows, Wiener-style spectral
  subtraction). The bed sat 20-27 dB under the solos. Check every line by cross-correlation with the published mix
  (0.73-0.99 here). Save `voice.flac` + `timeline.json`: that folder is a `voices_from`.
- Cache keys: a scene's key is its turns (speaker, direction text) and voices, grouped as consecutive lines with at
  most two speakers; solo lines (`solo_only`) are left out of scenes. Added lines must be `solo_only` + `new_take`
  so the old scenes group exactly as before. A line to replace keeps its place marked `unused` (still recorded with
  its scene, never placed) and the new take is a new line (Ep4's `noob_touched` -> `noob_touched2`). A different
  `solo_text` ("I touched it!!") forces a fresh recording. `new_take` solo lines now get all their takes even in a
  cache-only run.
- Takes reused from `voices_from` are placed "finished": per-character effects must be applied there too (Patch's
  `fx: "patch"` chain was missing on his reused lines at first).
- New sound code: Patch's voice (`cast.fx = "patch"`: 180 Hz high-pass, a 19 ms metallic slap and a slow flanger,
  ~10% wet; `patch_soft` on a line, 5%); sfx `hum` (`semi`, `sub`), `zap`, `siphon` (`big`), `ping`, `trill`,
  `warp`, and `crackle`/`land`/`fall` exposed; music `bounce` (light marimba comedy), `curious` (Patch), `deleted`
  (sub swell, one high note); music `mutes` (drops out dead on a gag, the groove keeping time underneath).

**Picture lessons.**
- **Picking up a chapter exactly:** import the previous renderer, build its world, and pose its last instant by
  swapping its beat table into `B` (`_use(E, 3)` ... `_use(E, 4)`; only one beat name collided). Measure what you
  need once in `prepare(E)` (the frozen pose, the Noob's seat, the last camera) and keep `apply` time-only.
- **Update order:** anything a character looks at must be posed before the character (Patch before Steve and the
  Noob), and anything that uses the camera's position must get this frame's (compute `_cam` first). Stale
  positions turned Steve's back to the camera.
- **Props in hands block faces:** Steve's pickaxe with a bent elbow sits in front of his face from most front
  angles; keep the elbow low (10-35) for a "ready" grip.
- **Cameras:** check each against every large prop's box (one camera sat inside the grown cube) and against hanging
  debris; for an over-the-shoulder, put the camera well back (3.4 m), well to the side (1.25 m) and high (+0.75 m)
  so the near head is small in the lower corner. A locked master shot for a growing prop gives the viewer a ruler.
- A crystal shell over a posed rig: link each mesh's data to a new object with an object-level material, place it
  at the posed matrix scaled ~1.07 about its centre, reveal by distance from the root.
- 360p/8-sample stills: five rounds (25 + 17 + 10 + 4 + 2 stills) caught every staging fault before the CI render.

**What Episode 5 picks up.** Ep4 ends on the twist: the Noob (REACT_N, -6.95, -0.8) stunned, Patch (-5.45, -3.0,
1.85) facing him, eye dim, the 1.45 m glitch block hovering at the terrace's front corner, Steve on the grey pad's
edge (-2.1, -1.3), the dragon sealed in crystal over the spawn pad, the portal flickering, REALITY 85%, the
`deleted` cue ringing (open tail: carry it on). The published Ep5 ("Noob Found Creative Mode",
`episodes/ep05_creative_mode.json`, `preview-ep05_creative_mode`) opens on "I can BUILD stuff!" / "Since when?" /
"Since the block!": **show on screen how the block gives him the power** (it is right there, huge, fed by him: he
touches it a third time and it pours into him instead of killing him, or it shatters into him). Then the statue,
the castle, the door, the duck (one of the Noob's builds: in the Short it is built on its own pad before the castle; show him building it so its vanishing lands), Patch's "It's not
you. Something is deleting what doesn't belong.", the wave, REALITY to 71% (the movie meter, one drop per event).
The same obby world (`movie_ep04.build` / `movie_ep03`), the same rigs and Patch (`patch.py`). Its takes:
`movie/ep05_published` (rescued raw: rescue it first if missing; then build the `voices_from` folder).


## Episode 5: how it was made (2026-11-27, in progress)

**State.** Episode file `episodes/movie_ep05_creative_mode.json`; sound `movie/ep05` (55.65 s, voices run 45918732916,
13/13 lines pass the hearing check), sent. Renderer `src/lookdev/movie_ep05.py`; three rounds of local stills; CI
preview runs 45922474466 (one shard crashed: a camera used state from the previous frame) + 45930883334 (range
5.37-7.05 on top) -> `preview-movie_ep05`, sent to the creator 2026-11-27. Awaiting notes. Lesson: `_cam` must never
read state set by an earlier frame (shards start anywhere). Shot list `story/movie/ep05_shots.md` (the decisions, the places, every shot).

**The voice rescue that worked (for Ep6-8).** The prep artifacts download straight from the Actions API
(`download_workflow_run_artifact` gives a signed URL on a `productionresultssaN.blob.core.windows.net` host; the
environment allows sa5, sa16, sa30, sa31). Rebuilding with the *published run's own code* (a worktree at its head
commit) and the lines at their unrounded times makes the bed bit-exact (-80 dB residual), so the solo lines lift out
cleanly (corr 0.999). With today's code or a rounded timeline the bed is off (Ep4 needed Wiener subtraction).

**Sound lessons.**
- New: `erase` (the one deletion sound: bit-crushed tear, inward suction, 60 -> 30 Hz vacuum, cut dead; `size`),
  `btool` (click-lock, scan, pop by `size`), `slam`, `door` (hinge creak, no crack), `gust` (wind through a doorway);
  `"stutters": [{"at": .., "n": 0, "silence": 0.15}]` gives 0.15 s of dead air after an erase.
- A reused take can be lifted without re-recording: `presence` (dB at 2.5-4 kHz) and `gain_db` on the line.
- Carrying on the `deleted` cue: `offset` = the seconds already heard, and `fall_at` (cue time) so its note stays
  fallen. The master level is set per chapter from its dialogue: match the carried cue's gain to the previous
  chapter's last second at the cut (Ep5 needed 0.62 vs Ep4's 0.3).

**Picture lessons.**
- The grey spawn pad is under the sealed dragon's crystal and the hanging cobblestones: nothing goes on it.
- One erase material (`erase`: object attributes `e_hi`, `e_cut`, `e_line` read from custom properties; the colour
  from the object colour) builds and erases everything: swap the slots to it (link OBJECT) for the window, restore after.
- Studio's selection box is `roblox.Gizmos` (`mode: "snap"`, `k` > 0.5 = the white first frame).
- The Noob's hand tool: a child of `E.N.arms["sr"]` at (0, -0.05, -1.38), handle along -y (arm space): raised it
  stands up, lowered it points forward (never behind the hip).

**What Episode 6 picks up** (from `movie_ep05.py`'s last instant; confirm against its final version before staging):
- **Where:** Ep3's obby with the course erased: the five stones west of the terrace, the orange stepping stone,
  the checkpoint (pad, flag), the truss tower and its high stage are gone. Left: the grey spawn pad, the blue
  terrace with the violet ledge (castle gone), Ep4's white spawn ring (empty: the duck was erased), the **door**
  standing open at the terrace's front edge (hinge (-8.08, -2.2), opened 95 degrees over the drop), the **dragon
  sealed in crystal** over the spawn pad, the portal flickering behind, the far world in the haze. The sun 25% dimmer
  and cooler.
- **Who:** the Noob on the terrace near (-5.4, -1.3) (`N_BUILD` + (-0.05, 0.25): he recoiled from the edge), scared, the BTools hammer in his
  right hand; Steve at (-2.35, -1.2) (`STEVE_D`) facing the Noob, flat brow, after "...That wasn't us."; Patch near
  (-7.1, -1.7, 2.6) looking at the Noob. REALITY 71%.
- **Sound at the cut:** the void wind (ambience `void`, 0.05) and a faint `drone` (seed 4, gain 0.07, `open_tail`,
  from `stairs_gone+1.2`): carry it on with `offset`.
- **Ep6's published opening** (`episodes/ep06_deleting_itself.json`, `preview-ep06_deleting_itself`) erases the
  dragon, then the duck's pad and the door: in the movie that is the sealed dragon, the empty spawn ring and the
  door, **by Ep5's erase rule** (import `movie_ep05`: `_erase_material`, the `erase` sfx), REALITY ticking down from
  71. Then "The world is DELETING itself!" / "Then we stop it." / Patch's "Oh no." / the pickaxe, the wall, the TNT
  erased in turn ("...My pickaxe.", "Wall!", "...No wall.", "It deleted the BOOM!") / "It's not attacking. It's
  correcting." / the face: Null's first "...Hi?" copying the Noob's / "Someone is watching... you." Null is new on
  screen: he must be seen coming from somewhere (the bible: he is made of the Noob's respawned bodies; the dark cubes
  that drifted off at each of Ep4's deaths are the planted clue).


## Episode 7: how it was made (2026-11-27, in progress)

**State.** Branch `claude/movie-ep07` (cut from `claude/movie-ep06`). Voices: `movie/ep07_published/voice.flac` rebuilt
from run 41463846907 (scene lines -78..-87 dB; the solos "From last time." (`solo_text`) and "I don't want to be
deleted." (`own_scene`) were missed by the tool at first: it now lifts them). Episode file
`episodes/movie_ep07_another_world.json` (~51.5 s, local build); shot plan `story/movie/ep07_shots.md`; a local sound
preview `movie/ep07/ep07_sound_preview_local.m4a` (Patch's one new line a placeholder). Next: the voices-only CI run
(the new take), the sound preview, the renderer `src/lookdev/movie_ep07.py`, stills, the CI preview.

**Sound additions.** `voice_hall` (episode): a wide digital hall on the dialogue (`decay`, `wet` as a plugin-style mix,
`hp`, optional `from`/`to`), added after the ducking. Ep7 uses decay 1.1, wet 0.13, hp 250, to the breach.

**What Episode 8 picks up** (confirm against `movie_ep07.py`'s final version and the CI timeline before staging):
- **The cut:** Ep7 ends on a full white-cyan flash (Patch's emergency warp out of the cracking Memory Grid), held
  ~0.3 s. Ep8 opens on that flash clearing onto the grass in front of Steve's hidden mossy obsidian portal, late
  golden sunset (the forest of `video_2.mp4`). Never the obby, never Null.
- **Who:** Steve (empty-handed), the Noob (no hammer; scared, worried brows: he just said "I don't want to be
  deleted."), Patch (his eye flashed amber on "It found the archive- I only have one stable coordinate left!", then
  flared cyan for the warp). They should arrive like in Ep7: tumbling out of the warp, not popped in standing.
- **Sound at the cut:** Patch's warp chime (sfx `chime`, pitch 1.25, gain 0.6) hits on the flash, ~0.3 s before
  the cut (`flash` beat): carry its tail on (`at: -0.3`; take the exact offset from Ep7's CI timeline). Under it a
  rumble rise and crackle from the breach; the `memory` cue was cut dead at the breach (no music to carry). The
  voices were in a hall: Ep8's are dry, outdoors.
- **REALITY 30%** at the end of Ep7 (the published Ep7 ended at 30% too).
- **Story link:** "one stable coordinate left" = the place Steve's first portal stands: Ep8's confession ("I built
  the first one. Before I met you.") pays it off; Steve's guilty glance in Ep7's shot 9B foreshadows it.


## Episode 8: how it was made (2026-11-27, in progress)

**State.** Branch `claude/movie-ep08` (cut from `claude/movie-ep07`). Voices: `movie/ep08_published/voice.flac` rebuilt
from run 41851020512 (all lines lag 0, corr 1.000; the residual floor is ~-40 dB here, the same in voice-free stretches:
the mix's level fit, inaudible). Episode file `episodes/movie_ep08_steve_hiding.json`; shot plan
`story/movie/ep08_shots.md`; sound `movie/ep08` (61.24 s, voices run 46064416479, 9/9 lines pass the hearing check;
`ep08_sound_preview.m4a` sent). One new take: Steve's "...I didn't do that." (the published line was Patch's: kept
`unused`); the screams cut. Next: the renderer `src/lookdev/movie_ep08.py` (import `movie_ep07` once it exists; the
set is the finale's forest clearing, `ep10_part1_null_entrance`'s builder), local stills, one CI preview.

**Sound additions.** Ambience `evening` (breeze through oaks, leaf rustle on the gusts, crickets fading in: `crickets`
[start, end] level, its own seeded generator); the ambience lookup is now a table (`AMBIENCE`; `meadow` and the void
wind unchanged). Sfx `obsidian_boom` (45 Hz THOOM, leaves rattling), `plasma_hum`, `plasma_crack`, `stone_groan`
(the J-cut into Null's claws, 0.25 s before the end), `flint`, `vines`.

**What the finale picks up:** Ep8 ends on shot 5B, the blazing violet portal on the finale's opening camera plane,
the magenta crack, the stone groan already sounding: hard cut to frame 1 of `ep10_part1_null_entrance`. REALITY 12%.
