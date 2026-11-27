# Movie Episode 7: "Patch Remembered Another World" — the Memory Grid (16:9, ~51.5 s)

The creator's 16:9 blueprint and fixes (2026-11-27; `story/movie/ep07_ep08_notes_2026-11-27.md` and the session's
notes on the published Short). Episode file `episodes/movie_ep07_another_world.json`; sound `movie/ep07`; renderer
`src/lookdev/movie_ep07.py` (imports `movie_ep06`, as Ep6 imports Ep5). **Null is never seen** (no body, no
checkerboard head, no smile): the dark residue becomes a shapeless core; his silhouette stays a surprise until
`ep10_part1_null_entrance`. **Never back to the obby.**

## What the published Short got wrong (the creator's notes) and what we do instead
| published | movie |
|---|---|
| 0:00-4.5 and 0:27.5-33.5: obby bookends next to Null ("It's COPYING me!", "Hold still. I'm taking us back.", "I don't want to be deleted" back on the obby) | cut. "It's copying me!" / "Hold still- I'm pulling us out!" now end Ep6 (new takes there); Ep7 opens on Ep6's cyan-white flash and stays in the grid; "I don't want to be deleted." is said in the grid among the ghosts |
| the BTools hammer glued to the Noob's left side | gone (the void took it in Ep6) |
| Steve's pickaxe back in his hand at 0:09 | empty hands through Ep7 and Ep8 |
| they pop onto the pads in stiff idle poses | they tumble out of the warp: Steve to one knee, the Noob on his back then hopping up, Patch wobbling then steadying |
| the past-Noob explodes in mid-air for no reason | he hops onto a faint translucent red kill-brick, shatters into glowing wireframe limbs, a dark cube thuds down, a new ghost pops up: "that's him dying and respawning" |
| frozen mouths (":o" held 3 s), a grin under Patch's explanation | lip-sync on every Noob line; worried brows, solemn mouth from "What are those?" to the end (no snap back to ":)" on "From last time.") |
| Steve stares into the lens on "What are those?" | he looks down at the cubes on the floor |
| a stray black diagonal rod across the ghosts (0:16.5, 0:21) | nothing in the grid that isn't built on purpose; checked in the stills |
| a grey-brown humanoid with a pink checkerboard head under the cubes; a Null clone beside the ghost trio; checkerboard Null statues in every cell | the cubes snap into a swirling sphere of pitch-black corrupted blocks with faint magenta cracks (no head, no arms, no face); each cell has a jagged translucent black-and-magenta void fissure instead |
| grey boxes piled on the ghost-Noob's head | clean holograms: Fresnel edge, horizontal scanlines, nothing on them |
| array-copied cells, one pose | four poses (waving; Steve shielding the Noob; both running; the Noob reaching for a dark cube), each cell turned 0/90/180/270 at random, varied spacing and height |
| Patch's close-up: static eye, Steve's shoulder cut in on the right, blocky clutter | 85 mm, Patch alone, centred, the grid in soft bokeh; the eye dims ~40%, flickers once, drops ~5 degrees on "...I stopped counting." |
| a cartoon whip-zing after "...I stopped counting." | nothing; the grid breach later gets a crystalline shatter and a sub-bass void tear |

## Decisions (ours)
- **Lines.** All nine original takes (`movie/ep07_published`, rebuilt from run 41463846907): "Hey, that's me!",
  "What are those?", "Every time you respawn, something stays behind.", "...Where does it go?", "That's... us?",
  "From last time.", "How many times have we done this?", "...I stopped counting.", "I don't want to be deleted.".
  **One new take:** Patch's "It found the archive- I only have one stable coordinate left!" (the creator gave two
  versions of the breach line; we use this one because "one stable coordinate" sets up Ep8's landing at Steve's
  portal). Patch's voice gets the movie's `patch` chain (as in Ep4-6).
- **Sound.** Ep6's warp chime tail rings over the cut (hit 0.25 s before it); Ep6's void wind under the first 1 s,
  cut under the landing; then the published `memory` cue (music box over a warm pad, tape-warped) for the whole
  grid, its hit (braam, choir) on the infinite pullback, **cut dead on the breach**; a faint electric room tone;
  all dialogue in a subtle wide digital hall (decay 1.1 s, 13% wet, high-pass 250 Hz: `voice_hall`, new) so Ep8's
  outdoor forest feels physical. The breach: a crystalline shatter + a sub-bass tear, the erase sound on the cells,
  crackle, a rumble rising under Patch's line, the turbine/charge of the warp, and Patch's chime on the white-cyan
  flash (the same as Ep6's: his warp signature), ringing into Ep8.
- **REALITY:** 52% (Ep6's end) until the breach; it flickers 41 / 52 then drops to 30% (the movie's white bar).
- **Where:** the Memory Grid, a new place: an endless translucent blue floor of glowing cyan grid lines (3 m cells)
  over layers of fainter grids below, in deep abyssal blue-teal (#030B14 at the horizon, #0A2438 mist; a volume of
  density ~0.01 fading the far lines into cyan-navy). The memory pads are glass slabs (IOR 1.15, Fresnel edge
  emission, thin cyan wire borders). The real trio arrive on a pad at the origin; the replay pad 3 m ahead (+y);
  the core far below (z -30); the past-loop trio one cell off to the side; the field of cells all round.

## Places (metres; the floor at z 0; the cameras mostly from -y looking +y)
- Arrival pad A (4 x 4) at (0, 0). Steve lands at (-0.9, -0.3) facing +y; the Noob at (0.9, -0.1) (on his back,
  head toward -x); Patch at (0, 0.4, 2.2).
- Replay pad R (2.5 x 5) at (3.4, 3.2): the ghost spawns at (3.4, 1.4) and walks +y; the red kill-brick at (3.4, 4.3);
  the dark cubes land at (2.9..3.9, 4.6), the third one already there from an earlier loop.
- The core: a sphere ~4 m of black blocks at (4, 8, -30) seen through the translucent floor and the layers.
- The past-loop cell P at (-6, 7): hologram Steve, Noob, Patch reaching toward a fissure at (-6, 10).
- The field: cells every ~11-13 m (jittered) out to ~150 m, each a pad, a hologram group (one of four poses, random
  quarter turn), a fissure behind it.

## Shots (times from the local sound build, 51.46 s; the CI voices run fixes them)
| # | time | lens | what | line |
|---|------|------|------|------|
| 1 | 0.0-6.8 | 28 mm wide, low, from (-1.5, -7, 1.0) | Ep6's cyan flash (the lens wash) clears over 0.7 s onto the grid; tumble (0.7-2.2): Steve lands to one knee (empty-handed), the Noob flat on his back, Patch wobbling; settle (2.2-4.2): Steve rises, the Noob hops up, turns, fascinated; spot (4.2-6.8): the Noob sees his hologram pop up on pad R and walk toward the red brick; a slow push-in | - |
| 2 | 6.8-12.1 | 35 mm medium-wide from (-0.5, -5.5, 1.5) toward (2, 3) | the real pair left, the replay right: the ghost hops onto the brick, shatters into glowing wireframe limbs, a pitch-black starry cube thuds down, a new ghost pops up; the Noob points, raised brows, lip-sync; the second loop, the second cube | "Hey, that's me!" (9.2) |
| 3 | 12.1-13.2 | 50 mm MCU on Steve from the front-left | his eyes and head turned down to the cubes (never the lens), wary flat brows | "What are those?" (12.1) |
| 4 | 13.2-18.2 | 40 mm, a slow tilt down from (3.4, 1.2, 1.4) | three trembling dark cubes on the glass; Patch drifts into frame beside them, eye toward the pair | "Every time you respawn, something stays behind." (14.8) |
| 5 | 18.2-24.2 | 24 mm, a vertical crane drop from above pad R down through the grid layers | the cubes rain down like dark snow, spiralling into the churning core with magenta cracks; the Noob leans over the pad's edge (seen from below through the glass), smile gone | "...Where does it go?" (21.4) |
| 6 | 24.2-26.2 | 45 mm medium past the hologram trio in cell P | the recorded trio reaching toward a looming jagged black-and-magenta fissure; scanlines, Fresnel edges | - |
| 7 | 26.2-29.6 | 65 mm close-up on the Noob | slow blink, furrowed brows, a solemn mouth; no smile on Patch's line | "That's... us?" (26.2), "From last time." (28.3) |
| 8 | 29.6-36.1 | 24 mm, one continuous crane pullback (up and back from the trio to ~40 m high) | hundreds of varied cells, each with its fissure, into the mist; the music's hit at 29.6 | "How many times have we done this?" (31.0) |
| 9A | 36.1-39.4 | 85 mm, shallow focus, Patch centred | Patch exhales; on the line his eye dims ~40%, flickers once, drops ~5 degrees | "...I stopped counting." (37.4) |
| 9B | 39.4-44.9 | 50 mm two-shot | the Noob looks out over the ghosts, lowers his hands; Steve glances at him with quiet guilt | "I don't want to be deleted." (40.8) |
| 10 | 44.9-51.5 | 28 mm wide, low | black-and-magenta cracks spiderweb across the floor under their feet; pads shatter, near cells dissolve into black; REALITY 52 -> 30; Patch's eye flashes amber; his warp ring flares cyan; the frame flashes white-cyan: cut to Ep8 | "It found the archive- I only have one stable coordinate left!" (46.7) |

## Picture recipes (from the blueprint)
- World: a gradient sky (#030B14 at the horizon to #0A2438 above), a volume (density 0.008-0.015) so the far grid
  lines fade into cyan-navy; the floor an emission grid (cyan lines on a faint translucent blue), two fainter grid
  layers below (z -8, -18).
- Pads: glass/transparent (IOR 1.15) + Fresnel edge emission, thin cyan wireframe borders.
- Holograms: the rigs with one hologram material: Fresnel edge emission (cyan), a horizontal scanline (wave texture)
  mixed with transparent, a slow flicker; nothing parented on them.
- The kill-brick: a faint translucent red neon slab. The ghost's death: limbs drift apart as glowing wireframes
  and fade; a starry black cube (Ep4's dark cube material) drops and lands with a small bounce.
- The core: ~300 small black blocks orbiting a centre (swirl, inward drift), a magenta crack emission inside, a
  faint magenta light; no figure.
- The field: 4 hologram groups instanced on jittered points, a random quarter turn, a fissure (jagged black slab with
  a magenta emissive edge, translucent) behind each.
- Faces: the Noob worried brows and a solemn mouth from shot 3 on, lip-sync on every line; Steve flat, wary; Patch's
  eye dims, flickers, looks down on his line, flashes amber on the breach line.
- Steve's hands empty; the Noob's hammer gone.
