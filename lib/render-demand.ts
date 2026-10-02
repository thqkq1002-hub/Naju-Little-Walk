/** Keep invalidations while the scene is hidden or its GPU context is unavailable. */
export class RenderDemand {
  private dirty = true;
  invalidate() { this.dirty = true; }
  take(animated: boolean, blocked: boolean) {
    if (blocked || (!animated && !this.dirty)) return false;
    this.dirty = false;
    return true;
  }
}
