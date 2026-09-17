# Selected soundtrack

On 17 September 2026 the user selected **Evening by Kevin MacLeod** from the 3 existing-composition choices. Instruments: guitar, cello and oboe; official duration 3:06; ISRC USUAN2300002. Source: https://incompetech.com/music/royalty-free/index.html?isrc=USUAN2300002 . Licensed CC BY 4.0.

The official MP3 is self-hosted unchanged, approximately 3.6 MiB. A streaming HTMLAudioElement feeds the existing Web Audio gain node, avoiding decoding the whole track into an in-memory PCM buffer. Playback begins only inside the opening/sound gesture. Gain is 0.12 (about -18.4 dB) with a soft start. Muting pauses the recording; re-enabling resumes at the same position. Native repeat preserves the piece’s natural ending and restart; this is not a newly composed seamless musical loop. Existing page rustle remains.

Visible attribution is in About; full attribution is also in CREDITS.md and public/licenses/evening-music.txt. No personal musical taste is attributed to Simone Weil. Earlier piano/guitar auditions remain archival options and are not played.

Validation: typecheck and 23 tests pass, including start/mute, playback failure and retry, a pending play interrupted by mute, and dispose/reinitialize. Browser playback verification was blocked by automatic approval review after a usage-limit rejection. Do not claim independent speaker listening or browser playback approval for this release.
