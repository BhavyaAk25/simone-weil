import { describe, expect, it } from 'vitest';
import { clamp01, entrancePose, interval, smooth, turnPose, validDestination } from '../src/book/motion';

describe('page-turn sequencing', () => {
  it('starts on the old spread and finishes on the new spread', () => {
    expect(turnPose(0)).toMatchObject({ outgoing: 1, page: 0, incoming: 0, showIncoming: false, showPage: false });
    expect(turnPose(1)).toMatchObject({ outgoing: 0, page: 1, incoming: 1, showIncoming: true, showPage: false });
    expect(turnPose(-1)).toEqual(turnPose(0));
    expect(turnPose(2)).toEqual(turnPose(1));
  });

  it('folds completely before the sheet moves and settles the sheet before unfolding', () => {
    for (let frame = 0; frame <= 1000; frame++) {
      const pose = turnPose(frame / 1000);
      if (pose.page > 0) expect(pose.outgoing, `old scene at progress ${frame / 1000}`).toBe(0);
      if (pose.incoming > 0) expect(pose.page, `new scene at progress ${frame / 1000}`).toBe(1);
      if (pose.page > 0 && pose.page < 1) expect(pose.showText).toBe(false);
      if (!pose.showIncoming) expect(pose.incoming).toBe(0);
    }
  });

  it('switches scenes only while both paper constructions are fully folded', () => {
    let previous = turnPose(0);
    let switches = 0;
    for (let frame = 1; frame <= 1000; frame++) {
      const pose = turnPose(frame / 1000);
      if (pose.showIncoming !== previous.showIncoming) {
        switches++;
        expect(previous.outgoing).toBe(0);
        expect(pose.outgoing).toBe(0);
        expect(previous.incoming).toBe(0);
        expect(pose.incoming).toBe(0);
      }
      previous = pose;
    }
    expect(switches).toBe(1);
  });

  it('moves continuously in one direction, with no jump to an exported default pose', () => {
    let previous = turnPose(0);
    for (let frame = 1; frame <= 1000; frame++) {
      const pose = turnPose(frame / 1000);
      for (const key of ['outgoing', 'page', 'incoming'] as const) {
        expect(pose[key]).toBeGreaterThanOrEqual(0);
        expect(pose[key]).toBeLessThanOrEqual(1);
        expect(Math.abs(pose[key] - previous[key])).toBeLessThan(0.015);
      }
      expect(pose.outgoing).toBeLessThanOrEqual(previous.outgoing);
      expect(pose.page).toBeGreaterThanOrEqual(previous.page);
      expect(pose.incoming).toBeGreaterThanOrEqual(previous.incoming);
      previous = pose;
    }
  });

  it('can reverse the sheet for a back turn while preserving fold/turn/unfold order', () => {
    const sheet = Array.from({ length: 101 }, (_, frame) => 1 - turnPose(frame / 100).page);
    expect(sheet[0]).toBe(1);
    expect(sheet.at(-1)).toBe(0);
    for (let frame = 1; frame < sheet.length; frame++) expect(sheet[frame]).toBeLessThanOrEqual(sheet[frame - 1]);
  });
});

describe('book entrance sequencing', () => {
  it('opens the cover completely before any scenery unfolds', () => {
    for (let frame = 0; frame <= 1000; frame++) {
      const pose = entrancePose(frame / 1000);
      if (pose.popup > 0) expect(pose.cover).toBe(1);
      if (pose.cover < 1) { expect(pose.popup).toBe(0); expect(pose.showScene).toBe(false); }
      if (!pose.showScene) expect(pose.popup).toBe(0);
    }
  });

  it('keeps writing inside the closed book and reaches a complete reading pose', () => {
    expect(entrancePose(0)).toMatchObject({ cover: 0, popup: 0, showScene: false, textOpacity: 0 });
    expect(entrancePose(1)).toMatchObject({ cover: 1, popup: 1, showScene: true, textOpacity: 1 });
    for (let frame = 0; frame <= 1000; frame++) {
      const pose = entrancePose(frame / 1000);
      if (pose.textOpacity > 0) { expect(pose.cover).toBe(1); expect(pose.showScene).toBe(true); }
    }
  });
});

describe('navigation guard', () => {
  it('accepts adjacent turns and contents jumps in either direction', () => {
    for (const [current, target] of [[0, 1], [1, 0], [0, 11], [11, 3]]) {
      expect(validDestination(current, target, 12, false)).toBe(true);
    }
  });

  it('rejects repeated rapid input throughout an active transition', () => {
    for (const target of [0, 1, 2, 11]) expect(validDestination(1, target, 12, true)).toBe(false);
  });

  it('rejects staying on the same chapter, boundary overflow, and invalid indices', () => {
    for (const target of [-1, 12, 100, 2.5, NaN, Infinity, -Infinity, 2]) {
      expect(validDestination(2, target, 12, false)).toBe(false);
    }
    expect(validDestination(0, 0, 0, false)).toBe(false);
  });
});

describe('bounded easing', () => {
  it('holds the endpoint before and after a scheduled interval', () => {
    expect(interval(0, 0.2, 0.8)).toBe(0);
    expect(interval(1, 0.2, 0.8)).toBe(1);
    expect(interval(0.5, 0.2, 0.8)).toBeCloseTo(0.5);
    expect(smooth(-1)).toBe(0);
    expect(smooth(2)).toBe(1);
    expect(clamp01(-Infinity)).toBe(0);
    expect(clamp01(Infinity)).toBe(1);
  });
});
