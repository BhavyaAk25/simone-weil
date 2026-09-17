#!/usr/bin/env python3
"""Original quiet guitar auditions; Python/numpy and macOS afconvert.

FreePats Spanish Classical Guitar, Roberto, 2019-06-18, CC0.
Source: https://freepats.zenvoid.org/Guitar/acoustic-guitar.html
Only auditions are produced; no change to the live soundtrack.
"""
from pathlib import Path
import json
import subprocess
import wave
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/audio/guitar-samples/samples'
OUT = ROOT / 'public/audio/guitar-previews'
PCM = ROOT / 'tmp/guitar-previews'
OUT.mkdir(parents=True, exist_ok=True)
PCM.mkdir(parents=True, exist_ok=True)
SR = 44100

def sample(name, cutoff, attack):
    with wave.open(str(SOURCE / (name + '.wav'))) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, SR)
        a = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32768
    a -= a.mean()
    t = np.arange(len(a)) / SR
    # Remove the sharp pick transient, while retaining recorded string/body tone.
    a *= np.sin(np.minimum(t / attack, 1) * np.pi / 2) ** 2
    a *= np.minimum((len(a) / SR - t) / .35, 1)
    f = np.fft.rfftfreq(len(a), 1 / SR)
    response = 1 / np.sqrt(1 + (f / cutoff) ** 8)
    response *= f ** 2 / (f ** 2 + 70 ** 2)
    a = np.fft.irfft(np.fft.rfft(a) * response, n=len(a))
    a *= .22 / max(np.max(np.abs(a)), .0001)
    return a

def render(slug, notes, spacing, cutoff, attack, wet, seed):
    rng = np.random.default_rng(seed)
    duration = 36
    dry = np.zeros((duration * SR, 2))
    cache = {name: sample(name, cutoff, attack) for name in set(notes)}
    for i, name in enumerate(notes):
        start = round((.4 + i * spacing + rng.uniform(-.045, .045)) * SR)
        a = cache[name] * rng.uniform(.85, 1)
        pan = rng.uniform(-.12, .12)
        end = min(len(dry), start + len(a))
        dry[start:end, 0] += a[:end-start] * (1-pan)
        dry[start:end, 1] += a[:end-start] * (1+pan)
    # Diffuse quiet room tail: many low-level reflections, no distinct echo pulse.
    result = dry * (1-wet)
    for ch in range(2):
        ir = np.zeros(round(SR * 2.4))
        for delay in rng.uniform(.025, 2.4, 1200):
            ir[round(delay * SR)] += rng.choice([-1, 1]) * np.exp(-delay * 2.5)
        ir /= np.sqrt(np.sum(ir ** 2))
        n = 1 << (len(dry) + len(ir) - 1).bit_length()
        room = np.fft.irfft(np.fft.rfft(dry[:, ch], n) * np.fft.rfft(ir, n), n)[:len(dry)]
        result[:, ch] += room * wet
    t = np.arange(len(result)) / SR
    result *= (np.minimum(t / 1.8, 1) * np.minimum((duration-t) / 5, 1))[:, None]
    rms = np.sqrt(np.mean(result ** 2))
    result *= min(10 ** (-30/20) / rms, 10 ** (-15/20) / np.max(np.abs(result)))
    wav = PCM / f'{slug}.wav'
    with wave.open(str(wav), 'w') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((result * 32767).astype('<i2').tobytes())
    out = OUT / f'{slug}.m4a'
    subprocess.run(['afconvert', str(wav), str(out), '-f', 'm4af', '-d', 'aac', '-b', '192000', '-q', '127'], check=True)
    return dict(file=slug, seconds=duration, notes=len(notes),
                rms_dbfs=round(20*np.log10(np.sqrt(np.mean(result ** 2))),2),
                peak_dbfs=round(20*np.log10(np.max(np.abs(result))),2),
                clipped_samples=int(np.sum(np.abs(result)>=1)))

# A single harmonic colour throughout each audition; no chord progression or solo.
choices = [
    ('01-warm-pages', ['C3','G3','E3','G3','C3','E3','G3','E3','C3','G3','E3','G3','C3','E3','G3','C3'], 1.85, 1450, .075, .26, 1701),
    ('02-evening-room', ['A2','E3','C3','G3','E3','A2','C3','E3','G3','C3','A2','E3','C3','E3'], 2.1, 1200, .12, .35, 1702),
    ('03-stillness', ['D3','A3','E3','A3','D3','G3','A3','E3','D3','A3','E3','D3'], 2.45, 1000, .18, .43, 1703),
]
metrics = [render(*choice) for choice in choices]
(OUT / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
print(json.dumps(metrics, indent=2))
