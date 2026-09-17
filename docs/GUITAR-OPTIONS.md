# Softer guitar choices, 17 September 2026

The user rejected the piano auditions as harsh and too prominent, preferring calmer guitar. The 3 new choices are auditions only; no soundtrack is selected automatically. They use real nylon-string guitar samples from FreePats (Roberto, CC0, version 2019-06-18). Primary source and license: https://freepats.zenvoid.org/Guitar/acoustic-guitar.html . Original notice is preserved under `scripts/audio/guitar-samples/`.

Each 36-second audition keeps one harmonic colour rather than changing chords. No percussion or lead melody. The first has 16 notes, the second 14, and the third 12. Compared with the previous piano examples, fewer notes, much slower attacks (75/120/180 ms), gentler high frequencies (1450/1200/1000 Hz rolloff), quiet room resonance and a 5-second ending fade reduce prominence. These are original simple arrangements, not historical reconstructions.

1. **Warm Pages**: natural rounded plucks in a stable C-major colour. RMS -32.46 dBFS; peak -15.00 dBFS.
2. **Evening Room**: softer darker tone with more room around an A-minor-7 colour. RMS -32.11 dBFS; peak -15.00 dBFS.
3. **Stillness**: very sparse suspended D colour with the gentlest attacks and longest spaces. RMS -30.00 dBFS; peak -15.12 dBFS.

All 3 measured files have 0 clipped samples, stereo 44.1 kHz, encoded as AAC. Signal checks do not replace user listening and approval. Selection is pending; a chosen soundtrack would need a longer seamless arrangement.

Reproduce on macOS with Python/numpy: `python3 scripts/audio/guitar_previews.py`. Source WAVs and source CC0 notice are retained; local audition WAVs go to ignored `tmp/guitar-previews`, deployable M4A files to `public/audio/guitar-previews`. No site audio code changed.
