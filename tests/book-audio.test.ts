import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { BookAudio } from '../src/book/audio';

let play: ReturnType<typeof vi.fn>;
let pause: ReturnType<typeof vi.fn>;
let resume: ReturnType<typeof vi.fn>;
let track: { src: string; loop: boolean; preload: string };
let close: ReturnType<typeof vi.fn>;

beforeEach(() => {
  play = vi.fn().mockResolvedValue(undefined);
  pause = vi.fn();
  resume = vi.fn().mockResolvedValue(undefined);
  close = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal('Audio', class {
    src: string;
    loop = false;
    preload = '';
    constructor(src: string) { this.src = src; track = this; }
    play = play;
    pause = pause;
    removeAttribute = vi.fn();
    load = vi.fn();
  });
  vi.stubGlobal('AudioContext', class {
    currentTime = 0;
    destination = {};
    resume = resume;
    close = close;
    createGain() { return { gain: { value: 0, cancelScheduledValues: vi.fn(), setTargetAtTime: vi.fn(), setValueAtTime: vi.fn() }, connect: vi.fn(), disconnect: vi.fn() }; }
    createMediaElementSource() { return { connect: vi.fn(), disconnect: vi.fn() }; }
  });
});
afterEach(() => vi.unstubAllGlobals());

it('plays the selected recording only on toggle, loops, and pauses on mute', async () => {
  const audio = new BookAudio();
  expect(play).not.toHaveBeenCalled();
  expect(await audio.toggle()).toBe(true);
  expect(track.src).toContain('audio/evening-kevin-macleod.mp3');
  expect(track.loop).toBe(true);
  expect(resume).toHaveBeenCalledOnce();
  expect(await audio.toggle()).toBe(false);
  expect(pause).toHaveBeenCalledOnce();
  audio.dispose();
});

it('reports failed playback and permits retry', async () => {
  play.mockRejectedValueOnce(new Error('blocked'));
  const audio = new BookAudio();
  await expect(audio.toggle()).rejects.toThrow('blocked');
  expect(audio.enabled).toBe(false);
  expect(await audio.toggle()).toBe(true);
  audio.dispose();
});

it('a delayed play rejection cannot undo a newer mute', async () => {
  let reject!: (error: Error) => void;
  play.mockImplementationOnce(() => new Promise((_, no) => { reject = no; }));
  const audio = new BookAudio();
  const opening = audio.toggle();
  expect(await audio.toggle()).toBe(false);
  reject(new Error('play interrupted by pause'));
  expect(await opening).toBe(false);
  expect(audio.enabled).toBe(false);
  audio.dispose();
});

it('releases pending playback on disposal and can initialize again', async () => {
  let resolve!: () => void;
  play.mockImplementationOnce(() => new Promise<void>(yes => { resolve = yes; }));
  const audio = new BookAudio();
  const opening = audio.toggle();
  audio.dispose();
  resolve();
  expect(await opening).toBe(false);
  expect(close).toHaveBeenCalledOnce();
  expect(await audio.toggle()).toBe(true);
  audio.dispose();
});
