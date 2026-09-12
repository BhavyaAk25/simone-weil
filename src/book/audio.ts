/** Original, quiet nylon-string-inspired music. No recordings or tracking are used. */
export class BookAudio {
  private context?: AudioContext;
  private ambience?: AudioBufferSourceNode;
  private master?: GainNode;
  enabled = false;

  private createMusic(context: AudioContext) {
    // An unhurried eight-bar arpeggio: Am(add9), Dm9, G6, Cmaj7,
    // Fmaj7, Dm9, E7sus4, E7. The last chord resolves into the loop's A minor.
    // This is an original Spanish-guitar-inspired passage, not a historical claim.
    const chords = [
      [45, 57, 60, 64, 71], [38, 57, 60, 65, 64],
      [43, 55, 59, 62, 64], [48, 55, 59, 64, 67],
      [41, 57, 60, 64, 69], [38, 57, 60, 65, 64],
      [40, 57, 59, 62, 69], [40, 56, 59, 62, 68],
    ];
    const sampleRate = 32000;
    const pulse = 60 / 110; // Eighth notes; a relaxed 55 quarter-note beats/minute.
    const length = Math.round(chords.length * 8 * pulse * sampleRate);
    const buffer = context.createBuffer(2, length, sampleRate);
    const left = buffer.getChannelData(0);
    const right = buffer.getChannelData(1);
    const pattern = [0, 2, 3, 1, 4, 2, 3, 1];
    const partialWeights = [1, 0.31, 0.14, 0.065, 0.027, 0.012];

    const pluck = (midi: number, start: number, strength: number, pan: number) => {
      const frequency = 440 * 2 ** ((midi - 69) / 12);
      const frames = Math.round(sampleRate * 4.8);
      const startFrame = Math.round(start * sampleRate);
      const leftGain = Math.sqrt((1 - pan) / 2) * strength;
      const rightGain = Math.sqrt((1 + pan) / 2) * strength;
      // Decaying partials give a soft plucked string without a sharp noise attack.
      // Recurrences avoid expensive per-sample trigonometry during the first click.
      const partials = partialWeights.map((weight, index) => {
        const harmonic = index + 1;
        const angle = 2 * Math.PI * frequency * harmonic / sampleRate;
        const decay = Math.exp(-1 / (sampleRate * (1.04 / harmonic ** 0.6)));
        return { sine: 0, cosine: weight, rotateSin: Math.sin(angle) * decay,
          rotateCos: Math.cos(angle) * decay };
      });
      for (let frame = 0; frame < frames; frame++) {
        let sample = 0;
        for (const partial of partials) {
          const sine = partial.sine * partial.rotateCos + partial.cosine * partial.rotateSin;
          partial.cosine = partial.cosine * partial.rotateCos - partial.sine * partial.rotateSin;
          partial.sine = sine;
          sample += sine;
        }
        const attack = Math.min(1, frame / (sampleRate * 0.007));
        const release = Math.min(1, (frames - frame) / (sampleRate * 0.08));
        sample *= attack * release;
        // Wrap every ringing tail onto the beginning: the loop has no cut-off notes.
        const output = (startFrame + frame) % length;
        left[output] += sample * leftGain;
        right[output] += sample * rightGain;
      }
    };

    chords.forEach((chord, bar) => pattern.forEach((voice, beat) => {
      // Tiny deterministic timing and dynamics differences keep the arpeggio gentle.
      const delay = beat === 0 ? 0 : [0.012, 0.004, 0.016][beat % 3];
      const strength = beat === 0 ? 0.46 : beat === 4 ? 0.31 : 0.25;
      pluck(chord[voice], (bar * 8 + beat) * pulse + delay, strength,
        voice === 0 ? -0.1 : (voice - 2) * 0.09);
    }));

    // A small, quiet room reflection adds space without a wash of background noise.
    const dryLeft = left.slice();
    const dryRight = right.slice();
    for (const [seconds, gain] of [[0.073, 0.08], [0.137, 0.045], [0.211, 0.025]]) {
      const offset = Math.round(seconds * sampleRate);
      for (let frame = 0; frame < length; frame++) {
        const delayed = (frame + offset) % length;
        left[delayed] += dryRight[frame] * gain;
        right[delayed] += dryLeft[frame] * gain;
      }
    }
    return buffer;
  }

  async toggle() {
    if (!this.context) {
      this.context = new AudioContext();
      this.master = this.context.createGain();
      this.master.gain.value = 0;
      this.master.connect(this.context.destination);
      this.ambience = this.context.createBufferSource();
      this.ambience.buffer = this.createMusic(this.context);
      this.ambience.loop = true;
      this.ambience.connect(this.master);
      this.ambience.start();
    }
    const context = this.context;
    try {
      await context.resume();
    } catch (error) {
      // Cleanup can close a context while its resume promise is pending.
      if (this.context !== context) return false;
      throw error;
    }
    if (this.context !== context) return false;
    this.enabled = !this.enabled;
    this.master!.gain.setTargetAtTime(this.enabled ? 0.16 : 0, context.currentTime, 0.25);
    return this.enabled;
  }

  rustle() {
    if (!this.context || !this.enabled || !this.master) return;
    const duration = 0.5;
    const buffer = this.context.createBuffer(1, this.context.sampleRate * duration, this.context.sampleRate);
    const samples = buffer.getChannelData(0);
    for (let i = 0; i < samples.length; i++) {
      const t = i / samples.length;
      samples[i] = (Math.random() * 2 - 1) * Math.sin(t * Math.PI) ** 2 * 0.1;
    }
    const source = this.context.createBufferSource();
    source.buffer = buffer;
    const filter = this.context.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = 1200;
    filter.Q.value = 0.55;
    source.connect(filter).connect(this.master);
    source.start();
    source.onended = () => { source.disconnect(); filter.disconnect(); };
  }

  dispose() {
    const context = this.context;
    const ambience = this.ambience;
    const master = this.master;
    // Release the graph, but let a later user gesture create a fresh one. React's
    // development StrictMode runs effect cleanup before setting the effect up again.
    this.context = undefined;
    this.ambience = undefined;
    this.master = undefined;
    this.enabled = false;
    ambience?.stop();
    ambience?.disconnect();
    master?.disconnect();
    void context?.close().catch(() => {});
  }
}
