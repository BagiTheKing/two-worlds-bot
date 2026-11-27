# Episode 4 "This Block Shouldn't Exist": the movie (the creator's notes, 2026-11-26)

The published Short (`preview-ep04_the_block`, 29.6 s) was a sketch in the old look: a grey void, the old rigs,
the dragon cleanly dark again, a cube floating down with no tear, "I touched it!" in a wrong-sounding voice, the
cube not visibly growing, Patch gliding in from nowhere with a rigid eye, its scan laser through the Noob, stray
dark cubes, REALITY jumping 92 -> 85 at the end in the old pink text, an end card naming a Patch nobody named.
The creator's notes (word for word in the session that made it) gave a full ~60 s blueprint; this is it as built.
Timing: `episodes/movie_ep04_the_block.json`, sound `movie/ep04` (53.2 s). Picture `src/lookdev/movie_ep04.py`.

**Decisions (ours):**
- **The seam:** Ep4 opens on Ep3 v3's last camera and instant (Ep3's last 8 frames now hold the missing texture,
  so the shudder carries straight across the cut). The world is Ep3's (`movie_ep03.build`), posed at Ep3's last
  instant by swapping Ep3's beat table in (`ep3_world`).
- **The dragon's fate:** after the block rips out of its chest it snaps back to its dark scales, and the glitch
  crystal that held the frozen players grows over it, wingtips first, and seals it where it hangs: a frozen statue
  in the sky for the rest of the episode (seen behind the twist).
- **Where Patch comes from:** out of the portal they came through (a cyan pixel-warp on its membrane), not out of
  thin air.
- **The spawn ring** on the blue terrace lights up when the Noob belly-flops onto it (a checkpoint touched), so it
  is not there before it is needed.
- **The dark cubes** (the bible's planting rule: one drifts from every Noob death; Null is made of them, Ep7
  replays them): kept, one per death, slow, drifting up and away off-centre; the random extras are gone.
- **Patch is named on screen** ("I'm Patch. I find glitches.", added) and the tether's rule is said ("It's feeding
  on your respawn loop.", the creator's line). "I touched it!" re-recorded in the Noob's voice. Every other line is
  the published take (recovered: `movie/ep04_published`).
- **The second touch** is one karate chop (the Short's three-death spree folded into it).

## Places (Ep3's obby; metres; the cameras mostly south looking north)

Grey spawn pad x -3..3, y -2.5..2.5 (top z 0); the portal behind it (0, 4.6, 1) facing -y; the blue terrace west of
it x -10..-4, y -2.5..3.5 (1 m gap), the violet ledge on its back edge. The frozen dragon's root (-1.0, 0.8, 5.2),
head (-3.0, 3.6, 5.1). The spawn ring (-6.9, 0.2); the cube (-4.85, -1.55), hovering 0.15 above the terrace;
Steve at the pad's west edge (-2.55, -1.0), his step back (-2.1, -1.3). Patch: out of the portal (-1.6, 4.3, 3.3),
stops (-5.98, -1.2, 1.55), scans from (-4.25, -3.3, 1.6), drifts to (-5.45, -3.0, 1.85).

## Shots

| Shot | From | What | Camera |
|---|---|---|---|
| open | shudder 0.0 | Ep3's frozen dragon shudders in the missing texture, the Noob on its neck | Ep3's last camera |
| drop | tearoff 1.6 | the block rips out (magenta sparks), lands on the terrace and hovers; the Noob flung, tumbling, belly-flop on the ring (it lights) | wide, low, south-west |
| seal | crystal 3.8 | the crystal grows over the dragon; the Noob up on the ring; Steve looking up | wide, south-west, looking up |
| secret | noob_secret | the Noob crouched to the little cube: "A secret block!" | close, south-east |
| warn | lean | Steve at the pad's edge, pickaxe ready, leaning, waving: "It fell off the dragon. Don't touch it." | front of Steve, from the west |
| master | poke1 | the poke, the zap, the burst, one dark cube; the respawn, the tether, the shockwave, the cube to 0.85; "I touched it!" (fist pump) | locked master (the ruler) |
| grew | stare | Steve stares: "...It grew." (music out) | front of Steve |
| master2 | noob_again | "Again!", the run, the chop (Steve lunges), the burst; the respawn, the cube to 1.45 (pink light on the terrace); the wind-up | the same master |
| arrive | patch_in | the portal flickers, the warp, Patch pops out, steadies, banks across, stops between fist and cube | wide, south-west |
| stop | patch_stop | "Please stop doing that." (eye squinting) | south, the three in a row |
| react | react | Steve jumps back into a guard | front of Steve |
| cube | noob_cube | the Noob hops back, points both hands: "A talking cube!" | the Noob |
| name | patch_name | "I'm Patch. I find glitches." | Patch, three-quarter |
| scan | scan | Patch glides front right, the cone over the cube, the read-out bars | south-west, side on |
| feed | patch_feed | "It's feeding on your respawn loop. It grows every time you come back." | Patch |
| helping | noob_helping | fists on hips: "So I'm helping!" | the Noob |
| no | sigh | the pickaxe down, a look Noob/Patch/Noob: "No." (music cut dead) | Steve, from the south-west |
| turn | turn | Patch turns sharply, eye dilates, scanlines; "Wait. I know you." | over the Noob's shoulder (his head low left) |
| doyou | noob_doyou | the smile gone: "...You do?" | the Noob |
| two | drift | the two-shot push-in, Noob left, Patch right, the dragon and the portal between: "From a world that got deleted." | south-west, slow push |
| stunned / glance | hold | the Noob's stunned face; Steve's alarmed glance | close |
