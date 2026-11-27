# Episode 5's published voice takes (raw rescue, 2026-11-27)

The published Short ("Noob Found Creative Mode", run 40886523331, `preview-ep05_creative_mode`). Its
`prep` artifact (expiring 2026-11-28 13:56 UTC) was downloaded straight from the Actions API (digest
sha256:8c437b90...b44a5 verified) on 2026-11-27, since the CI rescue run sat queued with no runner.

- `scenes/`: the two raw multi-line scene recordings (24 kHz), named by their first line
  (`steve_since`: steve_since .. noob_duck; `patch_delete`: patch_delete, steve_us). Every scene line has
  a pinned cut (see `published_voice_log.txt`).
- `published_audio.flac`: the published mix; `timeline.json`: its timing (29.2 s).
- Not in the scenes: the two solo Noob lines ("I can BUILD stuff!", "NO!"), to be lifted from the mix
  with the bed subtracted, as for Episode 4.
