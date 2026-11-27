# The movie: FINALE 1/5 (16:9), shot by shot

Source: the published Short "The Glitch Said HI... Then It Chose the Noob (FINALE 1/5)" = parts 1-3
(`preview-ep10_p1_entrance` run 42937616639, `preview-ep10_p2_omg` run 42952199184, `preview-ep10_p3_run` run
43015597357), studied at 4 frames a second. Renderer `src/lookdev/movie_finale1.py` (one scene for the chapter; it
drives `ep10_entrance` / `ep10_p2_omg`'s published choreography and re-stages part 3). Sound `movie/finale1`
(`tools/movie_finale1_join.py`), 27.12 s.

## The creator's notes (2026-11-27), and what was done

Times are the published Short's (P3 starts at 0:13.6 there).

| Note | Fix |
|---|---|
| Pink floor rectangle 0:26.5-0:28.5 | It was Null's world-erase effect: the 4x4 terrain chunks deleted behind them, the sky's pink horizon seen through the hole. The ground deletion is off in part 3 (the grass stays); area lights are also invisible to the camera everywhere. |
| Steve's teleporting pickaxe | The pickaxe (`item_iron_pickaxe`, held since `ep10_p2_omg.build`) is hidden for the whole chapter: he runs empty-handed (erased in Ep6). |
| Lighting cliff 0:26-0:27 | A wide soft violet area fill (`run_fill`, 9-15 m) runs with them, ahead and above; the cold rim follows them too. It fades as they reach the boulder (it blew out the boulder's top in the overhead). |
| 6 s dead delay after "RUN!" | The slow-motion turns, the POV and the empty whip-pan are cut. A 1.2 s slow-motion shock beat (Null's grin looming, specks hanging still, ear ring, one heartbeat) now sits *before* "RUN!", and the shout hard-cuts (0.3 s in) into them sprinting at full speed. |
| Retro synth-funk on the chase | New cue `war_drums` (`src/music.py`): taikos and mid toms on a war pattern, a dry snare rattle, a dark saw bass pulsing on sixteenths, a dissonant spiccato string ostinato (D / Eb / Ab). Null's drone stays under the dialogue and comes back at his choice. |
| The ending must read without text | The overhead split is held 2.1 s (was 1.6) from higher and steeper (the boulder no longer hides them). Null's face looks down; a 0.4 s flick left (to Steve), then a snap right on a distortion chime (glitch, crunch, a low chime, a sub drop): from his right, so the grin snaps into the lens. Then a new 1.6 s wide: Null banking down the right path after the Noob, Steve small and ignored on the left. No end card. |
| Frozen dialogue shot | Panic breathing on chest, head, arms (about 1.5 degrees at 2.3-2.6 Hz, a little irregular); the Noob's arms down in a hunched guard (no arm held straight out); Patch bobbing, his eye darting up to Null; a slow creep in. "What's the signal?" is a close-up of the Noob. |
| The Noob's blown-out, faceted head | Roughness 0.58+, Specular IOR Level 0.25, coat down; head shaded smooth by angle (35 degrees) + weighted normals; the magenta rim (`null_key`) at 65% on his close-ups. |
| The Noob's stiff run | Spine forward (chest_lean 22, the whole body tipped 10 degrees from the feet), arms pumping from a forward bias (his Roblox arms have no elbow: the bend is in the swing), a 1 s panicked glance back over his shoulder. |
| Patch a white blob, lost on the split | His casing dimmed to 40% while flying (a gain on its colour), facing where he flies so his cyan screen reads; at the split he banks right and stays with the Noob, glancing back at Steve. |

## The seam with Ep8

- Ep8 hard-cuts into frame 1 of P1 (the claws through the membrane). P1's set is the reference Ep8 matches
  (`ep10_entrance.build`: the portal at (0, 5, 0) facing -y, the clearing, the oaks); `movie_ep08.py` was not yet
  pushed when this was built: check its 5B camera against shot 1A once it is.
- **The storm is seen arriving:** P1 opens on Ep8's indigo twilight (zenith #070B1A, violet horizon) and the sky
  blends into Null's storm over 1.3 s (`TWILIGHT` -> `STORM`), the rip's flash on top.
- **Who is in frame:** Steve and the Noob stand in front of the portal from frame 1 (frozen as P2 opens them), Patch
  hovering just behind them between their heads; seen in P1's wide (1D) under the rising Null.
- REALITY 12% (Ep8's end): the meter holds, so the movie's meter stays hidden (it shows only on drops).
- Sound: P1's own soundtrack from its 0; Ep8's stone groan pre-laps the cut.

## Shots (chapter time, 24 fps; 16:9)

**P1: the entrance (0 - 7.08), published timing**
- 1A 0-1.75 Close beside the membrane: the claws through, feeling, gripping. Lens x0.62 (the frame and the forest at
  the sides). The storm rolls in.
- 1B 1.75-3.45 Low, from the front: both claws strain, the rip (flash, shake). Lens x0.7.
- 1C 3.45-5.43 Close at the opening: the membrane, the face behind, the burst, "HI!" (4.1). Lens x0.66.
- 1D 5.43-7.08 Wide, low, from the front-right (new place, 16 mm): Steve and the Noob in the mid-ground, Patch
  behind them, the rift tearing up and the whole of Null rising over them.

**P2: "Oh... My... God..." (7.08 - 13.60), published timing**
- 2A 7.08-10.68 Steve's face, side view from below; the words keyed by hand; lens x0.7 (the Noob's yellow soft at the
  edge of frame, the night beside him).
- 2B 10.68-12.03 Low at his feet: the slide back, the crouch. Lens x0.66.
- 2C 12.03-13.60 The Noob's face: "...Steve?"; Patch soft behind him; the rim down 35%, the new skin. Lens x0.7.

**P3: "RUN!" (13.60 - 27.12), re-paced (`episodes/movie_finale1_p3.json`)**
- 3A 13.60-15.97 The frozen two-shot from Null's side, a slow creep in: the Noob left (hunched guard), Steve right,
  Patch between and above; breathing; "On my signal... we split."
- 3B 15.97-17.25 Close on the Noob: "What's the signal?" (a small crash in).
- 3C 17.25-18.20 The shock, slow motion (the world at a fifth of its speed): low, up at Null's grin looming over
  them, specks hanging around the lens; ear ring, heartbeat, a sub drop.
- 3D 18.20-18.75 Close on Steve: his eyes slide to the Noob; "RUN!" (18.45), crash zoom.
- 3E 18.75-21.32 Hard cut: full speed at the camera, Null and the rift behind; the fill with them; Patch above
  between them; the Noob glances back (19.75-20.7). War drums.
- 3F 21.32-23.42 High and steep, held: the path forks at the boulder: Steve left, the Noob right, Patch banking right
  with him.
- 3G 23.42-25.02 Up at Null's face from his right (the Noob's side): looking down; flick left 23.72 (held 0.4 s);
  snap right 24.14, the grin into the lens; the chime.
- 3H 25.02-27.52 Wide, low, from ahead: Null banking down the right path after the Noob (right of frame), Steve small
  on the left path, ignored. The chapter ends here (FINALE 2/5 picks up).

## What FINALE 2/5 picks up
Steve on the left path (about x -9, y -31), the Noob on the right (x +9) with Patch, Null banking after the Noob
(neck near (7.5, -21), yaw 38, lean 38), the war drums and Null's drone hard-ended at 27.12 s.
