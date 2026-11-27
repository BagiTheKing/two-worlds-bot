# Movie Episode 8: "Steve Was Hiding Something" — the hidden portal (16:9, ~61 s)

The creator's 16:9 blueprint and fixes (2026-11-27: `story/movie/ep07_ep08_notes_2026-11-27.md` points 1-3 and the
session's notes on the published Short). Episode file `episodes/movie_ep08_steve_hiding.json`; sound `movie/ep08`;
renderer `src/lookdev/movie_ep08.py` (imports `movie_ep07`, as Ep7 imports Ep6). **Null is never seen**: Ep8 ends
on the blazing violet portal and a magenta crack, a hard cut into frame 1 of `ep10_part1_null_entrance` (his claws
bursting through). **Never the obby** (except the one-frame glimpse through the first portal in the flashback).

**One place, one light, no seam with the finale.** Ep8 is built in the finale's own forest clearing (the set of
`ep10_part1_null_entrance` / `video_2.mp4`): tall grass, a dark oak forest, distant snow-capped voxel mountains seen
past the portal. The clearing is the same; only the time of day moves: golden sunset at the landing, deep twilight
blue by the forgiveness, and at the ignition the finale's exact light (deep indigo sky, the portal's violet bounce on
the grass and trees). Shot 5B frames the portal on the finale's camera plane, so the cut into Null's entrance is
frame to frame.

## What the published Short got wrong (the creator's notes) and what we do instead
| published | movie |
|---|---|
| 0:00-1.5 a scream next to Null in the obby | cut (Ep7 ends on Patch's emergency warp); Ep8 opens on the warp flash clearing onto the grass |
| a flat sunlit green yard, a solid 5x5 wall of leaf blocks round the portal | the finale's forest clearing; a freestanding obsidian frame under an oak, draped in hanging vines and 6-8 overgrown moss/leaf clusters, two of which Steve pulls off by hand |
| harsh flat midday sun throughout | the sun keyed from 12 degrees (warm golden, #FFBE85) at 0:00 to -4 degrees by the ignition; the world sky shifting to deep midnight indigo (#070B1A); the twilight complete by shot 4B |
| the BTools hammer clipping into the Noob's hip (0:02, 0:03-4, 0:11-14) | gone (the void took it in Ep6); Steve has no pickaxe either |
| a glowing white cube floating between their waists (0:23.5-26.5); a dark-green block hanging in the sky inside the portal (0:23-26.5) | nothing in the set that isn't built on purpose: the stills are checked for strays, the Outliner too |
| flashback: Patch's cyan laser into the empty sky, a white flash, translucent Steve frozen 5 s with one arm out, a purple cube clipping into his chest | a smooth desaturating dissolve into cool hazy twilight blue; past-Steve *acting*: sets the last obsidian block, strikes flint and steel, the portal flares (a split-second glimpse of colourful obby blocks through the violet haze, then dark purple static rippling round the edges), he steps back in quiet awe |
| the Noob's `:)` flash at 0:10.5 before "So all of this is your fault?" | no smile: hurt brows from the dissolve back on |
| frozen faces: `:o` held 3 s, `:)` held on "...weird blocks", Steve's dead stare through his speech | lip-sync on every line; the Noob's brows pinch then relax into a crooked smile; Steve breathes, looks down, blinks before "Your side", lifts his eyes to the Noob, dips them on "...what it would cost" |
| a stiff plank arm and a missed fist-bump (0:24-26.5) | a gentle shoulder pat: the Noob's right elbow bent ~45 degrees, his hand on Steve's left sleeve for 10 frames, then dropping to his side |
| 0:27 a blinding pinkish front light; both characters vanish for 0.5 s | dim ambient; the violet light comes from the portal behind the camera and sweeps across their faces; nobody vanishes |
| a cartoon sci-fi warble as they turn | a deep 45 Hz obsidian THOOM, the leaves rattling, the crackling plasma hum; the piano and the crickets cut dead |
| "...I didn't do that." in Patch's voice (the voice swap) | Steve's own deep voice, a breathless whisper close to the mic (a new take) |
| the portal: pastel swirl -> flat purple -> a window with a bobbing mini checkerboard face; NEXT: THE END card | the finale's deep violet plasma shader, one look; no face; no card; the magenta crack, then the hard cut |

## Decisions (ours)
- **Lines.** All eight kept lines are the original takes (`movie/ep08_published`, rebuilt from run 41851020512):
  "You had a PORTAL?!", "I built the first one. Before I met you." (now voice-over on the flashback), "That's
  where it started." (voice-over), "So all of this... is YOUR fault?", "I wanted to see the other side. Your side. I
  didn't know what it would cost.", "...I touch weird blocks all the time.", "That's not the same.", "Kinda is.".
  **One new take:** Steve's "...I didn't do that." (the published line was Patch's: kept `unused`). The two
  screams are cut (kept `unused`).
- **Sound.** Ep7's warp chime rings over the cut (0.3 s before it). Ep8 is dry and outdoors: a new `evening`
  ambience (a light breeze through the oaks, a leafy rustle on the gusts, faint crickets fading in as the light goes),
  in sharp contrast to Ep7's hall. No music on the landing (0-11.5 s): grass, vines, steps. The published
  melancholic score from the flashback to the ignition: the `memory` cue over the flashback, `theme_soft` under the
  confession and the forgiveness (swelling a little on the quiet two-shot), **cut dead on the ignition** with the
  ambience. The ignition: `obsidian_boom` (a 45 Hz THOOM, leaves rattling), `plasma_hum` (the violet plasma's
  crackling hum), then on the dread hold the hum nearly gone over a faint `pressure` sub; `plasma_crack` on the
  magenta crack; `stone_groan` 0.25 s (6 frames) before the end: the J-cut into Null's claws gripping the frame.
- **REALITY** 30% (Ep7's end) until the ignition; it fractures 21 / 30, then 12% (the movie's white bar).
- **Light** (keyed on the beats): sun elevation 12 degrees (#FFBE85) at 0:00 -> ~6 degrees at the flashback's end
  -> 2 degrees at the confession's end -> -4 degrees by `hush` (51.9 s); the sky from warm amber to #070B1A.
  The flashback is its own light (cool hazy twilight blue, desaturated). A violet area light (#B833FF) inside the
  portal frame: 0 W until `ignite`, ramping to ~220 W over 0.4 s. No front fill on the turn.

## Places (metres; the ground at z 0; the clearing of `ep10_part1_null_entrance`)
To be fixed against the finale renderer's set when `movie_ep08.py` is written: the portal stands where the finale's
portal stands (its frame 4 x 5, freestanding, under an oak's canopy edge), the cameras of shots 5A/5B on the finale's
opening camera plane. Steve and the Noob land ~6 m in front of it, Patch hovering above them; the reconciliation
two-shot ~3 m in front of the frame.

## Shots (times from the local sound build, 59.9 s with a placeholder for the new take; the CI voices run fixes them)
| # | time | lens | what | line |
|---|------|------|------|------|
| 1 | 0.0-11.5 | 28 mm wide, low, golden sunset | Ep7's white-cyan flash fades down (0.6 s) onto the clearing, snowy peaks glowing faintly; tumble (0.6-2.2): Steve to one knee on the tall grass (empty-handed), the Noob rolling onto his back, Patch wobbling, steadying; Steve up first (2.2-3.6), walks quickly to the vine-choked archway under the oak (3.6-5.6), pulls two vine clusters clear (5.6-8.0): the ancient unlit obsidian frame; the Noob scrambles up behind him (8.0-8.9), genuinely shocked | "You had a PORTAL?!" (8.9) |
| 2 | 11.5-24.3 | 35 mm medium | a smooth desaturating dissolve (11.5-12.7) into the memory, cool hazy twilight blue: past-Steve sets the last obsidian block (12.7-14.3), strikes flint and steel (14.3-15.7), the portal flares open (15.7): a split-second glimpse of colourful obby blocks through the violet haze, dark purple static rippling round the edges; he steps back, watching in quiet awe; the memory dissolves back (23.3-24.3) | VO: "I built the first one. Before I met you." (17.3), "That's where it started." (20.8) |
| 3A | 24.3-28.5 | 50 mm MCU on the Noob, sunset rim | brows pinch in real hurt, shoulders drop, full lip-sync; no smile, no hammer | "So all of this... is YOUR fault?" (25.0) |
| 3B | 28.5-38.0 | 65 mm close-up on Steve, shallow focus, the peaks fading to indigo behind | head down -12 degrees (guilt), a slow blink, an exhale, Noise breathing on the chest (scale 30, strength 0.02); a 3-frame blink right before "Your side", his eyes rising to the Noob's eyeline on it, dipping again on "...what it would cost"; the sunset deepening after | "I wanted to see the other side. Your side. I didn't know what it would cost." (30.6) |
| 4A | 38.0-43.0 | 50 mm close-up on the Noob | his worried brow relaxes into a warm crooked smile, a slight playful head tilt, lip-sync | "...I touch weird blocks all the time." (39.2) |
| 4B | 43.0-51.9 | 35 mm warm two-shot in front of the unlit portal, the light now deep blue twilight | the Noob steps beside Steve (43.0-44.8), a gentle shoulder pat (44.8-46.3: elbow bent, hand on Steve's left sleeve 10 frames, then down); Steve's tiny reluctant half-smile; the Noob grins back; the two side by side (48.8-51.9) | "That's not the same." (46.3), "Kinda is." (47.5) |
| 5A | 51.9-54.5 | 40 mm two-shot | a deep violet glow sweeps across their faces from behind the camera (no white blowout, nobody vanishes); the THOOM; they freeze, then turn their heads slowly (head, then shoulders) toward the portal; REALITY 30 -> 12 | - |
| 5B | 54.5-~61 | 32 mm, a slow creeping push-in on the freestanding portal, dark trees and the snowy peaks behind | the portal blazing with the finale's deep violet plasma, purple light across the tall grass; Steve's whisper (off screen); 1.5 s of suffocating silence; a single bright magenta crack ripples across the sheet (~59); HARD CUT to frame 1 of `ep10_part1_null_entrance` | "...I didn't do that." (56.7, Steve) |

## Picture recipes (from the blueprint)
- The set: the finale's clearing (import its builder); the leaf wall of the Short is gone. The portal: a freestanding
  obsidian frame, organic hanging vines and 6-8 overgrown moss/leaf clusters draped over it; two clusters are
  separate objects that Steve's hands carry off (seen arriving in his hands, dropped in the grass beside the frame).
- Light: the sun lamp's elevation and colour keyed on the beats (above); the world sky blending to #070B1A; the
  violet area light (#B833FF) inside the frame, 0 W until `ignite`, then ~220 W; no front light on 5A.
- The portal plasma: the finale's violet shader exactly (the same material, the same strength), from `ignite`. The
  flashback's portal: the same shader with a split-second obby-block image mixed in and a dark purple static edge.
- The flashback: a desaturated cool blue grade (the compositor or a per-shot world/light swap), a soft dissolve both
  ways; past-Steve a solid rig (not translucent), animated: place (arm swing, a block arriving from his hand into
  the gap), flint (two strikes, sparks), a step back.
- Faces: the Noob shocked (shot 1), hurt brows (3A), relaxing into a crooked smile (4A, 4B), frozen wide eyes (5A);
  Steve flat and guilty, eyes down, the blink, the eyes up (3B), the half-smile (4B), dread (5A). Lip-sync on every
  on-screen line.
- Strays: no hammer, no pickaxe, no floating cubes or blocks; the stills are checked shot by shot.
