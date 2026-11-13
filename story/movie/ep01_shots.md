# Episode 1 "The Noob Who Punched a Tree": shot list for the movie remake

The source is the published Short, `preview-ep01_the_tree` (`episode.mp4`,
1080x1920, 24 fps, 31.4 s, `timeline.json`). It was studied frame by frame
with time-stamped contact sheets every 0.125 s (`tools/review_part.py ...
--every 0.125`). The punch (13.3-14.3 s) and the flurry and break
(19.6-21.9 s) were also stepped through at 12 frames a second. The shot
definitions are in `episodes/ep01_the_tree.json` (`shots`, `clips`, `fx`).

**The remake** keeps the same soundtrack and timing (the final mix and
`timeline.json`; nothing goes to the TTS). The picture is redone in 16:9 in
the upgraded look. It takes place in the same meadow as Episode 0's last
shot: the restored world of the finale's ending, with the oak and the cherry
trees, where the Noob landed out of the portal.

## Where it starts (the creator: "skip Ep1's repeat")

| Published | Time | Movie |
|---|---|---|
| "PREVIOUSLY...": Episode 0's fall and screams | 0.00-2.00 | **dropped** (Episode 0 has just shown it) |
| The forest clip: the Noob drops out of the portal, lands, "Whoa. Where am I?", with the "EPISODE 1 / 24 HOURS EARLIER" label | 2.00-6.94 | **dropped** (a repeat of Episode 0's 50.5-55.96) |
| He looks round and walks to the tree (no line) | 6.94-9.94 | **kept, my proposal** (see below) |
| "Okay. A tree. One punch. Watch this." to "...That's not." | 9.94-27.94 | **kept** |
| End card (TO BE CONTINUED, next episode, "WHAT BROKE THE SKY?") | 27.94-31.34 | **dropped** |
| "IS THIS NORMAL? COMMENT ↓" prompt | 23.66-25.05 | **dropped** (a Shorts comment prompt, not story) |
| REALITY meter 100%, turning to 99% (pink) on the crack | 2.4-27.94 | **kept** |
| Captions | throughout | **kept**, landscape layout |
| Watermark | throughout | **kept** |

**Proposed start: 6.94 s, not 9.94 s.** The 3 s after "Where am I?" are not
a repeat: the Noob looks round, notices the tree and walks to it. Without
them he would jump from "Where am I?" (Episode 0's last frame) straight to
standing at a tree saying "Okay". With them, the chapter runs **6.94-27.94
(21.0 s)**. To ask the creator.

**The join:** Episode 0 ends at 55.96 on the Noob walking toward the camera
past the near trunk. Episode 1 opens at 6.94 on him in the same place,
looking round. So the remake's Episode 1 starts from where its Episode 0
leaves him: the same spot, light, oak and camera side. The sound joins as
the published mix does (`theme_soft` is already running under "Where am
I?"); the join pass smooths it.

## Sound (reused as it is)

- **Music:** `theme_soft` from "Where am I?" to the crack (25.05), swelling
  after "Where am I?". The `null` cue from the crack, then `dread` from
  "...That's not." with a hit at 29.3, which falls after the chapter's end.
  The join pass decides how that tail ends.
- **Ambience:** the meadow until the crack.
- **Effects:**
  - footsteps on the walk to the tree (8.94-9.94, one every 0.227 s);
  - the punch thuds;
  - the flurry;
  - the break (20.93);
  - the glitch at the crack (25.05).
- **The silence:** the meadow stops at the crack.

## Shots

### 1. Looking round (6.94-8.94) · after "Where am I?"
- **Vertical:** a medium-wide, low angle on the Noob standing on the grass,
  facing the camera, the oak trunk at the right of the frame, a grassy slope
  behind. He turns his head right, left, then up (the clips at 7.0-8.9),
  smiling. Lens 24, still.
- **16:9:** the Noob centre, the oak at the right, the meadow and cherry
  trees behind. Head turns as people turn: head first, then the body
  following a little.

### 2. The walk (8.94-9.94)
- **Vertical:** close and low, tracking beside him as he walks past toward
  the tree. His face passes the lens, smiling, the trunk entering at the
  left by 9.9. Lens 26. Footsteps.
- **16:9:** tracking with him, the tree ahead at the right, room in front
  of him.

### 3. At the tree (9.94-13.38) · noob_tree "Okay. A tree. One punch. Watch this."
- **Vertical:** a medium shot, the Noob at the left facing the camera, the
  trunk filling the right edge. He turns to the tree on "Okay." (10.0-10.3).
  He talks to the camera, cocky: a toy smile, the eyes on us. At 13.25 he
  turns to the trunk (yaw 1.57). Lens 24.
- **16:9:** the Noob on the left third, the trunk on the right third,
  showing off to the camera. A cocky face: the smile wide, one eye
  squinting.

### 4. The punch (13.38-14.21)
- **Vertical:** over his shoulder from the side: the arm swings, the fist
  hits the trunk (13.5), he pulls back, and the arm hangs (14.0). Nothing
  happens to the tree. Lens 26.
- **16:9:** side on, the Noob left, the trunk right; one clean punch with a
  thud. A crack decal doesn't appear yet (Minecraft needs more hits).

### 5. Steve (14.21-16.33) · steve_tool "It's a tree. You need a tool."
- **Vertical:** a close-up of Steve, head and shoulders, his pickaxe raised
  in his right hand behind him. Flat, deadpan. He lowers the pick a little
  on "tool". Lens 38, shallow focus.
- **16:9:** Steve close, deadpan: brows level, apart, half-lidded. The
  pickaxe held up as the proof of "a tool". He stands a few blocks from the
  tree, so this shot also tells us where he is.

### 6. The wide (16.33-19.62) · noob_roblox "I don't need tools. I'm a Roblox player."
- **Vertical:** a wide from low on the grass: Steve small at the left, the
  Noob at the tree in the middle, the oak's crown filling the top. The Noob
  turns to Steve and spreads his arms (the pose, 16.3-19.5): "I'm a Roblox
  player." Lens 22.
- **16:9:** the wide of the three of them: Steve left, the Noob centre,
  the oak right, the meadow behind. It's the line Episode 10 gives back
  ("Steve, remember... I am a Roblox player."), so frame it cleanly, as a
  line people will remember.

### 7. The flurry (19.62-21.38)
- **Vertical:** side on at the trunk, close: the Noob punches fast,
  alternating fists, about 5 hits a second. At 20.93 (the break) the
  trunk's lowest block bursts into pieces and the rest of the tree stays up
  in the air. Lens 20.
- **16:9:** side on, the Noob left, the trunk right. A cartoon blur of
  punches with a crack decal growing on the block (Minecraft's breaking
  stages, 0 to 9). On the break, the block pops into small bits; the trunk
  above hangs in the air with a gap under it. Bits fall and bounce.

### 8. The reveal (21.38-21.85)
- **Vertical:** a wide: Steve left, the Noob cheering (the clip `cheer`)
  under a tree that now floats, the bits on the grass. One beat.
- **16:9:** the same wide as shot 6: the Noob's arms up in victory, the
  tree floating over the gap.

### 9. Floating (21.85-25.05) · noob_float "...Why is it floating?", steve_normal "That's normal."
- **Vertical:** a low angle from the grass up past the stump to the
  floating trunk and crown against the sky. Steve at the left and the Noob
  at the centre look up at it. "That's normal." is deadpan. Lens 19.
- **16:9:** low and wide, the floating tree at the top centre, the two
  looking up at it below, Steve left. The joke is Minecraft's
  floating-tree rule; Steve's "That's normal." gets its beat.

### 10. The sky cracks (25.05-26.75) · crack
- **Vertical:** Steve from behind and below, small, looking up at the sky.
  A jagged crack opens across it (25.25-25.5), showing the magenta and
  black missing-texture checker behind, with white glitch edges and shards.
  The light drops (the sky keys, from 25.05 to 25.65). REALITY turns to 99%
  in pink (25.45). Lens 17.
- **16:9:** the crack across the whole width of the sky, over the floating
  tree and the meadow. Steve looks up at it, three-quarter from behind, so
  we see his face turning up. (The notes ask for no backs to the camera;
  the published shot is from behind, so the remake turns him enough to
  read his face.)

### 11. The eye (26.75-27.94) · steve_not "...That's not."
- **Vertical:** closer on the crack: through it, a grey eye with a magenta
  slit pupil looks out from inside the checker, and the pupil moves (26.75
  to the end). Lens 32.
- **16:9:** the crack framed wide, the eye inside it looking down at them.
  It is the series' first sign that "something on the other side watches"
  (bible, Ep2's cliffhanger, already planted here). The same drawing,
  built in the new look: the same eye, nothing new about what it is.

## Notes for the build

- **Set:** Episode 0's `build_forest`, the meadow with the oak (`OAK`), the
  near trunk and the cherry trees, so the two chapters are one place. The
  tree he punches is the oak he fell past. The floating tree is that oak,
  with its bottom log block removed.
- **Steve** first appears in shot 5. In Episode 0's forest he is already
  far off at the left (`STEVE_FAR`); here he has walked closer, a few
  blocks from the tree, pickaxe in hand.
- **New pieces:**
  - the breaking-stage decal (Minecraft's destroy stages, from the MCprep
    pack);
  - the log breaking into bits;
  - the floating crown;
  - the sky crack with the checker behind it;
  - the eye.
- **The faces carry the comedy:** the Noob cocky in shot 3, delighted in
  shot 8, puzzled in shot 9; Steve flat in shots 5 and 9, and worried in
  shot 11 (heard off screen, so the eye has the frame).
- **Dark flags** in the automatic review (26, 30, 31 s) are the crack's
  darkening and the end card. In the movie, the darkening stays as bright
  as Episode 0's darken beat at least.
- **Five line-end flags** (a burst above 3 kHz after the line) are in the
  published mix: 6.94, 13.26, 16.09, 19.53, 24.55. The spectrograms
  (`line_ends.jpg`) put each burst 0.1-0.3 s after the line ends, where the
  next sound starts: the punch at 13.36, the next line at 16.33, the flurry
  at 19.63. None shows the line-end "tchch" itself. The soundtrack is reused
  as it is; still, listen to each before the preview. If any is the
  "tchch", take it to the creator, because fixing it means touching the
  reused mix.
