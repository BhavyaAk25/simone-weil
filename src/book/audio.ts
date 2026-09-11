/** Original synthesized sound; no recording or tracking is used. */
export class BookAudio {
  private context?: AudioContext;
  private ambience?: AudioBufferSourceNode;
  private master?: GainNode;
  enabled = false;

  async toggle() {
    if (!this.context) {
      this.context = new AudioContext();
      this.master = this.context.createGain();
      this.master.gain.value = 0;
      this.master.connect(this.context.destination);
      const buffer = this.context.createBuffer(1, this.context.sampleRate * 4, this.context.sampleRate);
      const samples = buffer.getChannelData(0);
      let last = 0;
      for (let i = 0; i < samples.length; i++) {
        last = (last + (Math.random() * 2 - 1) * 0.025) / 1.025;
        samples[i] = last * 0.25;
      }
      this.ambience = this.context.createBufferSource();
      this.ambience.buffer = buffer;
      this.ambience.loop = true;
      const filter = this.context.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.value = 380;
      this.ambience.connect(filter).connect(this.master);
      this.ambience.start();
    }
    await this.context.resume();
    this.enabled = !this.enabled;
    this.master!.gain.setTargetAtTime(this.enabled ? 0.12 : 0, this.context.currentTime, 0.2);
    return this.enabled;
  }

  rustle() {
    if (!this.context || !this.enabled || !this.master) return;
    const duration = 0.65;
    const buffer = this.context.createBuffer(1, this.context.sampleRate * duration, this.context.sampleRate);
    const samples = buffer.getChannelData(0);
    for (let i = 0; i < samples.length; i++) {
      const t = i / samples.length;
      samples[i] = (Math.random() * 2 - 1) * Math.sin(t * Math.PI) ** 2 * 0.45;
    }
    const source = this.context.createBufferSource();
    source.buffer = buffer;
    const filter = this.context.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = 1600;
    filter.Q.value = 0.55;
    source.connect(filter).connect(this.master);
    source.start();
    source.onended = () => { source.disconnect(); filter.disconnect(); };
  }

  dispose() {
    this.ambience?.stop();
    void this.context?.close();
  }
}
