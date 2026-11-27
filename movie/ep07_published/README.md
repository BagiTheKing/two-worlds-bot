# Episode 7's published voice takes (raw rescue, 2026-11-27)

The prep artifact of the published run 41463846907, downloaded straight from the Actions API (digest verified)
before it expired. `scenes/`: the raw scene recordings named by first line (cuts in `published_voice_log.txt`);
`published_audio.flac` + `timeline.json`: the published mix and its timing. Solo lines are not in the scenes:
lift them from the mix with the bed subtracted, as for Episode 4, when this episode is built.

**voice.flac (2026-11-27):** rebuilt with the published run's own sound code (run 41463846907, commit 446bef3):
the eight scene lines match the published mix at -78..-87 dB residual; the three solo takes (the Noob's "It's
COPYING me!", Patch's "From last time." (its own `solo_text` take), the Noob's "I don't want to be deleted." (an
`own_scene` take)) lifted with the bed subtracted (corr 1.000). Now a `voices_from` folder.
