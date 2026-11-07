# Look development: Steve at the reference quality bar

This is the work that took Steve to the level of the reference animations
(Benly). Every part was studied frame by frame in the reference, then built
and checked side by side.

| file | what it does |
|---|---|
| `hair.py` | 3D hair: a shell of one-pixel strips (fringe, sides, back, cap), each strip made of pixel-sized pieces in varied browns. It follows the head bone and the face lattice. |
| `faceplate.py` | The face: a thin plate over the front of the head. A shader draws the eyes (top and bottom lids as curves, rounded corners, a socket shadow, a square pupil with rim and catchlight) and the mouth (dome or lens openings, teeth slivers, tongue, a closed line). All settings are custom properties, so they can be keyframed. It also flattens the rig's old lips. |
| `brows.py` | 3D brows with shape keys: raise, tilt, arch, curl and squeeze. |
| `skin_face.py` | The painted 8x8 face (pink skin, cheeks, nose, beard rows) and the body palette (cyan shirt, violet trousers, dark collar V, pixel shading). |
| `pose.py`, `poses_lib.json` | Posing in plain terms (body turn, hips, chest, head, arms, elbows, feet) and 19 named poses. |
| `props.py` | Items from their 16x16 sprites, built as 3D pixel slabs one pixel thick. They are held in the fist (`hold`, with `GRIPS` presets: hanging, raised, swing), as held blocks, or as dropped items that float and turn. |
| `noob.py`, `noob_lab.py` | The Noob, built in code: the classic R6 body with a Minecraft-style pixel skin (chosen; plain plastic and a subtle version also exist), the classic Roblox head (chosen) or a box head, a Roblox-style face (black oval eyes with a shine and lids, the shared mouth shapes, no brows), rigid-limb posing with 18 poses (`NOOB_POSES`), and tools held Roblox style (`noob_hold`). The lab renders his variants on one sheet. |
| `null.py`, `null_lab.py` | Null, rebuilt from the series thumbnail: a glowing magenta and black missing-texture checker head (the classic Roblox head shape); a near-black voxel body that is solid at the core and ragged at the edges; long arms with dripping claws; a lower body that dissolves into a debris trail. Glitch pixels and scanlines run over him, and two rings of Minecraft, Roblox and missing-texture blocks orbit him with trails. He floats. `look.py` adds him with `NULL={...}`, plus a storm sky, a cold back-glow and pink and cyan rim light (the `storm` shot). The lab shows him alone in a storm studio. |
| `lips.py` | A simple lip sync: one mouth shape per frame from the voice (loudness and hiss). |
| `face_lab.py` | A studio sheet: renders many face or pose variants side by side. |
| `look.py` | The test world: a meadow, a forest hill, blocky clouds, sun and edge lights, the Standard view transform. Shots: `close`, `full`, `wide`. |
| `grade.py` | Applies the episode grade (`assemble.grade`) to a still. |

Key findings:

- Render with the **Standard** view transform. AgX drains colour from bright areas, and that was why our renders looked pale next to the reference.
- The rig's own face deforms into blobs, so we draw our own face on top.
- Light linking does not reach a collection instance, so edge lights are narrow spots aimed at the character.

Run (Blender as a Python module):

```
TWB_ASSETS=/path/to/assets python3 src/lookdev/look.py out/prefix 1080 64 close,full \
  # EXPR='{"face": {...}, "brows": {...}}'  POSE="idle (Benly 2.2)"
BLANK=1 FACE=1 python3 src/lookdev/face_lab.py variants.json sheet.jpg 300 16
```

`TWB_ASSETS` must hold the MCprep pack (`mcprep/resourcepacks/...`). It is not in the repo,
because its block textures come from Minecraft.
