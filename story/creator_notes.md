# What the creator asked for and insisted on

Everything the creator has asked for, corrected or insisted on since the
first proof of concept (October 17) through the finale (November 13),
collected from the whole working conversation. **Every session reads this
before working, and follows it.** When a note here and a draft disagree,
the note wins. Add to it whenever the creator gives a new standing note.

## The standard

- **"We need to win."** The goal is a channel that grows (1M views on an
  episode was the stated ambition). Every video has to be better than the
  last; a series gets better as it nears its end, never worse.
- **Quality over speed, always.** "Take your time", "take all the time and
  credit you need", "no shortcuts", "each part should take its time", "put
  the effort of a whole episode into a 5-second part". Never rush a scene to
  save renders.
- **The bar is Benly Animations** (the animated Minecraft movie trailer and
  "Steve tries to SPEEDRUN", studied frame by frame; see the playbook,
  section 2c). Compare our frames with theirs honestly; don't call it close
  when it isn't.
- **A stranger must understand everything.** "Someone who knows nothing
  should understand what's happening."
- **Honest work:** the scenes are real 3D, built and animated; the voices are
  AI and we say so. Never claim "no AI" for anything that used it.

## How we work together

- **Part by part.** Agree the beats in words, then sound, then stills, then
  a preview, then notes, then the full render. Don't move on until the
  creator approves the part.
- **Send the sound preview first**, before any frame render.
- **Ask when unsure.** The creator says "ask me if you need more input"; a
  question costs less than a wrong render.
- **Give your own opinion; don't just agree.** If you disagree, say so and
  say why. When you propose a better version of a line or a shot, offer it,
  but the creator's version is the default.
- **Fix only what was pointed at.** Never change parts that were already
  good while fixing others ("why are the good parts changing and not only
  the bad parts where I point?"). If a redo makes things worse, restore the
  previous version and fix just the named things.
- **Keep earlier versions so they can come back.** The creator often prefers
  an earlier take: Episode 0's first ending, part 5's first glitchy deja vu,
  the first "I am running" with the echo, the "very first" whisper. Never
  throw a version away.
- **Don't re-render what already exists.** Reuse earlier frames and runs;
  re-render only the part that changed.
- **Give honest ETAs**, and send previews as soon as they are ready.
- **Focus and care.** Check your own work before sending ("this is not a
  normal mistake, it looks done on purpose"): frame each moment, watch every
  cut, listen to every line.
- **Model choice:** the creator lost faith in Fable after its first finale
  attempt ("a disaster": cut scenes, poor motion, the entrance not as
  described). Don't hand the creator's scenes to another model without
  asking.

## Story

- Open with a **big mysterious event** that shocks; build a series that
  makes people come back and rewatch.
- **Every episode picks up where the last one left off**, and the link is
  visible (Ep7 to Ep8: "how did they move from the void to here?").
- **Explain, but as questions, not confirmations.** Raise the theories, never
  confirm or deny a viewer's theory.
- **The canon** (`story/bible.md`): Null is made of the Noob's old respawned
  bodies; he follows the Noob, his "creator"; all Null wanted was to fix the
  world; Patch remembers; Steve built the trap and lived it 412 times.
- **Lines the creator wrote are used as written** (adjusted only on the
  creator's say-so): "Noob... that's you!! Every time you respawned.", "I
  never came back for you guys. Sorry.", "Steve, remember... I am a Roblox
  player.", "DON'T— We can find another way!", "Now I can bring everything
  back to normal.", "I will not allow this.", "We did it, guys.", "What do
  you think happens to anyone in the void?", "I'VE SEEN ENOUGH. HE'S
  LITERALLY COMING TO DELETE US." (the punchline), "STEVE, WAKE UP! THE
  BRIDGE IS...".
- **Lines must be short and simple** ("Playing the archive. Please keep your
  arms inside the timeline." was too long), and say what they mean ("I want
  to see the other side. Your side.").
- **No new idea in the last seconds**, one premise per episode, and the
  jokes stay in when cutting: cut only what earlier episodes already said,
  keep the explanations a stranger needs.
- **The movie** (long form, landscape, all in the new look) is **a remake of
  what already exists**: same story, same lines, same soundtracks, no new
  voices and no new scenes; only the picture changes. The first and last
  episodes are already "one core, two perspectives". Don't ask the creator
  questions the files already answer; see `story/movie_handoff.md`.
- **The movie, episode by episode** (November 13): "at the end one movie with
  all parts, so synchronization and homogenisation is required, but to stay
  consistent we will do ep by ep so I can confirm the quality and the
  delivery." Each episode is approved on its own, and every episode is
  built so the chapters match: the same places, light, grade, captions and
  loudness.
- **Episode 1 skips its repeat in the movie** (November 13): its
  "PREVIOUSLY..." flash and the replay of the forest and "Whoa. Where am
  I?" go, because Episode 0 has just shown them. Episode 1 picks up at
  "Okay. A tree. One punch."
- **No time limit in the movie** (November 14): "For ep2 it is too fast, we
  are going to make a long video so no restrictions on time we can make it as
  long as we want as long as the quality is good and the story make sense."
  It applies to every episode from Episode 1 on; Episode 0 keeps the Short's
  timing as built. **Same lines, more room:** the same words and voice takes,
  no new dialogue; longer actions, pauses and reactions between the lines,
  with the music and effects re-laid to fit. So these episodes get a new
  sound preview before any frame.
- **The REALITY meter in the movie** (approved November 13, version 6,
  `src/movie_hud.py`): it is hidden while the number isn't moving ("if the
  bar isn't moving hide it with the number, and when it appears it should
  make a scene"). It glitches in before each wave of drops and pops 1.3x on
  each drop ("it grew too much" at 2x). The number drains, the bar's lost
  cells break off as pixels, and the edges pulse red. It tears away after
  the wave. The same meter in every episode.

## Voices and sound

- **Voices must not sound robotic.** The Gemini voices (the chosen pair) are
  the characters' voices now; keep them.
- **Every word is heard, whole.** No clipped lines ("NOOB R RUN", "I A AM
  RUNNING"), no wrong words ("Vincent" instead of Steve), nothing that sounds
  like something else ("that was my plan" heard as "how was my plan").
- **No stereo glitch ("tchch") at the end of lines.** The creator has
  flagged it in nearly every episode; check every line end.
- **Acting notes are never read aloud**: a scream is a scream, not the words
  "screaming in terror".
- **Delivery fits the moment:** Steve is calm and dry; "Oh... My... God..."
  is real shock; a realisation is a whisper, but whispers that sounded
  "like Venom" were rejected: when a whisper fails, use Steve's normal voice.
- **Timing makes the joke:** instant interruptions ("It's beautifu-" /
  "Don't."), a real pause where one is asked for (between the Noob's echo
  and Steve's line).
- **Music is under the voices**, never over them; it starts with the picture
  (no deaf opening), it changes for Null (his theme), and it carries the big
  moments.
- **Every action has a sound** (footsteps to the tree, the throw, the
  impacts). A heartbeat is a heartbeat, not a knock on a table, separated
  "bom bom" for each POV, in silence.
- **Reuse the original audio** when a moment returns (Episode 0's "Noob,
  RUN!").

## Picture and animation

- **Movement is human.** Turns go head, then shoulders, then hips, with a
  step and the arms following; never a snap ("turned suddenly"). Slow motion
  is truly slow. Characters frozen in fear move slowly, as if afraid of a
  false move.
- **The camera shakes, not the characters**: shaking, zooming, focus pulls,
  blur, like a real camera.
- **Mouths move as if really talking**; faces act (eyes, brows, mouth).
- **Faces:** Steve's brows are never joined (he must be likeable); anger
  brings them together and down. Null's smile must not look provocative or
  off. Sad and crying faces must be readable: in the middle of the frame and
  lit. Make important details obvious (a shinier tear).
- **Nothing is glued, clipped or inside anything:** no face plate that looks
  stuck on, no prop touching a character by accident, no body inside a wall
  or the ground (the Noob hanging inside the wall in part 6 was missed once;
  never again). Characters carried together stay apart.
- **Nothing appears from nowhere.** A prop arrives on screen before it's
  used (the duck); a new ability transforms into being, piece by piece (the
  "mechanic, Gundam-style" robot arms); objects come from where they
  logically are (the cell falls from where Null exploded, from far away,
  toward the Noob, without stopping in mid-air).
- **Sizes make sense:** a cell the Noob grabs fits in one hand.
- **Falls are short and read as falling**, not standing in the sky.
- **Framing:** the action is centred and the distances are consistent;
  everyone who matters in a moment is in frame; the camera follows a moving
  thing with space around it (not glued to it); it never loses the
  characters or ends up in the grass. No backs to the camera.
- **Brightness as bright as the original**, even with Null on screen.
- **Spectacle with feeling:** big moments must give goosebumps (Null's
  entrance: the small portal ripped open by his hands, his head first, "HI!"
  in a shaking camera); transitions are smooth and continuous (the dive
  through the Noob's eye like a flying bee, and the way back out).
- **No visual faults:** no white square, no lag, no frozen last frame, no
  black screen between parts.

## Editing

- **Clean cuts**: no rough joins, no stray sound at a cut, no pause after an
  action (cut right as the turn ends).
- **A recap is labelled** ("Previously..." at the top) and only shows what
  is needed (Null and the screams).
- **Joined parts play straight through**, in order, each Short a new start.
- **Text on screen stays light.** The creator noticed viewers leaving when
  too much text appeared at once (moving captions plus a tutorial card); no
  votes.

## Publishing and the channel

- **Titles:** Episodes 1-8 used "<hook> | Minecraft x Roblox Animation | Two
  Worlds, One Glitch · Ep. N" (up to 100 characters); from Episode 9 the
  hook leads ("Steve & Noob Got UPGRADED Before the Finale"); the finale
  Shorts carry "(FINALE n/5)". The title's promise is in frame 1.
- **Thumbnails:** the series image with the episode number (for the finale,
  "FINALE n/5" in the image's own neon lettering, chosen over the rendered
  one). Game names in plain lettering, never imitating the official logos;
  "FAN ANIMATION" on it.
- **Watermark** @GLITCHBOUND2469 on every video.
- **Uploads** in 4K; US afternoon timing.
- **Community:** credit viewers whose ideas are used (@youssefakram7493:
  BTools, the theory card); reply to theories without confirming; replies
  show a confident personality, kind but sharp with trolls.
- **Credits:** the Steve rig credit (EpicPiggy_1401356, BlendSwap, CC-BY)
  stays in descriptions as the licence requires, even though the model was
  heavily reworked (the creator questioned it on November 8).
- **Dubs** (Episode 0): Indonesian, Spanish, Portuguese, French, Arabic (the
  Spacetoon style with Charon, with full tashkeel so words read right, the
  Noob named نوب).
