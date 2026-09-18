/** Schedules only invalidated frames and active animation, never an idle GPU loop. */
export class FrameLoop {
  private frame = 0;
  private paused = false;
  private disposed = false;

  constructor(
    private render: (now: number) => boolean,
    private request = (callback: FrameRequestCallback) => requestAnimationFrame(callback),
    private cancel = (id: number) => cancelAnimationFrame(id),
  ) {}

  invalidate = () => {
    if (!this.frame && !this.paused && !this.disposed) this.frame = this.request(this.tick);
  };

  private tick = (now: number) => {
    this.frame = 0;
    if (this.paused || this.disposed) return;
    if (this.render(now)) this.invalidate();
  };

  setPaused(paused: boolean) {
    this.paused = paused;
    if (paused) { this.cancel(this.frame); this.frame = 0; }
    else this.invalidate();
  }

  dispose() {
    this.disposed = true;
    this.cancel(this.frame);
    this.frame = 0;
  }
}
