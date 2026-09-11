export const ENTER_DURATION = 4.4;
export const TURN_DURATION = 2.7;
export const clamp01 = (value: number) => Math.min(1, Math.max(0, value));
export const smooth = (value: number) => {
  const t = clamp01(value);
  return t * t * (3 - 2 * t);
};
export const interval = (value: number, start: number, end: number) => smooth((value - start) / (end - start));

export function entrancePose(progress: number) {
  const t = clamp01(progress);
  return {
    cover: interval(t, 0.53, 0.80),
    popup: interval(t, 0.83, 1),
    showScene: t >= 0.82,
    textOpacity: interval(t, 0.91, 1),
  };
}

export function turnPose(progress: number) {
  const t = clamp01(progress);
  return {
    outgoing: 1 - interval(t, 0, 0.24),
    page: interval(t, 0.30, 0.70),
    incoming: interval(t, 0.78, 1),
    showOutgoing: t < 0.27,
    showIncoming: t > 0.75,
    showPage: t >= 0.28 && t <= 0.73,
    showText: t < 0.14 || t > 0.88,
    textOpacity: t < 0.5 ? 1 - interval(t, 0, 0.14) : interval(t, 0.88, 1),
  };
}

export function validDestination(current: number, target: number, count: number, busy: boolean) {
  return !busy && Number.isInteger(target) && target >= 0 && target < count && target !== current;
}
