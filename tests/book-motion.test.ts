import { describe, expect, it } from 'vitest';
import {
  TURN_DURATION, TURN_FOLD_END, TURN_LEAF_END, TURN_LEAF_START, TURN_PANEL_DOWN, TURN_PANEL_RISE, TURN_UNFOLD_START,
  TURN_FLAT_ON_LEAF, clamp01, clipForAngle, entrancePose, incomingWriting, interval, leafTravel, progressForTravel, smooth, turnPose, validDestination,
} from '../src/book/motion';
import { curlWeight, travelForTip } from '../src/book/leaf';

const frames = (count = 2000) => Array.from({ length: count + 1 }, (_, frame) => frame / count);

describe('page-turn sequencing', () => {
  it('starts on the old spread and finishes on the new spread', () => {
    expect(turnPose(0)).toMatchObject({ outgoing: 1, leaf: 0, incoming: 0, reading: 1, showLeaf: false, showOutgoing: true, showIncoming: false });
    expect(turnPose(1)).toMatchObject({ outgoing: 0, leaf: 1, incoming: 1, reading: 1, showLeaf: false, showOutgoing: false, showIncoming: true });
    expect(turnPose(-1)).toEqual(turnPose(0));
    expect(turnPose(2)).toEqual(turnPose(1));
  });

  it('takes a click turn of about a second, with the leaf itself crossing in 0.6-0.9 s', () => {
    const leafSeconds = (TURN_LEAF_END - TURN_LEAF_START) * TURN_DURATION;
    expect(leafSeconds).toBeGreaterThanOrEqual(0.6);
    expect(leafSeconds).toBeLessThanOrEqual(0.9);
    expect(TURN_DURATION).toBeLessThanOrEqual(1.1);
  });

  it('lays the reading panel flat before any page moves and raises it only after the leaf lands', () => {
    expect(TURN_PANEL_DOWN).toBeLessThanOrEqual(TURN_LEAF_START);
    expect(TURN_PANEL_RISE).toBeGreaterThanOrEqual(TURN_LEAF_END);
    for (const t of frames()) {
      const pose = turnPose(t);
      if (pose.leaf > 0 && pose.leaf < 1) expect(pose.reading, `panel at ${t}`).toBe(0);
      expect(turnPose(t, -1).reading).toBe(pose.reading);
      if (pose.showLeaf) expect(pose.reading).toBe(0);
    }
  });

  it('collapses the pieces on the leaf as it closes, flat before it nears the other page', () => {
    for (const t of frames()) {
      const forward = turnPose(t, 1), backward = turnPose(t, -1);
      // Forward, the old pieces ride on the leaf: upright until it moves, flat once it is 100 degrees over.
      if (forward.leaf >= TURN_FLAT_ON_LEAF) expect(forward.outgoing, `old scene at ${t}`).toBe(0);
      if (forward.leaf === 0) expect(forward.outgoing).toBe(1);
      // Backward, the new pieces ride on the leaf and rise as it opens, upright when it lands.
      if (backward.leaf <= 1 - TURN_FLAT_ON_LEAF) expect(backward.incoming, `new scene at ${t}`).toBe(0);
      if (backward.leaf === 1) expect(backward.incoming).toBe(1);
    }
  });

  it('keeps pieces on a still page flat whenever the leaf could reach them', () => {
    for (const t of frames()) {
      const forward = turnPose(t, 1), backward = turnPose(t, -1);
      // Forward: the new pieces rise only when the leaf is well past the vertical.
      if (forward.incoming > 0) expect(forward.leaf, `new scene at ${t}`).toBeGreaterThan(0.65);
      if (t <= TURN_UNFOLD_START) expect(forward.incoming).toBe(0);
      // Backward: the old pieces are flat before the leaf, coming from the left, is near the vertical.
      if (backward.leaf >= 0.3) expect(backward.outgoing, `old scene at ${t}`).toBe(0);
      if (t >= TURN_FOLD_END) expect(backward.outgoing).toBe(0);
    }
    expect(leafTravel(TURN_FOLD_END)).toBeLessThan(0.3);
  });

  it('never shows an empty book and always has the leaf there while both scenes exist', () => {
    for (const t of [...frames(), ...frames()]) {
      const pose = turnPose(t, t > 0.5 ? 1 : -1);
      expect(pose.showOutgoing || pose.showIncoming, `progress ${t}`).toBe(true);
      // The pressed-flat scene under or on the leaf only exists while the leaf covers it.
      if (pose.showOutgoing && pose.showIncoming) expect(pose.showLeaf).toBe(true);
      // Forward, no scene ever stands up under the leaf while it is still over the right page.
      if (t > 0.5 && pose.showIncoming && pose.leaf < 0.5) expect(pose.incoming).toBe(0);
    }
  });

  it('moves continuously in one direction, with no jump to an exported default pose', () => {
    for (const direction of [1, -1]) {
    let previous = turnPose(0, direction);
    for (const t of frames().slice(1)) {
      const pose = turnPose(t, direction);
      for (const key of ['outgoing', 'leaf', 'incoming'] as const) {
        expect(pose[key]).toBeGreaterThanOrEqual(0);
        expect(pose[key]).toBeLessThanOrEqual(1);
        // Pieces: the hinge angle the clip produces (smooth of clip time) changes continuously.
        const value = key === 'leaf' ? pose[key] : smooth(pose[key]), before = key === 'leaf' ? previous[key] : smooth(previous[key]);
        expect(Math.abs(value - before), `${key} at ${t}`).toBeLessThan(0.01);
      }
      expect(pose.outgoing).toBeLessThanOrEqual(previous.outgoing);
      expect(pose.leaf).toBeGreaterThanOrEqual(previous.leaf);
      expect(pose.incoming).toBeGreaterThanOrEqual(previous.incoming);
      previous = pose;
    }
    }
  });

  it('swaps the writing only while the leaf covers the panel', () => {
    for (const t of frames()) {
      // Forward: the new writing arrives printed on the leaf and replaces the panel when it lands.
      expect(incomingWriting(t, 1)).toBe(t >= TURN_LEAF_END);
      // Backward: the earlier writing is placed under the leaf as it starts from the left page.
      expect(incomingWriting(t, -1)).toBe(t > TURN_LEAF_START);
    }
  });

  it('maps a held page back to turn progress exactly (drag)', () => {
    for (const travel of [0, 0.1, 0.33, 0.5, 0.71, 0.99, 1]) {
      expect(leafTravel(progressForTravel(travel))).toBeCloseTo(travel, 4);
    }
    expect(progressForTravel(0)).toBeCloseTo(TURN_LEAF_START, 4);
    expect(progressForTravel(1)).toBeCloseTo(TURN_LEAF_END, 4);
  });
});

describe('piece hinge timing', () => {
  it('inverts the clip easing exactly', () => {
    for (const angle of [0, 0.1, 0.28, 0.5, 0.9, 1]) expect(smooth(clipForAngle(angle))).toBeCloseTo(angle, 6);
  });

  it('crosses the edge-on band quickly on a still page', () => {
    // Pieces on a still page (forward: incoming; backward: outgoing) cross 20-45 degrees quickly.
    const band = (key: 'outgoing' | 'incoming', direction: number) => {
      let inBand = 0;
      for (let t = 0; t <= 1; t += 0.0005) {
        const degrees = 90 * smooth(turnPose(t, direction)[key]);
        if (degrees > 20 && degrees < 45) inBand++;
      }
      return inBand * 0.0005 * TURN_DURATION;
    };
    expect(band('incoming', 1)).toBeLessThan(0.05);
    expect(band('outgoing', -1)).toBeLessThan(0.05);
  });
});

describe('leaf curl', () => {
  it('lies exactly on its page at both ends and stays between them', () => {
    for (let u = 0; u <= 1; u += 0.05) for (let v = 0; v <= 1; v += 0.25) {
      expect(curlWeight(u, v, 0)).toBe(0);
      expect(curlWeight(u, v, 1)).toBe(1);
      for (const L of frames(200)) {
        const w = curlWeight(u, v, L);
        expect(w).toBeGreaterThanOrEqual(0);
        expect(w).toBeLessThanOrEqual(1);
      }
    }
  });

  it('turns every part of the sheet one way only (no flutter back)', () => {
    for (let u = 0; u <= 1; u += 0.05) for (const v of [0, 0.5, 0.85, 1]) {
      let previous = 0;
      for (const L of frames(400)) {
        const w = curlWeight(u, v, L);
        expect(w, `u ${u} v ${v} L ${L}`).toBeGreaterThanOrEqual(previous - 1e-9);
        previous = w;
      }
    }
  });

  it('bends in an S: the fore-edge leads while the page lifts and trails as it falls', () => {
    expect(curlWeight(1, 0.85, 0.25)).toBeGreaterThan(curlWeight(0.3, 0.85, 0.25));
    expect(curlWeight(1, 0.85, 0.75)).toBeLessThan(curlWeight(0.3, 0.85, 0.75));
    // The held row leads the others.
    expect(curlWeight(1, 0.85, 0.25, 0.85)).toBeGreaterThan(curlWeight(1, 0.1, 0.25, 0.85));
  });

  it('finds the travel that puts the held edge under the hand', () => {
    for (const target of [0, 0.2, 0.5, 0.8, 1]) expect(curlWeight(1, 0.6, travelForTip(target, 0.6), 0.6)).toBeCloseTo(target, 3);
  });
});

describe('book entrance sequencing', () => {
  it('opens the cover completely before any scenery unfolds', () => {
    for (const t of frames(1000)) {
      const pose = entrancePose(t);
      if (pose.popup > 0) expect(pose.cover).toBe(1);
      if (pose.cover < 1) { expect(pose.popup).toBe(0); expect(pose.showScene).toBe(false); }
      if (!pose.showScene) expect(pose.popup).toBe(0);
    }
  });

  it('keeps writing inside the closed book and reaches a complete reading pose', () => {
    expect(entrancePose(0)).toMatchObject({ cover: 0, popup: 0, showScene: false, textOpacity: 0 });
    expect(entrancePose(1)).toMatchObject({ cover: 1, popup: 1, showScene: true, textOpacity: 1 });
    for (const t of frames(1000)) {
      const pose = entrancePose(t);
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
