# Episode 2 "The Plan": shot list for the movie remake

The source is the published Short, `preview-ep02_the_plan` (`episode.mp4`,
1080x1920, 24 fps, 29.25 s, `timeline.json`). I studied it frame by frame
with time-stamped contact sheets every 0.125 s (`tools/review_part.py ...
--every 0.125`), plus the first and last frame of every shot. The shot
definitions are in `episodes/ep02_the_plan.json` (`shots`, `clips`, `fx`,
`actors`).

**The remake** keeps the same soundtrack and timing (the final mix and
`timeline.json`; nothing goes to the TTS). Only the picture is redone, in
16:9 and in the upgraded look. It takes place in the meadow from Episodes 0
and 1: the same oak, which is still floating since Episode 1 (the episode
file's `tree_broken` effect), and the same cherry trees. The portal is built
beside the oak.

## The movie's longer timing (the creator, November 14)

"For ep2 it is too fast ... no restrictions on time." The lines stay the
same words and the same voice takes. Only the room around them grows,
with the music and effects re-laid to fit. The movie's episode file is
`episodes/movie_ep02_the_plan.json`. It reads the voices only from the
cache (`voices_cache_only`), so a missing take stops the run instead of
recording a new one. The shot times below are still the published ones;
the new times come from the sound preview.

| Moment | Published | Movie | What the room is for |
|---|---|---|---|
| The eye | 1.4 s | 2.6 s | it looks round before the crack snaps (the hit moves to 2.1) |
| *new beat* `look_up` | none | 1.0 s | the sky clears; the two still staring up, then at each other |
| After "Today." | 0.15 s | 0.6 s | the line lands |
| *new beat* `build` | none | 3.0 s | the frame finished block by block; Steve steps back, satisfied. The PLAN timer still runs exactly 3 s to the press: the joke stays tight |
| After "This one?" | 0.05 s | 0.25 s | Steve sees the Noob's hand over the button |
| The press | 0.35 s | 0.5 s | |
| Portal opens | 0.8 s | 1.6 s | the flash, the swirl, the Noob cheering |
| The pour | 1.9 s | 4.0 s | the junk and three zombies come out one by one; more pops and groans |
| The hit / the respawn | 0.55 / 0.35 s | 0.8 / 0.8 s | the burst reads, then the pop |
| After "New record!" | 0.1 s | 0.4 s | |
| Chaos | 1.1 s | 3.0 s | the zombies loose in the meadow, Steve dodging |
| Dash / smash | 0.45 / 0.75 s | 0.9 / 1.0 s | the wind-up |
| The suck | 1.3 s | 2.6 s | everything pulled back in, the zombies lifted off their feet |
| *new beat* `quiet` | none | 1.2 s | dust settling, the meadow quiet, Steve breathes out |
| After "...Never again." | 0.25 s | 0.6 s | |
| *new beat* `approach` | none | 2.0 s | the Noob wanders to the dark portal and notices something inside |
| The mirror | 1.7 s | 3.0 s | the figure waves back, slowly |
| After "It waved back." | 0.35 s | 0.6 s | |
| The snap | 0.9 s | 2.5 s | the empty frame, the quiet, the Noob frozen |

About 25.8 s becomes about 46 s.

## What stays and what goes

| Published | Time | Movie |
|---|---|---|
| The eye in the sky crack; the crack snaps shut | 0.00-1.40 | **kept**: it picks up exactly where Episode 1 ends (the eye) |
| "EPISODE 2 / STEVE'S PLAN LASTED 3 SECONDS" label | 1.40-3.88 | **to ask**: it is an episode card (dropped in the movie), but its second line sets up the PLAN timer joke. My proposal: drop it; the timer tells the joke on its own |
| PLAN timer (0.00s counting, then "PLAN FAILED: 3.00s" in red) | 4.99-9.54 | **kept**: a story gag, like the REALITY meter. Landscape layout |
| "WOULD YOU PRESS IT? COMMENT ↓" | 6.91-8.94 | **dropped** (a Shorts comment prompt) |
| Achievement "TEAMWORK! Build a portal together" | 8.64-10.94 | **kept** |
| REALITY 99% → 97% (pink) at 17.56 | 1.40-25.80 | **kept** as the approved movie meter: hidden while still; it glitches in for the drop at the suck and tears away after it |
| The white flash on the smash | 16.56-16.71 | **kept** |
| End card (TO BE CONTINUED, Episode 3, "WHAT WAS WATCHING THEM?") | 25.80-29.20 | **dropped**; the chapter ends at 25.80 |
| Captions, watermark | throughout | **kept**, landscape layout |

**The chapter runs 0.00-25.80 (25.8 s).**

**The join with Episode 1:** Episode 1 ends on the eye in the crack
("...That's not."). Episode 2 opens on the same eye, which then snaps shut.
Both the eye and the crack must be the very model Episode 1's remake builds,
seen from the same side.

## Sound (reused as it is)

- **Music:**
  - `dread` under the eye, with a hit on the snap (1.05);
  - `theme_soft` under Steve's plan;
  - `chase` from the button press (7.99) to after the suck, swelling on the chaos;
  - `dread` again from the end of the suck, hitting on the portal's snap (24.90);
  - Null's theme (`null`) after it, which falls past the chapter's end. The join pass decides how that tail ends.
- **Ambience:** the meadow from 1.40 to the suck (16.96).
- **Effects:**
  - the glitch and thump at the start, the snap of the crack;
  - 18 block "place" sounds while the portal is built;
  - the click of the button, the portal opening, a whoosh and a jingle;
  - pops as the junk pours out, the zombies groaning;
  - the burst when the Noob is hit, the respawn;
  - a whir under the chaos, the dash whoosh, the crunch of the smash;
  - the suck, a sub drop under "Hi!", the snap of the portal.
- **Line-end flags** in the automatic review:
  - 13.32 ("I'm fine! New record!"): an 11.6 dB burst; it is the chaos shot's groan and pops starting.
  - 24.55 ("...Steve? It waved back."): a 72.8 dB burst; it is the snap at 24.90 (the loudest sound of the chapter, on purpose).
  - Neither looks like the "tchch". Listen before the preview anyway.

## Shots

Times are the published ones. The 16:9 notes say how the shot is restaged.

### 1. The eye (0.00-1.40) · `eye`
- **Vertical:** looking up past a dark tree crown at the sky crack. A grey
  eye with a magenta slit pupil looks out of the missing-texture checker,
  lit pink. At 1.05 the crack snaps shut to a thin glowing line. Then plain
  blue sky with blocky clouds, and a little glint where it closed. Lens 50,
  a slight shake.
- **16:9:** the same up-angle as Episode 1's last shot, the oak's (floating)
  crown at the bottom of the frame. The crack closes from the ends inward on
  the hit and leaves a fading seam. The sky's light comes back up as it
  closes (the sky keys: dark under the crack, day after 1.6).

### 2. "New rule. We leave. Today." (1.40-3.62) · `steve_rule`
- **Vertical:** Steve turns to the camera (1.38-1.6) into a chest-up
  close-up, the forest behind, pickaxe in his right hand. Flat and
  decisive. Lens 38, shallow focus.
- **16:9:** Steve on the right third, the meadow and the floating oak soft
  behind him. The turn goes head first, then shoulders (the creator's rule).
  A deadpan face: brows level and apart, eyes steady on us.

### 3. "Portal home. Three steps. Nobody touches anything." (3.62-6.92) · `steve_plan` / build
- **Vertical:** a low wide from behind a grey stone pillar topped with a big
  red button (foreground right). Steve stands at the right and places
  obsidian with the pickaxe swinging. The portal frame grows block by block
  (18 places), left pillar first, then the top and the right. On "anything"
  it is a full empty frame. The PLAN timer starts at 4.99. Lens 20.
- **16:9:** the button pillar in the left foreground, Steve at the right
  building, the frame rising between them with the meadow and trees behind.
  Each block lands on a "place" sound with a small puff. The Noob is out of
  shot (the episode file has him at the right, watching); in 16:9 he can
  stand at the far right edge, so the next shot's "This one?" has a place to
  come from.

### 4. "This one?" (6.92-7.54) · `noob_this`
- **Vertical:** low, close: the Noob at the button pillar, his right hand
  hovering over the red button, his smile to the camera. The empty portal
  frame is behind. Lens 26.
- **16:9:** the Noob and the button centre-left, his hand above it, his face
  innocent and curious (the toy smile, brows up), the portal frame behind
  at the right.

### 5. "Don't!" (7.54-8.00) · `steve_dont`
- **Vertical:** Steve turns sharply to the camera, his right arm shooting
  out toward us (the button). Lens 35.
- **16:9:** Steve medium, reaching across the frame toward the Noob
  (off-screen left). His face alarmed: eyes wide, mouth open, brows up and
  apart.

### 6. The press (8.00-8.33) · `press`
- **Vertical:** an extreme close-up: the Noob's hand comes down on the red
  button and it sinks. "PLAN FAILED: 3.00s" flashes red. Lens 30, a jolt.
- **16:9:** the same insert, wide enough to see the button whole. The
  hand's press and the click land together. The timer turns red on the
  frame of the press.

### 7. The portal opens (8.33-11.04) · `portal_open` + `pour`
- **Vertical:** a wide from the front-left: the portal fills with a bright
  white flash, then a blue and pink swirl (8.35-8.6). Steve and the Noob
  stand at the right by the button; the Noob cheers. The achievement pops
  in at 8.64. From 9.1, salmon-pink cubes fly out of the portal toward the
  camera, a red-and-white barrier pole tumbles out, and three zombies step
  out one after another (9.29, 9.59, 9.94), arms raised. Lens 18.
- **16:9:** the portal centre-left, the two at the right, the meadow
  around. The junk pours at the camera and past it, the pole spinning end
  over end, the zombies shuffling out. Steve's face goes to shock, the
  Noob's to delight (his cheer, 8.34-8.84).

### 8. The hit (11.04-11.58) · `hit`
- **Vertical:** close on the Noob from the side: a pink cube hits him and
  he bursts apart into flying limbs (his blocks), with a dark cube left
  inside the burst (the `dark_cube` effect). Lens 28, a shake.
- **16:9:** the Noob centre, side on. The cube smacks him and his parts fly
  outward; the burst is quick (0.5 s). The dark cube planted here is the
  series' first hint of Null's cells (the bible); keep it small, visible
  for a moment, and not explained.

### 9. Respawn (11.58-13.42) · `respawn` + "I'm fine! New record!"
- **Vertical:** a low medium on a respawn pad (a stone ring with a glowing
  cyan rim) on the grass. The Noob pops up on it (11.6-11.75) and cheers
  with both arms up. Lens 26.
- **16:9:** the pad centre, the meadow and trees behind, the Noob popping
  in with a respawn shimmer, arms up, a big smile and dazed eyes. The pad
  appeared at 8.69 (the `spawn_pad` effect, at the portal's opening); in
  16:9 it should be visible in shot 7's wide so it doesn't come from
  nowhere.

### 10. Chaos (13.42-14.54) · `chaos`
- **Vertical:** the shot 7 wide again: the zombies at the left, the barrier
  pole rolling, pink cubes on the grass, Steve at the right by the button
  flinging his arms in shock. Lens 18, a shake.
- **16:9:** the same wide as shot 7, so the viewer reads what changed:
  zombies out, junk everywhere, Steve stunned at the right.

### 11. "Plan B!" (14.54-15.75) · `steve_planb`
- **Vertical:** Steve close, the portal's purple frame behind him at the
  left. He shouts and raises the pickaxe in his left hand (14.6-15.0).
  Lens 32, a slight shake.
- **16:9:** Steve chest-up at the right, the portal swirling at the left of
  the frame. A determined face: brows down but apart (the creator: anger
  brings them down, never joined). The pickaxe goes up on "B".

### 12. The dash (15.75-16.21) · `dash`
- **Vertical:** low behind the button pillar: Steve runs at the camera
  toward the button, the portal swirling behind him. Lens 24.
- **16:9:** Steve dashing from the left toward the pillar at the right, a
  whoosh. Fast; motion blur.

### 13. The smash (16.21-16.96) · `smash`
- **Vertical:** a low angle past the red button up at Steve against the
  square sun. He swings the pickaxe down onto the button (16.5). On the
  crunch (16.56) there is a white flash (with two very short cuts in the
  flash at 16.58 and 16.62), then pink pieces and the button's shards fly
  off. Lens 18, a strong shake.
- **16:9:** low past the button, Steve swinging down with the sun behind
  him. The flash covers the impact (as published). The button breaks into
  pieces, its red cap flying.

### 14. The suck (16.96-18.25) · `suck`
- **Vertical:** the wide again: the portal turns white and sucks
  everything back in: the pole, the cubes, then the zombies (17.4-17.9),
  pulled off their feet into it. Steve at the right watching. REALITY drops
  to 97% (17.56). The portal's swirl flickers and goes dark purple.
- **16:9:** the same wide, everything streaking back into the portal.
  The zombies are lifted and spun in, and the junk pops away. The meter
  glitches in for the 99→97 drop (it pops 1.3x on the drop, then tears
  away).

### 15. "...Never again." (18.25-19.96) · `steve_never`
- **Vertical:** Steve medium, standing still in front of the now dark
  portal (its obsidian frame at the left), exhausted, the pickaxe hanging.
  Lens 30.
- **16:9:** Steve centre-right, the dark portal behind at the left, the
  meadow at the right in the daylight. He is tired and relieved: half-lidded
  eyes, a long breath out. After the line his head turns a little up and
  left (the clip `look`, a hint something is there).

### 16. "Hi!" and the mirror (19.96-22.29) · `noob_hi` + `mirror`
- **Vertical:** from the side of the portal, low: the dark purple portal at
  the right, the Noob at the left edge, waving at it. Inside the portal a
  small pink checker figure (Null, seen far away through it) waves back
  (from 20.3). The light is dim and the sky darker. Lens 20.
- **16:9:** the portal side-on at the right, the Noob at the left waving
  with his right arm. Through the dark surface, deep inside it, the small
  figure waves back. It is the finale's Null in the new look, tiny and far:
  the checker body, no readable face. The sub drop sits under "Hi!".
- **Brightness:** the published shot is very dark (brightness 24-31 out of
  255 from 22 s). The notes ask for the brightness of the original "even
  with Null on screen". The remake keeps the mood with the portal's purple
  glow and a dimmer sky, but stays readable.

### 17. "...Steve? It waved back." (22.29-24.88) · `noob_waved`
- **Vertical:** a low close angle along the portal's frame: the Noob at the
  left edge, his face to the camera, uneasy. The figure inside the portal
  comes closer (from 23.3, the clip `walk`) and keeps waving. Lens 22.
- **16:9:** the Noob at the left, three-quarter to us, the portal filling
  the right two-thirds. The figure grows as it walks toward the surface.
  The Noob's face goes from puzzled to worried (eyes wide, smile gone).

### 18. The snap (24.88-25.80) · `snap`
- **Vertical:** the portal flashes white (24.9), then is suddenly empty: a
  bare obsidian frame with the meadow seen through it. The Noob stands
  beside it with his arm still up. Lens 22.
- **16:9:** the flash and the snap together; then the empty frame and the
  quiet meadow, the Noob frozen beside it. Steve's shock (the clip) is off
  screen in the published shot. In 16:9 he could be at the edge of frame,
  but only if he fits without a new action. **To ask the creator.** The
  chapter ends at 25.80.

## Notes for the build

- **Set:** the meadow from Episode 0's `build_forest` (Episode 1's remake
  reuses it too), with the floating oak.
- **New pieces** (in the new look):
  - the obsidian portal frame built block by block, its swirl, flash and
    dark state, and the snap to an empty frame;
  - the red button on its stone pillar, and the button smashed;
  - the respawn pad;
  - the pink cubes, the barrier pole and three zombies;
  - the Noob's burst into parts with the dark cube.
- **Reuse:**
  - the portal from `portal.py` (the finale's) for the swirl and flash, if
    it fits an obsidian frame;
  - the finale's Null, scaled small, seen through the portal.
- **Zombies:** the series has no new-look zombie yet. The only one is the
  old kit's `make_zombie` (`src/kit/rigs.py`). A new-look zombie is built
  on Steve's new rig with the zombie's skin, and its face follows Steve's
  faceplate (no new face style).
- **Faces carry the comedy:** Steve deadpan (2, 3), alarmed (5), shocked
  (7, 10), determined (11), exhausted (15); the Noob innocent (4), delighted
  (7, 9), uneasy (17).

## To ask the creator

1. The "EPISODE 2 / STEVE'S PLAN LASTED 3 SECONDS" label: drop it with the
   other episode cards (my proposal; the PLAN timer carries the joke), or
   keep its second line as a story card?
2. Shot 18: keep Steve out of the last shot as published, or show him at
   the edge, frozen in shock?
