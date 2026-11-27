# Episode 8's published voice takes (raw rescue, 2026-11-27)

The prep artifact of the published run 41851020512, downloaded straight from the Actions API (digest verified)
before it expired. `scenes/`: the raw scene recordings named by first line (cuts in `published_voice_log.txt`);
`published_audio.flac` + `timeline.json`: the published mix and its timing. Solo lines are not in the scenes:
lift them from the mix with the bed subtracted, as for Episode 4, when this episode is built.

**voice.flac (2026-11-27):** rebuilt with the published run's own sound code (run 41851020512, commit 8ff625d):
the seven scene lines sit at lag 0, corr 1.000, residual ~-40 dB against the published mix (the floor is the same
in the voice-free stretches, so it is the mix's level fit, not the takes; inaudible); the four solo takes lifted
with the bed subtracted (corr 0.99-1.00): "You had a PORTAL?!" and Steve's "I wanted to see the other side. Your
side. I didn't know what it would cost." (its own `solo_text` take) are clean; the two screams overlap each other
(`together`) and are not separable (the movie cuts them). Now a `voices_from` folder.
