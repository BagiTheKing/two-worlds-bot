# two-worlds-bot

The pipeline behind **Two Worlds. One Glitch.**: animated YouTube Shorts in which
a blocky survival world and a plastic obstacle-course world collide. The cast
are 3D rigs rendered by Blender on the CPU, so characters look identical in
every shot of every episode. Voices are local (Kokoro), sound effects are
synthesised, and nothing in the frame comes from a video model.

Built from the Failure Point pipeline (`BagiTheKing/failure-point-bot`); its
writer chain, uploader, posting gate and analytics carry over in later steps.

## How an episode is made

| Step | File | What it does |
|---|---|---|
| 1 | `episodes/*.json` | The episode: cast voices, and an ordered list of beats (actions) and dialogue lines |
| 2 | `src/textures.py` | Draws the pixel textures and faces (original art, from code) |
| 3 | `src/audio.py` | Voices every line (Chatterbox, acted per line; Kokoro for quick local tests), then lays out the timeline: beats get their durations, lines get their spoken length. Synthesises the sound effects, adds the score (`src/music.py`, composed in code) and mixes. Writes `build/timeline.json` and `build/audio.wav` |
| 4 | `src/build_episode.py` | Builds any episode in Blender from its file and the timeline, and renders frames. Its parts live in `src/kit/`: worlds, rigs, actions, effects, cameras. (`scene_poc.py` is the hand-written proof of concept, still used for episode 1's forest) |
| 5 | `src/assemble.py` | Upscales to 1080x1920, draws the overlays (REALITY meter, episode label, achievement, title and end cards), burns in captions, encodes the MP4 with the audio |

Because the audio decides the timing, every punch, cut and head-bob lands on
its sound and line.

## Run it locally

```
pip install -r requirements.txt bpy
# Kokoro model files into models/ (see the workflow for the two URLs)
python src/textures.py build/tex
python src/audio.py episodes/ep00_poc.json build
python src/scene_poc.py build/timeline.json build/tex build/frames --res 720 --samples 16
python src/assemble.py build/timeline.json build/frames build/audio.wav build/episode.mp4
```

Look-dev without rendering the whole episode:
`--stills 60,190,340` renders just those frames.

## Run it on GitHub Actions

**Actions → Render episode → Run workflow** (pick the episode file). One runner makes the
voices and the timeline, sixteen render frame ranges in parallel, and the last
one assembles the Short and pushes it to the `preview-<episode id>` branch.

## Ground rules

- Original models, textures, sounds and music only; no game assets or logos.
  The channel is unofficial and says so in every description.
- YouTube's synthetic-content label covers realistic footage; this is
  stylised animation. The real risk is the "inauthentic content" policy
  (mass-produced, repetitive uploads), so every episode tells a new story.
- Decide the "made for kids" setting deliberately for the channel.
