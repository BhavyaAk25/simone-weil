#!/usr/bin/env python3
"""Render three original, sparse piano auditions. macOS + Python/numpy required.
Samples: Salamander Grand Piano, Alexander Holm, CC BY 3.0. See LICENSE.md.
No existing website music is changed. Network needed only for missing samples.
"""
from pathlib import Path
import json, subprocess, urllib.request, wave
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'scripts/audio/samples'
OUT = ROOT / 'public/audio/previews'
WAV_OUT = ROOT / 'tmp/piano-previews'
WAV_OUT.mkdir(parents=True, exist_ok=True)
SR = 44100
SOURCES = {'A2':45,'C3':48,'Ds3':51,'Fs3':54,'A3':57,'C4':60,
           'Ds4':63,'Fs4':66,'A4':69,'C5':72,'Ds5':75,'Fs5':78}
BASE = 'https://raw.githubusercontent.com/Tonejs/audio/master/salamander/'
NOTE = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}

def midi(name):
    return 12 * (int(name[-1]) + 1) + NOTE[name[0]] + (1 if '#' in name else -1 if 'b' in name else 0)

CACHE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
samples = {}
for key,pitch in SOURCES.items():
    mp3 = CACHE / f'{key}.mp3'; wav = CACHE / f'{key}.wav'
    if not mp3.exists(): urllib.request.urlretrieve(BASE+mp3.name,mp3)
    if not wav.exists(): subprocess.run(['afconvert',str(mp3),str(wav),'-f','WAVE','-d','LEI16'],check=True)
    with wave.open(str(wav)) as f:
        assert f.getframerate()==SR and f.getnchannels()==2
        samples[pitch]=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float64).reshape(-1,2)/32768

# All sequences are newly authored for these auditions. The modest note range,
# pauses, and restrained dynamics intentionally leave space for reading.
def attention():
    # Unhurried 4/4, 64 bpm, warm C-major colours; motif answers itself.
    beat=60/64; events=[]
    chords=[('C3',['E3','G3'],['E4','G4','D4']),('A2',['E3','C4'],['C4','E4','G4']),
            ('F3',['A3','C4'],['A4','G4','E4']),('G3',['B3','D4'],['D4','E4','D4']),
            ('C3',['E3','G3'],['E4','G4','C5']),('A2',['E3','C4'],['B4','A4','E4']),
            ('F3',['A3','C4'],['G4','E4','D4']),('C3',['G3','E4'],['C4'])]
    for bar,(bass,inner,melody) in enumerate(chords):
        t=.35+bar*4*beat
        events.append((t,bass,2.8,.45))
        for j,n in enumerate(inner): events.append((t+.10+j*.065,n,2.5,.34))
        for j,n in enumerate(melody):events.append((t+(j+.50)*beat,n,1.55,.46 if j==0 else .40))
    return events,34.5,3000

def belonging():
    # Gentle 3/4, 56 bpm. Quiet inner pulse, no emphatic oom-pah bass.
    beat=60/56;events=[]
    chords=[('F3',['A3','C4'],['A4','G4']),('D3',['F3','A3'],['F4','E4']),
            ('Bb2',['F3','D4'],['D4','F4']),('C3',['G3','E4'],['G4','E4']),
            ('F3',['A3','C4'],['F4','A4']),('D3',['F3','A3'],['G4','F4']),
            ('Bb2',['F3','D4'],['E4','D4']),('F3',['C4','A3'],['F4'])]
    for bar,(bass,inner,melody) in enumerate(chords):
        t=.35+bar*3*beat
        events.append((t,bass,2.5,.40))
        for j,n in enumerate(inner):events.append((t+(1+j*.13)*beat,n,1.5,.28))
        for j,n in enumerate(melody):events.append((t+(j*1.6+.25)*beat,n,1.8,.45))
    return events,31.0,3400

def quiet_light():
    # Spacious modal D minor, long pauses and open fifths, resolving gently.
    events=[]
    phrases=[('D3',['A3','F4'],[(.45,'A4'),(2.15,'F4')]),
             ('Bb2',['F3','D4'],[(.70,'E4'),(2.45,'D4')]),
             ('F3',['C4','A4'],[(.55,'G4'),(2.65,'F4')]),
             ('C3',['G3','E4'],[(.80,'D4'),(2.75,'E4')]),
             ('G3',['D4','Bb4'],[(.60,'A4'),(2.45,'G4')]),
             ('D3',['A3','F4'],[(.60,'F4'),(2.15,'D4')])]
    for bar,(bass,inner,melody) in enumerate(phrases):
        t=.45+bar*4.5
        events.append((t,bass,3.7,.42))
        for j,n in enumerate(inner):events.append((t+.16+j*.09,n,3.4,.27))
        for offset,n in melody: events.append((t+offset,n,2.1,.43))
    return events,33.0,2700

def render(title,fn,seed):
    events,duration,cutoff=fn(); rng=np.random.default_rng(seed)
    result=np.zeros((round(duration*SR),2),np.float64)
    for onset,name,hold,velocity in events:
        pitch=midi(name); anchor=min(samples,key=lambda p:abs(p-pitch))
        ratio=2**((pitch-anchor)/12)
        source=samples[anchor]
        length=min(len(source)/ratio,(hold+1.5)*SR)
        positions=np.arange(int(length))*ratio
        tone=np.column_stack([np.interp(positions,np.arange(len(source)),source[:,c]) for c in range(2)])
        t=np.arange(len(tone))/SR
        # Smooth key release and soft hammer. Retain authentic sampled attack.
        envelope=np.exp(-np.maximum(0,t-hold)*4)
        envelope*=np.minimum(t/.006,1)
        tone*=envelope[:,None]
        # Gentle warmth, no added oscillator, pluck or chime layer.
        freqs=np.fft.rfftfreq(len(tone),1/SR)
        response=1/np.sqrt(1+(freqs/cutoff)**4)
        tone=np.fft.irfft(np.fft.rfft(tone,axis=0)*response[:,None],n=len(tone),axis=0)
        onset += rng.uniform(-.015,.015)
        start=max(0,round(onset*SR));end=min(len(result),start+len(tone))
        result[start:end]+=tone[:end-start]*(velocity+rng.uniform(-.025,.025))
    # Quiet short room reflections. No obvious rhythmic delay or endless wash.
    dry=result.copy()
    for delay,gain in [(.037,.055),(.061,.04),(.097,.025),(.151,.014)]:
        n=round(delay*SR);result[n:]+=dry[:-n,::-1]*gain
    t=np.arange(len(result))/SR
    result*=np.minimum(t/.04,1)[:,None]
    result*=np.clip((duration-t)/2.8,0,1)[:,None]
    result-=result.mean(axis=0)
    rms=np.sqrt(np.mean(result**2));gain=min(10**(-24/20)/rms,10**(-5/20)/abs(result).max())
    result*=gain
    wav=WAV_OUT/f'{title}.wav'
    with wave.open(str(wav),'w') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes((np.clip(result,-1,1)*32767).astype('<i2').tobytes())
    m4a=OUT/f'{title}.m4a'
    subprocess.run(['afconvert',str(wav),str(m4a),'-f','m4af','-d','aac','-b','192000','-q','127'],check=True)
    metrics={'file':title,'duration_seconds':duration,'notes':len(events),'peak_dbfs':round(20*np.log10(abs(result).max()),2),'rms_dbfs':round(20*np.log10(np.sqrt(np.mean(result**2))),2),'clipped_samples':int(np.sum(abs(result)>=1)),'aac_bytes':m4a.stat().st_size}
    print(json.dumps(metrics));return metrics

metrics=[render('01-a-little-attention',attention,410),render('02-a-place-to-belong',belonging,411),render('03-quiet-light',quiet_light,412)]
(OUT/'render-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
