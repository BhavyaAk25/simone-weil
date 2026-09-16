# Piano auditions, 16 September 2026

The user requested 3 soothing piano choices and will choose before the soundtrack changes. These original samples are audition files only; `src/book/audio.ts` remains unchanged. No claim is made about Weil’s documented musical taste.

1. **A Little Attention**: 34.5 seconds, gentle answering melody, 64 bpm.
2. **A Place to Belong**: 31 seconds, warm slow 3/4 movement, 56 bpm.
3. **Quiet Light**: 33 seconds, sparse minor-key phrases and long pauses.

All use a sampled Yamaha C5 grand piano by Alexander Holm (Salamander, CC BY 3.0), restrained dynamics, softened high frequencies, and a short quiet room. Attribution: `scripts/audio/LICENSE.md` and `public/audio/previews/LICENSE.md`.

Reproduce on macOS with Python/numpy and `python3 scripts/audio/render_previews.py`. The script downloads missing licensed MP3 samples, uses afconvert to decode/encode, saves local WAVs under ignored `tmp/piano-previews`, and deployable M4A auditions under `public/audio/previews`. Sample PCM caches are ignored.

Measured stereo 44.1 kHz output: all 3 have 0 clipped samples; peaks -5.00, -5.83, -5.00 dBFS; RMS -24.09, -24.00, -24.28 dBFS. These are signal checks, not independent speaker-listening approval. The final selected piece still needs a longer seamless reading arrangement.
