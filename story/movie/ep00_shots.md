# Episode 0 "The End": shot list for the movie remake

The source is the published Short, `preview-ep00_the_end` (`episode.mp4`,
1080x1920, 24 fps, 61.0 s, `timeline.json`). It was studied frame by frame
with time-stamped contact sheets every 0.125 s
(`tools/review_part.py <dir> episode.mp4 --every 0.125`), plus full-size
frames of the fast moments (the run past the camera, the bridge drop and
grab, the ledge erase and the fall). The shot definitions are in
`episodes/ep00_the_end.json` (`shots`, `clips`, `fx`). The branch
`preview-ep00_the_end-shots` holds two test renders, of frames 851 and 1098,
on the same timeline; they aren't part of the published cut.

**The remake** uses the same soundtrack and timing (that run's final mix and
`timeline.json`; nothing goes to the TTS). The picture is redone in 16:9 in
the upgraded look: the new-look Steve, Noob and Null, and the new-look world
and obby used in Episode 9 and the finale (`src/lookdev/`). Each shot keeps
its start and end time, who is in frame, the action, the camera's distance,
angle and movement, and the cue it plays on. Only the framing widens for
landscape.

## What stays and what goes

| Element | Time | Movie |
|---|---|---|
| "EPISODE 0 / THE END" label | 0.00-3.17 | **dropped** (an episode card; the title becomes a YouTube chapter) |
| Captions (cyan for Steve, yellow for the Noob, magenta for Null) | throughout | **kept**, in a landscape layout |
| REALITY meter (counting 100% to 3%) | 11.61-48.52 | **kept** (part of the story) |
| ACHIEVEMENT UNLOCKED: SURVIVE THE APOCALYPSE | 46.42-48.52 | **kept** |
| "24 HOURS EARLIER" card, typed on black | 48.52-50.52 | **kept** (the story's time jump) |
| Forest clip (Episode 1's opening) | 50.52-55.96 | **kept**, re-staged in the new look |
| End card (TWO WORLDS ONE GLITCH, to be continued, next episode, "WHO IS NULL?") | 55.96-60.56 | **dropped** |
| Watermark @GLITCHBOUND2469 | none in the original | **added**, as on every video |

So the chapter runs **0.00-55.96 s**.

## Sound (reused as it is)

- **Music:** `theme_soft` from 0.0 to the freeze (11.6), `chase` from the
  erasure (13.4) to the bridge deletion (+0.3, about 24.1), `null` from the
  darkening (33.0) to black (48.5). The end card's `theme_full` goes with the
  card.
- **Ambience:** a meadow until the freeze; the void from the erasure (13.4)
  to black, at 0.12; the meadow again in the forest, from 52.8.
- **Effects:**
  - a crackle at the freeze (11.6);
  - erasure ticks over 13.4-15.8 (16 hits) and 18.8-21.4 (22 hits); the
    times are in `fx_times`;
  - the bridge breaking (23.8);
  - the grab (25.0);
  - a sub drop at the darkening (33.0);
  - a rising rumble for Null (35.7);
  - the ledge (45.8);
  - the plunge (46.9);
  - a whoosh into black (48.5);
  - the forest clip's own audio (50.5).
- **The silence device:** the meadow and the birds stop at the freeze.
  After that there is only the void's hum, the music and the effects.

## Shots

Times are seconds in the published cut. "Vertical" is what the Short shows;
"16:9" is how the remake frames it. The new-look sources are noted where a
builder already exists.

### 1. Both worlds (0.00-3.17) · vo_1 "There used to be two worlds."
- **Vertical:** a high, wide, slightly tilted view. Steve's grass world fills
  the lower left; the plastic obby world (coloured towers and cylinders,
  white and green plates) sits across the void on the right. A rainbow
  bridge links them. A rainbow staircase rises into the sky, birds circle,
  and the sky is a dusk gradient (peach horizon, blue-grey top). Steve is a
  tiny figure on the grass at the bottom left. The camera drifts very slowly
  closer (lens 18).
- **Caption:** "THERE USED TO / BE TWO WORLDS." (cyan, Steve's narration).
- **16:9:** the same high wide view. Landscape suits it: the cherry
  meadow on the left, the void in the middle, the obby on the right, the
  bridge across, Steve small on the grass. The same slow push.
- **Sound:** `theme_soft` starts with the picture, no deaf opening; meadow
  ambience.

### 2. Mine (3.17-4.71) · vo_2 "Mine..."
- **Vertical:** a medium close-up of Steve from the waist up, three-quarter
  front, under a big oak. He holds his pickaxe low in his left hand and looks
  off screen to the right, calm. Shallow focus (lens 35, f/2.8), a slight
  drift.
- **16:9:** Steve on the left third under the tree (cherry blossom in the
  new world), the meadow going soft behind him on the right.
  A calm face, brows apart.

### 3. His (4.71-6.21) · vo_3 "...and his."
- **Vertical:** the Noob on a pale obby plate in front of a green block, a
  yellow cylinder behind, the void at the left edge. He is **dancing**: arms
  swinging up and down, a little bounce (the `bounce` clip, height 0.55, rate
  1.5, from 0 to the freeze). Cheerful toy smile. Medium-wide (lens 30).
- **16:9:** the Noob on the right third, dancing, with the obby's colours
  around him. Steve's narration says "his", amused.

### 4. They crashed into each other (6.21-8.38) · vo_4
- **Vertical:** a low, wide view from below the level of the bridge, looking
  across the void. The bridge's dark planks run left to right (rainbow
  plastic on the obby side) with a sign post at the left end. The obby towers
  stand on the right, birds fly across the sky, and the purple void fills the
  lower half (lens 20). It barely moves.
- **Caption:** "THEN THEY CRASHED / INTO EACH OTHER."
- **16:9:** the bridge across the whole width: Steve's cliff on the left,
  the obby on the right, the void below. This is the seam where the worlds
  meet.

### 5. The sky; reality stops (8.38-13.42) · vo_5 "And one day... reality just stopped." then the freeze
- **Vertical:** a worm's-eye view looking up past the obby towers to a
  **square sun** with a halo. Clouds float, birds circle, the rainbow
  staircase hangs tilted in the upper right, and Steve is small at the
  bottom left looking up (lens 18). At **11.61 (the freeze)** everything
  stops: the birds and clouds hang still (the `freeze` keys on clouds and
  birds), there's a crackle, and **REALITY: 100%** appears at the top left.
  The picture holds still to 13.41: "reality just stopped" made literal.
- **16:9:** the same upward angle with the sun high and centred; the obby
  towers and the staircase on the right, Steve small on the left. The freeze
  must read as a stop, not as a frozen render: the camera keeps a breath of
  drift while the world stands still.

### 6. The erasure begins (13.42-14.71) · "erasure" beat
- **Vertical:** back to the high wide view of shot 1. Erasure ticks run
  across the obby world and the meter drops 100, 97, 95, 90, 87%.
  Steve is a speck on the grass.
- **16:9:** the wide of shot 1. The deletion is the new-look erase from
  Episode 9 (pieces turn to the black-and-magenta missing texture and
  vanish), spreading across the obby.
- **Sound:** the void hum and `chase` start; one erasure tick per hit.

### 7. The obby (14.71-15.79)
- **Vertical:** inside the obby, from a low angle. Three Roblox avatars (red
  shirt with dark trousers, purple with white, orange with blue) jump
  between floating plates toward a rainbow staircase. The checker erasure
  eats a plate in the foreground (15.25-15.6) and the world tilts toward
  the void. The meter falls 82, 77, 72, 69, 64, 59% (lens 28, the camera
  turning to follow).
- **16:9:** the avatars running left to right across the frame, the
  staircase going up the right, the erasure eating the plate in the near
  foreground.

### 8. "Noob! Run!" (15.79-17.25) · steve_run
- **Vertical:** the same framing as shot 2 (Steve under the tree, pickaxe
  low). He shouts toward the right. Meter at 59%.
- **16:9:** the framing of shot 2. Steve is shouting now, with a mouth open
  wide and alarmed brows (raised and tilted, not joined).

### 9. "I am running!" (17.25-20.37) · noob_running, then erasure_b
- **Vertical:** the Noob runs toward the camera along a plastic rainbow
  brick walk (red, orange, yellow, green, blue studs) with a Minecraft brick
  edge, a green block and an orange cylinder behind him. The camera tracks
  him (lens 24, its look following him at 0.3). He reaches the camera and
  runs past it out of frame left (18.6-19.4). Behind him the walk turns to
  checker and vanishes: erasure_b, the meter falling 54, 49, 46, 41, 36, 31,
  26%. The walk stays empty until 20.37.
- **16:9:** the same: the Noob running at the camera, then out of frame
  left, with the deletion chasing him. His run is flailing and Roblox-style,
  per the creator's "I am running!" note.

### 10. The bridge, side on (20.37-21.46)
- **Vertical:** a wide side view of the bridge from below its level. Steve
  (left) and the Noob (right of him) run along the planks toward the left
  end and pull up at the sign; the void is below and the meter falls 23, 21,
  18, 11, 8, 6, 3%. At 21.37 the Noob turns his head ("OH!").
- **16:9:** the bridge across the frame, the two small, running right to
  left toward Steve's cliff, the void below. The meter lands on **3%**.

### 11. The sign (21.46-22.38) · noob_bridge "Oh! The bridge is..."
- **Vertical:** a close-up of a wooden Minecraft sign, **BRIDGE UNDER
  MAINTENANCE**, at the bridge's end. The planks run away below it with a
  red and white plastic barrier and the void behind; birds overhead (lens
  26).
- **16:9:** the sign large on the left, the empty bridge going off to the
  right. *New prop:* the sign in the new look (an oak sign, pixel-crisp
  lettering).

### 12. Two-shot on the bridge (22.38-24.10) · "...under maintenance!"
- **Vertical:** a medium two-shot on the brick bridge. The Noob is at left
  in profile, facing right, oblivious; Steve is at right facing camera,
  arms half raised, looking at the Noob in deadpan dread. The grass cliff is
  behind (lens 30, f/5.6).
- **16:9:** the two side by side: the Noob cheerful on the left, Steve
  side-eyeing him on the right. Steve's face carries it: flat, tired, brows
  apart.

### 13. The drop and the grab (24.10-25.55) · bridge_delete, fall, grab
- **Vertical:** a wide side view of the cliff face (grass top, dirt wall)
  with the stub of the bridge sticking out. The bridge's far end is checker
  and gone (24.1), the planks blink out, and the two drop (24.3-24.6). Steve
  grabs the cliff edge with one raised hand. The Noob grabs Steve and hangs
  below him (24.75-25.0). Below is the void; one small dark cube drifts away
  in it (the planting rule). A camera shake of 0.03 (lens 24).
- **16:9:** the cliff on the left, the void on the right and below, the pair
  dropping and catching. This must read as a short fall with a real grab
  (the creator's notes: falls are short; hands on the edge; bodies clear of
  the wall).
- **Sound:** `chase` ends at about 24.1; the bridge breaks, then the grab.

### 14. From below (25.55-30.11) · noob_respawn "Steve... can you respawn if there's no world?"
- **Vertical:** a low angle from below the hang, looking up the tilted cliff
  wall (dirt above, grey stone below) into a blue sky with a square cloud.
  Steve hangs from the edge by one arm and the Noob hangs from Steve,
  swaying slightly (lens 22, a slow drift).
- **16:9:** the cliff runs diagonally across the frame with the two hanging
  at the centre, the void's edge below. *Exists in the new look:* the
  finale's hang (`ep10_p6_fall.py`), reframed.

### 15. Faces (30.11-35.48) · steve_no "No.", noob_oh "...Oh.", look_down, darken, steve_what "What... is that?"
- **Vertical:** closer, still from below. The Noob fills the frame from the
  waist up with Steve above him (lens 30, f/4).
  - 30.1-30.6 "No.": flat.
  - 30.6-31.7: a long pause (the joke's timing, `pad` 1.1).
  - 31.7 "...Oh.": the Noob's face turns up and he realises.
  - 32.4 look_down: they look down.
  - 33.0-34.0 darken: the light turns from blue day to a dark red-magenta
    (the sky keys drop, a fill light comes in from below), and the music
    switches to `null`.
  - 34.0 "What... is that?": Steve whispers.
- **16:9:** the two faces as the subject: the Noob's face at the centre and
  lit, Steve's above, the darkening spreading over them. The faces carry
  the shot: the Noob's realisation, then both of them afraid.

### 16. The reveal (35.48-38.29) · null_rise
- **Vertical:** a very wide view over the void (lens 14). The cliff edge is
  at left and the dusk horizon high. Dark and coloured debris blocks float in
  the void. From 35.7 **Null rises** out of it at centre-right: the checker
  head first, then the dark body with glitch pixels, blocks orbiting him.
  He climbs into frame centre by 38.0 and the camera tilts up with him.
- **16:9:** the wide void with Null rising in the centre, the cliff and the
  two tiny on the left. *Exists in the new look:* Null's rise
  (`ep09_new.py` rise, `null.py`).
- **Sound:** the rumble rise, the `null` cue.

### 17. Null close (38.29-45.77) · null_1 "Reality has been corrected." then null_hand
- **Vertical:** a low angle on Null from the waist up, filling the frame:
  the magenta-black checker head, the near-black body with cyan and violet
  glitch pixels, grass, dirt, yellow and brick blocks orbiting and passing
  close to the lens. Dusk sky behind, birds (lens 22, a slow push).
  - 38.3-44.6: the line, slow and cold (magenta caption).
  - 44.87 null_hand: a big brick block and his dark arm sweep at the camera
    as he reaches toward the ledge.
- **16:9:** Null large at the centre, low angle, the orbiting blocks
  crossing the frame. His reach toward the ledge starts the next shot.

### 18. The ledge goes (45.77-46.62) · ledge_gone, the screams begin
- **Vertical:** 45.77-45.88 is a flash: the cliff face is solid
  black-and-pink checker, with the two still hanging on it (`erase_named`
  removes the ledge blocks). From 45.88 the checker is gone and they drop
  away from a grass cliff, small against the blue sky. The shake is 0.03.
  The screams start at 46.12 (both together).
- **16:9:** the same: the cliff turning to missing texture for 2-3 frames,
  then gone, and the two falling.

### 19. The plunge (46.62-48.52) · fall_void, the achievement
- **Vertical:** looking down with them as they fall (the camera falling
  too, lens 24, shake 0.04), past dark debris cubes. A big dark block passes
  in the left foreground. The two tumble away into the void until they are
  tiny. **ACHIEVEMENT UNLOCKED · SURVIVE THE APOCALYPSE** slides in at the
  top (46.42); the meter stays at 3%. The last frames (48.1-48.5) blur into
  a pale sky.
- **16:9:** the same fall with the achievement at the top left. The two stay
  in frame with room around them until they're swallowed.
- **Sound:** the plunge, the screams ("AAAAAAAH!" stacked for both) to
  48.6.

### 20. 24 HOURS EARLIER (48.52-50.52)
- **Vertical:** a black screen. The last "AAAAAAAAH!" caption (the Noob's)
  runs to 48.6, then "24 HOURS EARLIER" types in letter by letter
  (48.9-49.5) and holds. A whoosh.
- **16:9:** the same card, centred. A deliberate black: it is the story's
  time cut, not a gap between parts.

### 21. The forest; the Noob arrives (50.52-55.96) · Episode 1's opening, noob_where "Whoa. Where am I?"
- **Vertical:** this is `assets/clips/ep01_opening.mp4`, with a fade in from
  black (50.52-51.02):
  - 50.5-52.5: a low angle up at an oak against a blue sky with blocky
    clouds. A **small Nether-style portal** (purple frame, glowing pale
    centre) tumbles in the sky above the tree, grows, and the Noob drops out
    of it, past the tree, and lands on the grass behind it (51.4-52.0). He
    stands up.
  - 52.5-53.9: a medium shot of the Noob facing camera, smiling, looking
    around ("WHOA.").
  - 53.9-55.96: he walks toward and past the camera, the tree trunk in the
    right foreground ("WHERE AM I?"). Steve is just visible far off at
    the left edge, half hidden.
- **16:9:** the same three beats in the new world: the portal tumbling over
  the tree, the Noob's fall and landing, his "Whoa", and his walk past the
  tree with Steve far off. *Exists in the new look:* the portal
  (`portal.py`).
- **Sound:** that clip's own audio, the meadow back from 52.8.

## How the finale answers Episode 0 (one core, two perspectives)

All 14 published finale parts (`preview-ep10_p1_entrance` to
`preview-ep10_p14_end`) were studied at two frames a second, alongside their
renderers' notes in `src/lookdev/ep10_p*.py`. The finale is Episode 0's
moment lived again from inside the loop. The remake has to make the two
match, so that the ending lands on pictures the viewer has already seen.

| Episode 0 | The finale | What the remake does |
|---|---|---|
| The two worlds joined by a bridge over the void (shots 1, 4, 6) | P4: the Noob builds the Roblox half with his BTool and sends a rainbow bridge onto **the old oak-plank bridge**; P6 calls it "the old bridge" | The bridge is the finale's: old oak planks over the void, with the rainbow plastic at the obby end. Same place, same materials |
| "Noob! Run!" / "I am running!" (shots 8, 9) | P5, the deja vu: Episode 0's own recordings. Through Steve's eyes the Noob runs at the camera on the rainbow, the world erasing behind him, and splits into the Noobs of other loops; "412 times", "I built a trap" | Shot 9 is framed like P5's memory: the Noob centred, running straight at the camera on the rainbow, the erasure behind. The finale then "remembers" the very picture of Episode 0 |
| "The bridge is under maintenance!", then the bridge is deleted and they drop and grab (shots 11-13) | P6: "STEVE, WAKE UP! THE BRIDGE IS FALLING!" The bridge is deleted piece by piece, they leap and catch the stub and hang over nothing | Shots 10-18 use the finale's void stage (`ep10_new.py` `_void_stage`: the ledge, the old bridge, the void, the stub), so the finale's hang is visibly the same spot |
| The hang: "Can you respawn if there's no world?" "No." "...Oh." (shots 14, 15) | P10-P11: hanging from the same stub, "Steve, remember... I am a Roblox player." The Noob lets go on purpose | Same stub and cliff. Episode 0's "No." is what the Noob's choice in the finale answers |
| Null rises from the void: "Reality has been corrected." He reaches for the ledge, erases it, they fall (shots 16-19) | P7-P9: Null is made of the Noob's old bodies (small cubes, each a Noob head); "sorry"; "You weren't supposed to survive." P14: "All I wanted was to fix this world" | Null is the new-look Null (`null.py`, Ep9/finale): the round checker head with the copied smile, the dark cell body, the orbit rings. His reach toward the ledge uses the finale's reach (`REACH`, `null_ledge`). "Corrected" is the same wish as his last line in the finale |
| Small dark cubes drifting in the void (the bible's planting rule) | P7: those cubes are Null's cells, each one a Noob's head | The void debris is the finale's cell cubes, small and dark, their faces too small to read. Rewatchers will see what they are |
| They fall into the void. "24 HOURS EARLIER": the Noob drops out of a portal into the forest. "Whoa. Where am I?" (shots 19-21) | P1: the first portal in the forest, where Null comes through. P12-P14: the Noob falls into the void, the world comes back, Patch sets them down on the meadow: "...So. I'm back?" | The forest is the meadow the finale ends in, and the portal is the finale's first portal (`portal.py`). "Where am I?" (the loop restarting) and "So. I'm back?" (the loop broken) happen in the same place |

So the story's spine, as the episodes already tell it:
- **Episode 0:** the loop as it always ends. They run, the bridge goes,
  they hang, Null erases the ledge, they fall, and the portal throws the Noob
  back to the start.
- **The finale:** the 413th time, seen from inside. Steve knows; the Noob
  says sorry; Null breaks; the Noob jumps on purpose; Patch catches him. The
  same place, the same lines echoed, a different ending.

The remake keeps every Episode 0 shot as published. It only sets those shots
in the finale's places and gives them the finale's things (the bridge, the
stub, the void, Null, the cells, the portal, the meadow), so the two match
when they're seen in one movie.

## Where Episode 0 meets Episode 1

The published Episode 1 opens with a "PREVIOUSLY..." flash of Episode 0's
fall and screams (0-2 s). It then plays this same forest clip with the same
"Whoa. Where am I?" (2.0-5.25, labelled "EPISODE 1 · 24 HOURS EARLIER").
Its new material starts at 9.9 s ("Okay. A tree. One punch."). Joined
straight, the movie would play the fall, the forest and "Where am I?" twice
in a row. Proposed: the recap and the repeat are Shorts packaging, so in the
movie Episode 1 picks up right after Episode 0's "Where am I?". **The
creator agreed on November 13: skip Episode 1's repeat.**

## As built (`src/lookdev/movie_ep00.py`)

- The renderer loads the finale's finished egg (`ep10_p6_fall.build`) and
  stages Episode 0 in it. Minecraft is on +x (screen right in the wides),
  the Noob's obby on -x, and the old bridge runs along x at the egg's near
  end (y = -27, deck z = 11), with its stub at x = 3. That matches the
  finale's geography, so the Short's left/right is mirrored where the
  finale needs it.
- The chasm is about 10 m across, so the Noob runs across his obby before
  he reaches the bridge.
- Null rises out of the open void past the near rim and faces the hang.
  His cells' faces are kept dark (`cells_look(awake=0)`), because in
  Episode 0 nobody knows what he is made of.
- Narration (the `vo` lines) moves no mouth.
- The black between 48.52 and 50.52 s is rendered as black frames; the
  card is laid over it in assembly.
- The forest is its own build (`build_forest`): the restored world of the
  finale's ending, an oak, the first portal tumbling over it, and Steve far
  off at the left.

## Decided by the creator (November 13)

1. **Left and right follow the finale's geography**: Minecraft on the right,
   the obby on the left in the wides, mirrored from the vertical Short.
2. **The hang stays in Episode 0's daylight** until the darkening. The
   finale's purple dusk on the same stub comes later in the story.
3. **"Whoa." is amazed** (an open "o" mouth), not the published smile.

## Notes for the build

- The hidden dark cubes (the bible's planting rule) appear in shots 9, 10,
  13 and 14 as tiny black cubes in the void. Keep them small and off centre.
- Shots 2 and 8 share one setup, and so do shots 1 and 6; shots 14, 15
  and 18 are one location (the hang). Build each location once.
- Faces: Steve's brows are never joined. The Noob's face is the new
  Roblox face (black oval eyes with shine, the shared mouth shapes).
- Already built for the finale and reused: the void stage (the ledge, the
  old bridge, the stub, the cells), Null and his reach, the erase, the
  meadow and the cherry world (`world.py`), the first portal, the Noob's
  obby parts (`roblox.py`, P4).
- New pieces to build: the wide of the two worlds side by side in daylight;
  the BRIDGE UNDER MAINTENANCE sign; the Noob's dance; the sky with the
  square sun and the freeze; the three obby avatars running; the portal
  tumbling in the daytime sky over the meadow.
