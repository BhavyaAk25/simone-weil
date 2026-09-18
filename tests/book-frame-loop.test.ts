import { describe, expect, it, vi } from 'vitest';
import { FrameLoop } from '../src/book/frameLoop';

function harness(render = vi.fn(() => false)) {
  let id = 0;
  const pending = new Map<number, FrameRequestCallback>();
  const loop = new FrameLoop(render, callback => { pending.set(++id, callback); return id; }, key => { pending.delete(key); });
  const frame = () => {
    const callbacks = [...pending.values()];
    pending.clear();
    callbacks.forEach(callback => callback(100));
  };
  return { loop, render, pending, frame };
}

describe('on-demand rendering lifecycle', () => {
  it('coalesces rapid input into one frame and stops while idle', () => {
    const h = harness();
    for (let i = 0; i < 20; i++) h.loop.invalidate();
    expect(h.pending.size).toBe(1);
    h.frame();
    expect(h.render).toHaveBeenCalledTimes(1);
    expect(h.pending.size).toBe(0);
  });

  it('continues active animation, then stops and wakes for new input', () => {
    const h = harness(vi.fn().mockReturnValueOnce(true).mockReturnValue(false));
    h.loop.invalidate(); h.frame();
    expect(h.pending.size).toBe(1);
    h.frame();
    expect(h.pending.size).toBe(0);
    h.loop.invalidate(); h.frame();
    expect(h.render).toHaveBeenCalledTimes(3);
  });

  it('cancels pending frames while hidden and redraws once on return', () => {
    const h = harness();
    h.loop.invalidate(); h.loop.setPaused(true); h.loop.invalidate(); h.frame();
    expect(h.render).not.toHaveBeenCalled();
    h.loop.setPaused(false); h.frame();
    expect(h.render).toHaveBeenCalledTimes(1);
  });

  it('cannot be restarted after disposal, including from a render callback', () => {
    const h = harness(vi.fn(() => { h.loop.dispose(); return true; }));
    h.loop.invalidate(); h.frame();
    h.loop.setPaused(false); h.loop.invalidate(); h.frame();
    expect(h.render).toHaveBeenCalledTimes(1);
    expect(h.pending.size).toBe(0);
  });
});
