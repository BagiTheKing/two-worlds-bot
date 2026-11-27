# Episode 5 "Noob Found Creative Mode": the movie (the creator's notes, 2026-11-27)

The published Short (`preview-ep05_creative_mode`, 29.2 s) was a sketch in the old look: a cold open with upbeat
music and a hammer from nowhere (Ep4's lore bomb ignored, the giant cube gone), the old pink REALITY text jumping
85 -> 71 at the end, the dragon frozen in the sky then gone between cuts, the door clipping through its pad, Patch
scanning empty sky, the hammer jammed on the hand and poking out of the hip, the Noob smiling through "Where's my
duck?" and Patch's warning, Steve frozen like a statue, the four freed players cheering while the world deletes,
three different deletion looks, arcade bleeps under the cascade, the door gag and the twist rushed. The creator's
notes (word for word in the session that made it) gave a full ~60 s blueprint; this is it as built.
Timing: `episodes/movie_ep05_creative_mode.json` (55.4 s). Picture `src/lookdev/movie_ep05.py`.

**Decisions (ours):**
- **The seam:** Ep5 opens on Ep4's last camera (Steve's alarmed glance) and instant; Ep4's poses go on (its own
  code, posed at Ep4's time) for the first 1.2 s, then the Noob's eyes slide to the cube. Ep4's `deleted` cue goes on
  (same seed and level, its note already fallen: `fall_at`), raised to match Ep4's last second at the cut.
- **How the block gives him the power (shown):** the third poke: a pink flash and no zap; the 1.45 m cube implodes,
  folding into a stream of magenta-cyan code that pours into his fist and condenses into the BTools hammer. Patch's
  added line, "Wait- don't-", is cut off by the poke. REALITY stays at 85 (it took nothing from the world).
- **Where the builds go (all in Ep3's obby, nothing from nowhere):** the duck on Ep4's white spawn ring beside him
  (the spawn plate on the grey pad is under the sealed dragon's crystal); the statue on the checkpoint east (dark
  grey pad); the castle on the violet ledge's west end; the door at the terrace's front edge, facing the open sky.
- **BTools materialize (8 frames, every build):** Studio's blue selection box snaps (first frame white), a cyan scan
  plane rises through it (solid below, nothing above), the thing pops with a 1.04 -> 1.0 bounce and square dust puffs.
- **One erase rule (every deletion):** checkerboard sweeping top to bottom, sliced into nothing by a ragged front
  trailing it, a dozen dead pixels rising (one material: `erase`). The same sound every time (`erase`: a digital
  tear, an inward suction, a 60 -> 30 Hz vacuum drop, cut dead; 0.15 s of dead air after it).
- **REALITY, one drop per erasure:** duck 85 -> 82, castle -> 80, statue -> 77, the course 75, 73, 71 (the movie
  meter, the same white segmented bar).
- **The twist reads:** after the Noob's builds, the original course goes: the five stones west of the terrace
  (the ones the four freed players ran off along in Ep3), nearest first, then the orange stepping stone and the
  checkpoint east, then the truss tower and its high stage. Only the grey pad, the blue terrace, the door and the
  dragon are left; the sun pales and cools.
- **The dragon:** Ep6 opens by erasing it (and the door): here it flickers violently into the missing texture
  with a scanline tear in the cascade and snaps back, still there. **The door stays** for the same reason.
- **The four freed players** are gone already (they ran off along the course at the end of Ep3).
- **The original takes** (`movie/ep05_published`, rebuilt bit-exact from the published prep); "NO!" pushed
  (+3 dB presence), "...That wasn't us." 3 dB closer and quieter. New take only for "Wait- don't-".

## Places (Ep3's obby; metres; the cameras mostly south looking north)

The Noob at Ep4's end (-6.95, -0.8), the poke (-5.95, -1.3), building from (-5.35, -1.55) (where the cube was),
beside the door (-6.75, -1.95). Steve at Ep4's end (-2.1, -1.3), a half step back from the duck (-2.35, -1.2).
Patch at Ep4's end (-5.45, -3.0, 1.85), watching (-4.7, -3.3, 2.05), over the empty ring (-6.2, -1.3, 2.4).
The duck on the ring (-6.9, 0.35); the statue (4.2x the Noob, arms up) on the checkpoint (8, -1, top 0.5); the
castle on the ledge (-9.0, 2.9, top 1.1); the door's hinge (-8.08, -2.2), 0.92 x 2.0, the leaf 4 cm above its sill,
swinging out 95 degrees over the drop.

## Shots

| Shot | From | What | Camera |
|---|---|---|---|
| open | still | Ep4's last instant: Steve's alarmed glance | Ep4's last camera |
| stunned | still+0.55 | the Noob's stunned face; a blink, his eyes slide to the cube | Ep4's stunned close-up |
| master | reach | he walks to the cube, finger out; Patch darts: "Wait- don't-"; the poke, a pink flash; the implode | Ep4's locked master (the ruler) |
| hand | implode+0.55 | the code pouring into his fist, the hammer forming with a flare | close on the fist |
| hammer | hammer | he looks at it, points it at the ring | the Noob, medium |
| duck | hammer+0.45 | the box round the ring, the scan, the duck pops; Steve's half step back | wide, south-east |
| build | noob_build | "I can BUILD stuff!" the hammer high, bouncing | the Noob |
| since | lower | Steve lowers the pickaxe: "Since when?" | Steve |
| block | noob_block | "Since the block!" the hammer lifted | the Noob, a little low |
| statue | statue | the swing east; the box; the statue slams down, dust, shake | wide, south-west |
| me | noob_statue | "A statue of me!" arms wide, the statue far behind | low, behind-left of the Noob |
| crane | crane | Steve's head up to its top, a blink down: "Why is it so big?" | low on Steve, the statue towering |
| see | noob_see | "So everyone can see me!" | the Noob |
| castle | castle | a swing back over his shoulder; the castle snaps onto the ledge | behind the Noob |
| pinch | pinch | Steve pinches his nose, points at the sky: "Build us a way home." | Steve |
| door | salute | the salute; the swing; the door at the terrace's edge | wide, south-west |
| open_door | open | he pushes the handle; it creaks open onto the sky: "Close enough!" | from behind the door, through it |
| stare | stare | Steve's deadpan stare, the wind through the doorway | Steve, close |
| chime | chime | the groove back for a bar; the chime; the duck erased (85 -> 82), the music cut dead | the two of them, the duck between |
| where | noob_duck | "Hey! Where's my duck?" worried | the Noob |
| scan | scan | Patch darts over the empty ring, the beam down on it, pink static | wide |
| patch | patch_delete+2.2 | "...deleting what doesn't belong."; the beam whips to the castle | Patch |
| castle_gone | castle_gone | the castle erased behind the Noob (82 -> 80) | behind the Noob |
| statue_gone | statue_gone | the statue erased top to bottom (80 -> 77); the Noob steps toward it | over Steve's shoulder |
| no | noob_no | "NO!" hands out | the Noob |
| dragon | dragon | the sealed dragon flickers into the missing texture, a scanline tear; it snaps back | up at it |
| west | hush | silence; the five stones west go one by one (75, 73) | locked on the course |
| east | stairs_gone+2.3 | the stepping stone and the checkpoint go (71) | east, Steve on the pad |
| void | stairs_gone+2.9 | the truss tower goes; two pads in the empty sky | the lonely wide |
| us | steve_us-0.15 | Steve, staring where the stones were, turns slowly: "...That wasn't us." | Steve, close |
| hold | hold | the three of them, the door, the dragon; the wind | wide |
