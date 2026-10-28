# Playbook: what we have learned, episode by episode

The bible says what the story is. This file says how to make an episode
that works, from three sources kept apart on purpose:

- **Measured**: what YouTube's numbers showed. Facts about our audience.
- **The creator's eye**: notes from watching each cut as a viewer
  (quality, consistency, whether the story holds together). Not measured,
  but they have been right every time so far, and the numbers cannot see
  these things.
- **Production**: traps in the pipeline that cost us renders.

Read it before planning an episode and check every cut against the
checklist at the end. Add to it after every episode's stats.

## 1. Measured

| | Ep1 | Ep2 | Ep3 | Clean test (Ep3 gag, 9 s) | Ep4 |
|---|---|---|---|---|---|
| Stayed to watch | 36.7% | 39.7% | 37.7% | 32.0% | *pending* |
| Avg. view duration | 0:18 (58.6%) | 0:20 (67.7%) | 0:17 (64.4%) | 0:11 (119%) | |
| Views (~2 days) | 1.2k | ~0.5k engaged | 1.37k | 1.35k | |
| Shorts feed share | | | 94.4% | 95.9% | |

What it means:

- **The swipe happens in the first second or two, and it has not moved**
  (32-40%) through four very different openings: a slow walk, no voice for
  1.4 s, a roaring dragon, a clean screen. So it is decided by what every
  video shares in its first frame: the look. Not the voice (Ep2 had none),
  not the overlays (the test had none), not the scene.
- **Screen clutter causes the mid-video cliff.** Ep2 and Ep3 both lost about
  30% of their remaining viewers at 0:04-0:06, when 5-6 things were on
  screen at once. The clean test had no cliff and was rewatched (119%).
- **Viewers who stay, love it.** Looping, rewatching, a second push from
  YouTube at 32 h (Ep3). The content is not the problem; the first
  impression is.
- **Almost everyone is a stranger** (94-96% from the Shorts feed). Every
  episode must work for someone who has seen nothing else.
- **A 3 s end card loses half the remaining viewers**; 1.5 s, ending on a
  frame that loops into the first, does not.
- **Measured audience is 25-44** (signed-in adults), likely kids on parents'
  devices. Keep "not made for kids": the comment questions need comments.
- **Ep4 tests faces**: a face in frame 1 and expressions on the punchlines.
  If "stayed" rises well above 40%, every episode gets them.

## 2. The creator's eye (quality and consistency)

- **Every episode must pick up where the last one left off.** Ep3 opened
  in the obby with no word on how they got there; Ep4 at first had nothing
  of Ep3's frozen dragon. A returning viewer must recognise the thread
  within the first seconds: show it, or say it in one short line ("It used
  our portal.", "It fell off the dragon."). Never a recap.
- **Faces change only on the moments that matter** (the hook, punchlines,
  the cliffhanger). The rest of the time the characters keep the faces
  the series started with: continuity first, expressions as a "take".
- **Nothing should look glued, clipped or accidental.** A face plate that
  reads as a sticker, a prop touching a character, a block hiding the
  person speaking: each one reads as a glitch that isn't part of the story.
  Leave a visible gap unless the contact is the point.
- **Voices must sound like the characters.** Steve is calm and dry; urgent
  is fine ("HIDE!"), panic is not. A line that sounds like it means
  something else ("That was my plan" heard as "How was my plan") gets
  re-taken.
- **Spectacle matters.** Ep3 (the dragon) felt strong and Ep4 (a block and
  a cube) weaker. Each episode needs at least one big visual moment, not
  only dialogue.
- **Framing: the action is centred and the distances are consistent.** Who
  or what matters in a moment is fully in frame (a new character's entrance
  shows them with everyone they are talking to); close-ups all at one
  chest-up distance, wide shots at one medium distance, each with a slow
  camera move. A camera aimed at where a prop *used to be* (Ep4's block)
  cut the action out of frame.
- **No backs to the camera. Brightness as bright as the original.**
- **Honesty**: the voices are AI and we say so. Never claim "no AI" about
  anything that used it.

## 3. Production traps

- **Whisper's word timings differ between CI runners.** The same recording
  was cut differently on two runs ("Plan: wall." lost its second word;
  "...It grew." swallowed a 1.6 s murmur). Once an episode's voices are
  approved, pin every line with `cut_at` from the published scene
  (`preview-logs/scenes/`), so re-renders cannot drift.
- **Changing one line inside a scene re-records the whole scene** (and every
  other line's delivery). Keep the scene's `direction_text` and give the
  changed line a `solo_text`: only that line is recorded again.
- **Whisper scores words, not delivery.** When takes tie, choose by ear
  (or by the loudness and punctuation in the log) with `solo_take`.
- **Keys on material colours blend between keyframes**: key the old value one
  frame before each change (Patch's eye drifted pink over 20 s).
- **Out-of-order test stills can show stale face plates** (persistent data);
  real renders are in order and are fine. Judge faces on rendered frames.
- **Dubs**: the voices only act with a direction; solo takes drop it, so
  dub lines are recorded as scenes of their own (`own_scene`, 3 takes).
  Arabic: Spacetoon-style Standard Arabic, vowel marks only where a word
  could be misread, pausal endings. Clean every take's edges (`trim`,
  `mute_start`): models leave pops and hiss at the ends.

## 4. Checklist for every cut

1. Frame 1: a face or a big moment, readable with zero context.
2. The link to the previous episode is clear within the first ~3 s.
3. At most one extra element on screen besides captions and the watermark.
4. A big visual moment somewhere in the middle.
5. Faces change only on the key moments, and look painted on.
6. Nothing touching that shouldn't, no glitches that aren't the story.
7. Every line sounds like what it says; Steve stays Steve.
8. 1.5 s end card, last frame loops into the first.
9. Every line's cut pinned once the voices are approved.
10. As bright as the original; no backs to the camera.
11. Every shot checked on its first and last frame with the real timing:
    the action centred, nothing that matters cut off, the same distances.

## 5. Experiment log

| Episode | What we changed | Result |
|---|---|---|
| Ep2 | Strong first second, no recap, comment question early | Stayed +3 pts, retention +9 pts; cliff at 0:04 |
| Ep3 | Spectacle hook (dragon), loop ending, 1.5 s end card | Stayed flat; no end-card drop; second push at 32 h |
| Clean test | Same gag, captions only | Stayed flat (32%); no 0:04 cliff; 119% retention |
| Ep4 | Face-first hook, faces on key moments, clean screen, Ep3 link | *pending* |
