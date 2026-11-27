# Movie Episode 6: "The World Started Deleting Itself" (16:9, ~46 s)

The creator's rewritten blueprint (2026-11-27). Episode file `episodes/movie_ep06_deleting_itself.json`; sound
`movie/ep06`; renderer `src/lookdev/movie_ep06.py` (imports `movie_ep05`). Null is **not** on screen: the threat is an
unseen Void Wall; his silhouette stays a surprise until the Ep8 portal / `ep10_part1_null_entrance`.

## Decisions
- **Lines.** Original takes from `movie/ep06_published` (rebuilt from run 41223595607): "The world is DELETING
  itself!", "Then we stop it.", "...My pickaxe.", "Wall!", "It deleted the BOOM!", "It's not attacking. It's
  correcting.", the Noob's "...Hi?". **New takes** (CI voices run): Steve's "...No wall." (the movie gives it to
  Steve, deadpan; the Noob's published take is kept `unused`), Patch's "Stop throwing things at it!" (before the
  original "It's not attacking..."), the Noob's "It's copying me!", Patch's "Hold still- I'm pulling us out!".
  Dropped: Patch's "Oh no." (not in the blueprint), Null's published "...Hi?" take.
- **The void's "...Hi?"** is the Noob's own take processed (`mimic_of: noob_hi`): -6 semitones, partly stretched,
  a reversed 1.2 s dark-hall pre-echo breathing into it, ring-mod + bit-crush 15% wet, a dark room after.
- **One erase rule** (Ep5's material and `erase` sound) for the dragon, the pickaxe, the wall, the TNT and the
  terrace corner. REALITY 71 -> 66 (dragon) -> 62 (pickaxe) -> 57 (TNT) -> 52 (the surge).
- **Sound arc:** Ep5's void drone carried on (offset 7.112) into a pulsing `industrial` drone (no melody) under
  the attempts; the TNT fuse (`fuse_rise`) crescendo cut to dead silence on the checkerboard frame, then a faint
  blip-vacuum; a high dissonant `tremolo` under Patch's scan, cut dead; total silence with sub-50 Hz `pressure`
  for both "...Hi?"; a `turbine` swell + charge to the cyan flash, the warp chime ringing over the cut into Ep7.
- **The seam:** opens on Ep5's last instant (level matched: Ep5 ends -33.9 dB, Ep6 opens -34.2 dB); ends on the
  cyan-white flash that Ep7 opens on (the Memory Grid).

## Shots (times from the local build; the CI run fixes them)
| # | time | lens | what |
|---|------|------|------|
| 1 | 0.0-7.4 | 28 mm low, behind Steve & the Noob, slow push | Ep5's last instant; the Void Rift rolls across the sky (overcast shadow, magenta rim light); its edge erases the sealed dragon tail to head; "The world is DELETING itself!" |
| 2 | 7.4-10.1 | 50 mm MCU Steve | eyes track the last pixels, harden; stance, pickaxe in both hands; "Then we stop it." |
| 3 | 10.1-15.0 | 35 mm 3/4 front, then 40 mm side tracking | wind-up, overhand throw, the spinning arc, 4-frame hit-freeze, checkerboard, implode; Steve's blink; "...My pickaxe." |
| 4 | 15.0-21.0 | 32 mm wide two-shot | "Wall!"; cyan wireframe, stone barrier drops; the void glides into it, one bottom-to-top dissolve; Steve: "...No wall." |
| 5 | 21.0-26.3 | 45 mm on Steve, then 35 mm wide | TNT lit, thrown, fuse rising; white flash snatched to checkerboard, dead silence; the Noob whips round: "It deleted the BOOM!" |
| 6 | 26.3-32.8 | 40 mm, Patch front-left, wall right half | Patch banks, scan cone on the wall's magenta edge (Patch_ScanTarget), readouts; "Stop throwing things at it! It's not attacking. It's correcting." |
| 7 | 32.8-40.3 | 65 mm on the Noob, then 35 mm dead centre into the black | silence; worried brows, small wave at chest height, no hammer in frame; "...Hi?"; two beats; a 6-8 frame static ripple deep in the black on the void's "...Hi?" |
| 8 | 40.3-46.1 | 28 mm wide pullback | the wall surges, swallows the terrace's front corner; "It's copying me!" / "Hold still- I'm pulling us out!"; Patch's cyan ring expands; the frame flashes cyan-white: cut |

## Picture recipes (from the blueprint)
- Void Wall: a curved plane ~40 x 30 m, drifting from 8 m off the front edge to 1.5 m by the surge; pure black
  (roughness 1, specular 0); a displaced stepped-noise leading edge with a transparent + pink/black checker
  emission rim (strength 3) and cubic debris; a magenta-violet area light on it; world sky strength keyed down 50%.
- The static ripple: a plane 0.5 m in front of the wall's centre, a stretched horizontal wave+noise alpha, 0 until
  the void's word, flickering 0.2-0.7 pale magenta/white for 6-8 frames, back to 0.
- Pickaxe: Child Of Steve's right hand, influence 1 -> 0 on release, a keyed parabola with -720 deg spin over 12
  frames, Constant interpolation for 4 frames at the hit, then the erase material.
- The Noob's hammer: only on his right hand (Ep5's `sr` child); hidden after he drops it in panic after shot 4, so
  nothing pokes into shots 7-8. Patch's rear casing bulge removed; the scan cone aimed at Patch_ScanTarget.
