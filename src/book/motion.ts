export const ENTER_DURATION = 4.4;

/**
 * One click turn: 1.0 s. The reading panel lies down (0.08 s); the leaf then
 * crosses in 0.72 s, carrying the pieces hinged to it as real geometry, which
 * collapse as it closes on the other page; the pieces on the page it uncovers
 * rise as it opens, and the new panel rises once the leaf has landed.
 * See docs/INTERACTION.md.
 */
export const TURN_DURATION = 1.0;
/** The panel is flat from here until TURN_PANEL_RISE. */
export const TURN_PANEL_DOWN = 0.08;
/** The leaf leaves its source page here (the panel is already flat)... */
export const TURN_LEAF_START = 0.08;
/** ...and lies on the other page here. */
export const TURN_LEAF_END = 0.8;
/** Outgoing pieces are completely folded by here: the leaf is still clear of the vertical. */
export const TURN_FOLD_END = 0.3;
/** Incoming pieces start to rise once the leaf has passed the vertical. */
export const TURN_UNFOLD_START = 0.56;
export const TURN_PANEL_RISE = 0.82;

export const clamp01 = (value: number) => Math.min(1, Math.max(0, value));
export const smooth = (value: number) => {
  const t = clamp01(value);
  return t * t * (3 - 2 * t);
};
export const interval = (value: number, start: number, end: number) => smooth((value - start) / (end - start));
/**
 * The chapter \`unfold\` clips ease their hinges: the angle from flat is
 * smooth(clip time). This returns the clip time for a wanted angle (0 flat, 1 upright).
 */
export const clipForAngle = (angle: number) => {
  const a = clamp01(angle);
  return a <= 0 ? 0 : a >= 1 ? 1 : 0.5 - Math.sin(Math.asin(1 - 2 * a) / 3);
};

export function entrancePose(progress: number) {
  const t = clamp01(progress);
  return {
    cover: interval(t, 0.53, 0.80),
    popup: interval(t, 0.83, 1),
    showScene: t >= 0.82,
    textOpacity: interval(t, 0.91, 1),
  };
}

/**
 * The leaf's travel (0 on its source page, 1 landed) for turn progress t: a
 * quick lift and a soft landing, like a page let go of.
 */
export function leafTravel(progress: number) {
  const s = clamp01((clamp01(progress) - TURN_LEAF_START) / (TURN_LEAF_END - TURN_LEAF_START));
  // Two joined parabolas with one peak speed at 38%: the page leaves briskly and settles slowly.
  const peak = 0.38;
  return s < peak ? s * s / peak : 1 - (1 - s) * (1 - s) / (1 - peak);
}

/** Turn progress at which the leaf has travelled `travel` (inverse of leafTravel). */
export function progressForTravel(travel: number) {
  const target = clamp01(travel);
  let lo = TURN_LEAF_START, hi = TURN_LEAF_END;
  for (let i = 0; i < 30; i++) {
    const mid = (lo + hi) / 2;
    if (leafTravel(mid) < target) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

/** Leaf travel at which pieces riding on it lie flat: the leaf is 100 degrees over, facing away. */
export const TURN_FLAT_ON_LEAF = 0.56;

/**
 * Angle (0 flat, 1 upright) of pieces that stay on a still page while the
 * other page moves: they cross the band where the camera sees cards edge-on
 * (about 20-45 degrees above flat) in a few hundredths of a second.
 */
export function quickFold(s: number) {
  const x = clamp01(s);
  const knots: [number, number][] = [[0, 1], [0.45, 0.5], [0.53, 0.2], [1, 0]];
  for (let i = 1; i < knots.length; i++) {
    const [x0, y0] = knots[i - 1], [x1, y1] = knots[i];
    if (x <= x1) {
      // Smooth within each span, so the pieces ease into and out of the quick part.
      const f = (x - x0) / (x1 - x0), e = i === 1 ? f * f : i === knots.length - 1 ? f * (2 - f) : f;
      return y0 + (y1 - y0) * e;
    }
  }
  return 0;
}

/**
 * One continuous page turn. The leaf is real geometry. Forward, the outgoing
 * pieces ride on the leaf (they are hinged to the right page, which is the
 * leaf) and collapse as it closes on the left page, like a real pop-up; the
 * incoming pieces wait, pressed flat, on the page beneath and spring up once
 * it has gone. Backward is the same mechanism in reverse. Pieces on the
 * moving leaf fold in step with it, which keeps them facing the camera until
 * the leaf itself hides them: they are never seen edge-on.
 */
export function turnPose(progress: number, direction = 1) {
  const t = clamp01(progress);
  const leaf = leafTravel(t);
  const staticFold = quickFold(t / TURN_FOLD_END);
  // Rising is the fold played backwards: quick off the page, then easing upright.
  const staticRise = quickFold(1 - clamp01((t - TURN_UNFOLD_START) / (1 - TURN_UNFOLD_START)));
  const onLeafFold = 1 - clamp01(leaf / TURN_FLAT_ON_LEAF);
  const onLeafRise = clamp01((leaf - (1 - TURN_FLAT_ON_LEAF)) / TURN_FLAT_ON_LEAF);
  return {
    /** Outgoing pieces (clip time: 1 upright, 0 flat). */
    outgoing: clipForAngle(direction > 0 ? onLeafFold : staticFold),
    /** The leaf's travel, 0..1. */
    leaf,
    /** Incoming pieces (clip time: 0 flat, 1 upright). */
    incoming: clipForAngle(direction > 0 ? staticRise : onLeafRise),
    /** Reading panel: folds before any page moves, rises after the leaf lands. */
    reading: t <= TURN_PANEL_DOWN ? 1 - interval(t, 0, TURN_PANEL_DOWN) : interval(t, TURN_PANEL_RISE, 1),
    showLeaf: t > TURN_LEAF_START && t < TURN_LEAF_END,
    /** The old pieces exist until the leaf has pressed them flat on the far page. */
    showOutgoing: t < TURN_LEAF_END,
    /** The new pieces exist once the leaf is there to cover them. */
    showIncoming: t > TURN_LEAF_START,
  };
}

/**
 * Which chapter's writing is on the reading panel. Forward, the new writing
 * arrives on the leaf's back and takes over the panel only when it has landed.
 * Backward, the leaf lifts the old writing away and the earlier chapter's
 * writing is already on the panel beneath it.
 */
export function incomingWriting(progress: number, direction: number) {
  const t = clamp01(progress);
  return direction > 0 ? t >= TURN_LEAF_END : t > TURN_LEAF_START;
}

export function validDestination(current: number, target: number, count: number, busy: boolean) {
  return !busy && Number.isInteger(target) && target >= 0 && target < count && target !== current;
}
