# Episode 3 "The Dragon Entered an Obby": shot list for the movie remake

The source is the published Short, `preview-ep03_the_dragon` (`episode.mp4`,
1080x1920, 24 fps, 26.58 s, `timeline.json`). I studied it frame by frame
with time-stamped contact sheets every 0.125 s and the first and last frame
of every shot (`tools/review_part.py ... --every 0.125`). The definitions
are in `episodes/ep03_the_dragon.json` (`shots`, `clips`, `fx`, `actors`).

**The remake:** the same lines and voice takes, re-staged in 16:9 in the
new look. The creator allows more time ("no restrictions on time ... as
long as the quality is good and the story make sense", November 14), with
"same lines, more room". The movie's episode file is
`episodes/movie_ep03_the_dragon.json`, and its sound preview comes before
any frame.

**The place:** the Noob's obby. In the movie it is the obby half of the
finale's egg island, the same parts and colours as Episode 0's obby, so the
viewer recognises it. Four frozen players stand in glass cases on a ledge
above the course.

## What stays and what goes

| Published | Time | Movie |
|---|---|---|
| "EPISODE 3 / THE DRAGON ENTERED AN OBBY" label | 0.30-3.95 | **dropped** (an episode card) |
| The game's TUTORIAL panel "JUMP ON THE BOSS!" with its arrow | 4.05-6.30 | **kept**: it is the obby speaking, and the Noob's line answers it. Landscape layout |
| "WOULD YOU JUMP? COMMENT ↓" | 4.35-7.65 | **dropped** (a Shorts comment prompt) |
| PLAN timer, failing at 0.80 s on the crash | 10.80-12.40 | **kept**: the joke from Episode 2 comes back |
| The white flash on the crash | 11.60-11.72 | **kept** |
| Achievement "ACCIDENTAL HERO / Free the frozen players" | 15.88-17.73 | **kept** |
| REALITY 97% → 92% (pink) on the glitch | 0-24.66 | **kept** as the movie meter: it glitches in for the drop at the glitch |
| End card (Episode 4, "WHO FROZE THE DRAGON?") | 24.66-26.56 | **dropped** |
| Captions, watermark | throughout | **kept** |

## The join with Episode 2

Episode 2 ends with the portal snapping shut, empty. Episode 3 opens on the
dragon bursting into the obby. Steve's line "It used our portal" ties them:
the dragon came through the portal they built. The movie makes that
readable by opening on the obby's sky tearing open the same way the portal
flashed (the same white flash, the same snap sound family) as the dragon
comes out of it.

## Shots (published times; the movie's come from its sound preview)

### 1. The dragon arrives (0.00-1.67) · `open` + "BOSS FIGHT!"
- **Vertical:** low and wide on the obby: the dragon swoops down over the
  course, wings spread, bits of a smashed part flying. The Noob, centre,
  jumps with his arms up ("BOSS FIGHT!"). Steve stands small at the left
  by the frozen players' cases. The camera tilts up as the dragon passes
  over (1.0-1.6).
- **16:9:** the whole obby wide, with the dragon diving in from the top
  right. It smashes a part (`smash_near`: three parts burst). The Noob is
  thrilled at the centre, Steve at the left, the four cases behind him. In
  the movie the arrival gets 1.6 s instead of 0.25 s before the line: the
  roar, the dive, the parts breaking.

### 2. "It used our portal. Hide!" (1.67-4.05) · `steve_hide`
- **Vertical:** Steve medium, facing the camera, the cases behind him at
  the left. Flat and deadpan. A small turn on "Hide!".
- **16:9:** Steve on the right third, the cases and the obby behind him,
  the dragon's shadow passing over. A deadpan face, brows level and apart.

### 3. The tutorial (4.05-6.30) · `tutorial` + "Tutorial says jump!" + "Don't—"
- **Vertical:** wide: the Noob on the blue part at the right, Steve at the
  left edge, the dragon circling above. The TUTORIAL panel pops in with an
  arrow pointing up at the dragon. "Don't—" is cut off by the jump.
- **16:9:** the two of them on their parts left and right, the dragon
  circling, the panel above the Noob. The Noob reads it, delighted; Steve
  alarmed, a hand out.

### 4. The jump and the kill (6.30-7.65) · `jump` + `kill`
- **Vertical:** the Noob leaps from the red part toward the dragon (6.4).
  The dragon sweeps through him and he bursts into pieces (7.25), with the
  dark cube in the burst (Episode 2's hint again).
- **16:9:** side on: the leap, the dragon's sweep across the frame, the
  burst. More time in the movie (1.4 s jump, 0.7 s kill) so the burst
  reads.

### 5. "Checkpoint!" (7.65-9.17) · `respawn` + `noob_cp`
- **Vertical:** close on the checkpoint pad: the Noob pops in and cheers,
  arms up. The dragon wheels behind him.
- **16:9:** the Noob centre on the pad by the flag, unbothered, the dragon
  in the sky behind. The same respawn pad as Episode 2.

### 6. "Plan: wall." (9.17-11.62) · `steve_wall` + `build`
- **Vertical:** wide, low: Steve on the green part places cobblestone
  blocks in front of himself, a small 3x2 wall. The PLAN timer starts
  (10.80). The dragon comes in from the right (11.1).
- **16:9:** Steve side on at the left, the wall going up block by block
  with a place sound each, the dragon arriving from the right of frame. The
  timer counts.

### 7. The crash (11.62-11.69) · `crash`
- **Vertical:** the dragon smashes through the wall: a flash, the blocks
  flung, "PLAN FAILED: 0.80s" in red.
- **16:9:** the wall bursting toward the camera, the flash, Steve ducking.
  In the movie it gets 1.0 s: the blocks tumble and land.

### 8. The leap onto the dragon, "Tutorial complete!" (11.69-13.92) · `leap` + `noob_done`
- **Vertical:** wide over the course: the Noob jumps from the checkpoint
  pad and lands on the dragon's back as it passes (12.75). He rides it,
  arms up.
- **16:9:** the wide course, the dragon sweeping low, the Noob landing on
  its neck. Steve small at the left watching.

### 9. The dive (13.92-15.83) · `dive`
- **Vertical:** close and low beside the dragon as it dives along the
  obby, the Noob riding, straight at the glass cases.
- **16:9:** tracking with the dragon as it dives, the Noob on its back,
  the cases ahead at the right. The chase music swells.

### 10. The cases break (15.83-16.83) · `free`
- **Vertical:** the dragon smashes into the cases. Glass shards (pink and
  cyan) burst everywhere and the frozen players tumble out free. The
  achievement pops in (15.88).
- **16:9:** the cases shattering across the frame, the four players
  freed, standing up and looking round. In the movie it gets 2.2 s, with
  the three breaks heard one after another.

### 11. "That was my plan." (16.83-18.50) · `steve_myplan`
- **Vertical:** Steve close, flat, the freed players behind him at the
  left, the dragon passing overhead.
- **16:9:** Steve chest-up at the right, deadpan, the freed players in the
  background.

### 12. "Your plan was a wall." (18.50-20.00) · `noob_planwall`
- **Vertical:** the Noob riding the dragon in the air, arms up, cheerful
  and honest.
- **16:9:** the dragon hovering, the Noob on its back facing the camera.
  Steve's deadpan beat follows (0.5 s pad).

### 13. The freeze (20.00-22.29) · `freeze` + "...Is it lagging?"
- **Vertical:** a wide from low: the dragon stops dead in mid-air, wings
  locked, the Noob on its back. Steve below on his part looks up. The music
  and the sky's ambience stop on the freeze (a snap).
- **16:9:** the frozen dragon in the sky over Steve, with nothing moving.
  The silence carries it: 2.0 s in the movie. The Noob's line is small and
  unsure.

### 14. "Worlds don't lag." (22.29-23.46) · `steve_lag`
- **Vertical:** Steve close, serious, the frozen players behind.
- **16:9:** Steve chest-up, quiet and serious; it is not a joke this time.

### 15. The glitch (23.46-24.66) · `glitch`
- **Vertical:** close on the frozen dragon: it flickers into the pink and
  black missing-texture checker and back. REALITY drops to 92%. The dread
  cue, a glitch and a sub drop.
- **16:9:** the dragon in the middle of the frame flickering between its
  skin and the checker. The meter glitches in for 97→92. The chapter ends
  on the frozen, flickering dragon (2.4 s in the movie).

## Notes for the build

- **Set:** the finale's obby half, with the course parts from the episode
  file (`obby_course`: the noob pad, steve pad, kill pad, flag, checkpoint
  pad) placed among the finale's parts. Add the four glass cases with the
  frozen players.
- **New pieces in the new look:**
  - the Ender-style dragon (the series' blocky dragon, in the world's own
    textures);
  - the cobblestone wall built and smashed;
  - the glass cases and their shards;
  - the four frozen or freed players: Noob-style avatars, as Episode 0's
    obby players;
  - the dragon's checker flicker (the missing texture, as in Episode 0's
    erasure).
- **Reuse:** the respawn pad and the burst with the dark cube (Episode 2),
  the PLAN timer (Episode 2), the avatars (Episode 0).
- **Faces:**
  - the Noob: thrilled (1), delighted (3), unbothered (5), triumphant (8, 12), small and unsure (13);
  - Steve: deadpan (2, 11), alarmed (3), dry (6), serious (14).
- **Line-end flags** in the automatic review: 10.40, 13.93, 19.75, 23.16.
  - 10.40 is the place sounds starting.
  - 13.93 and 19.75 are the flaps and chase.
  - 23.16 (159.7 dB, impossible as a voice) is the glitch's start at 23.46, measured on a wrapped value.
  - Each is checked again in the movie's sound preview.
