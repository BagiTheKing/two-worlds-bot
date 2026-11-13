# Two Worlds · One Glitch: rules for every session

Before any work, read `story/creator_notes.md` (everything the creator has
asked for and insisted on) and the handoff brief for the current job
(`story/movie_handoff.md` for the long-form movie, `story/ep10_handoff.md`
for the pipeline). Follow them.

## The review gate: nothing reaches the creator unchecked

Every piece of work goes through an independent review **before** it is sent
to the creator: a sound preview, test stills, a preview render, a full
render, a joined Short or chapter, a thumbnail.

1. Run the automatic checks:
   `python tools/review_part.py <out_dir> <media> --timeline <timeline.json>`
   (for a fix, add `--previous <the last version> --changed <the seconds
   you were asked to change>`; for the movie, `--aspect 16:9`).
2. Launch the **`part-reviewer`** agent (`.claude/agents/part-reviewer.md`)
   with the media path, the timeline, **the creator's request for this piece
   word for word**, their earlier notes on it, and what you changed.
3. If its verdict is **FIX FIRST**, fix every "must fix" item and review
   again. Don't send until the verdict is **PASS**.
4. Send the creator the piece **with the reviewer's short summary**: what was
   checked, anything left "for the creator to judge", and any finding you
   chose not to fix and why. The creator then checks it and gives the final
   approval. Their approval is the only one that counts.

Never skip the gate to save time, and never tell the creator something
passed review when it didn't.

## Standing rules (short version; the notes have the full list)

- For the movie remake: study each published episode frame by frame and
  write its shot list before building any of it (see the movie brief).
- Part by part; the sound preview before any render; ask when unsure; give
  your own opinion.
- Fix only what the creator pointed at; keep earlier versions; reuse
  earlier renders instead of re-rendering.
- Never put a model name or ID in commits, code or anything pushed. Work on
  `lookdev-steve`; commit and push your work.
- Never commit the MCprep textures; never push to the MCprep repository.
