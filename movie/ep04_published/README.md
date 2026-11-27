# Episode 4's published voice takes (recovered 2026-11-26)

The published Short (run 40605934372, `preview-ep04_the_block`) predates the voices-only stem, and its
takes had gone from the CI voice cache. Its prep artifact was saved (via `voices_from`) to `preview-logs`
an hour before it expired; this folder rebuilds the finished lines from it:

- `scenes/`: the four raw multi-line scene recordings (24 kHz), cut at each line's pinned `cut_at`, so
  those ten lines are exactly the published takes.
- The three solo lines (A secret block!, It fell off the dragon. Don't touch it., Again!) were taken from
  the published mix (`published_audio.flac`), the October bed rebuilt by the sound code and subtracted
  spectrally (it sat 20-27 dB under them).
- `voice.flac` + `timeline.json`: the finished lines on the published timing; use as `voices_from`.
