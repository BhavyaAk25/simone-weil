/** Quiet playback of Kevin MacLeod's Evening (CC BY 4.0), plus page rustle. */
export class BookAudio {
  private context?: AudioContext;
  private music?: HTMLAudioElement;
  private musicSource?: MediaElementAudioSourceNode;
  private master?: GainNode;
  private revision = 0;
  enabled = false;

  async toggle() {
    if (!this.context) {
      this.context = new AudioContext();
      this.master = this.context.createGain();
      this.master.gain.value = 0;
      this.master.connect(this.context.destination);
      this.music = new Audio(`${import.meta.env.BASE_URL}audio/evening-kevin-macleod.mp3`);
      this.music.preload = 'none';
      this.music.loop = true;
      this.musicSource = this.context.createMediaElementSource(this.music);
      this.musicSource.connect(this.master);
    }
    const context = this.context;
    const music = this.music!;
    const revision = ++this.revision;
    this.enabled = !this.enabled;
    const gain = this.master!.gain;
    gain.cancelScheduledValues(context.currentTime);
    gain.setTargetAtTime(this.enabled ? 0.12 : 0, context.currentTime, this.enabled ? 0.7 : 0.08);
    if (!this.enabled) {
      music.pause();
      return false;
    }
    try {
      // Both calls occur in the opening gesture, before awaiting any network work.
      await Promise.all([context.resume(), music.play()]);
    } catch (error) {
      if (this.context !== context || revision !== this.revision) return this.enabled;
      this.enabled = false;
      music.pause();
      gain.cancelScheduledValues(context.currentTime);
      gain.setValueAtTime(0, context.currentTime);
      throw error;
    }
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
    ++this.revision;
    const context = this.context;
    const music = this.music;
    this.context = undefined;
    this.music = undefined;
    this.enabled = false;
    music?.pause();
    music?.removeAttribute('src');
    music?.load();
    this.musicSource?.disconnect();
    this.master?.disconnect();
    this.musicSource = undefined;
    this.master = undefined;
    void context?.close().catch(() => {});
  }
}
