type Pointer = { x: number; y: number };
export type ViewDelta = { dx: number; dy: number; scale: number };

// Only canvas pointers belong here: a thumb on the movement pad cannot steal look.
export class ViewGesture {
  private pointers = new Map<number, Pointer>();
  down(id: number, x: number, y: number) { this.pointers.set(id, { x, y }); }
  up(id: number) { this.pointers.delete(id); }
  clear() { this.pointers.clear(); }
  move(id: number, x: number, y: number, allowZoom: boolean): ViewDelta | null {
    const old = this.pointers.get(id);
    if (!old) return null;
    const entries = [...this.pointers.entries()];
    this.pointers.set(id, { x, y });
    if (entries.length > 1) {
      if (!allowZoom) return null;
      const pair = entries.slice(0, 2);
      if (!pair.some(([pointerId]) => pointerId === id)) return null;
      const before = Math.hypot(pair[0][1].x - pair[1][1].x, pair[0][1].y - pair[1][1].y);
      const after = pair.map(([pointerId]) => this.pointers.get(pointerId)!);
      const distance = Math.hypot(after[0].x - after[1].x, after[0].y - after[1].y);
      return { dx: 0, dy: 0, scale: before > 0 && distance > 0 ? before / distance : 1 };
    }
    return { dx: x - old.x, dy: y - old.y, scale: 1 };
  }
}
