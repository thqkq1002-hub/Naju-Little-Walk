export type LandscapeResult = 'locked' | 'rotate' | 'unavailable';

// Orientation locking is optional even when fullscreen is supported (notably iPad).
export async function enterLandscape(
  target: { requestFullscreen?: () => Promise<void> },
  orientation: { lock?: (mode: 'landscape') => Promise<void> } | undefined,
  alreadyFullscreen = false,
): Promise<LandscapeResult> {
  if (!alreadyFullscreen) {
    if (!target.requestFullscreen) return 'unavailable';
    try { await target.requestFullscreen(); } catch { return 'unavailable'; }
  }
  if (!orientation?.lock) return 'rotate';
  try { await orientation.lock('landscape'); return 'locked'; }
  catch { return 'rotate'; }
}

export function needsLandscape(width: number, height: number, touch: boolean) {
  return touch && width < height;
}

export type GraphicsQuality = 'balanced' | 'detail';
export function pixelRatioFor(quality: GraphicsQuality, ratio: number) {
  return Math.min(ratio, quality === 'balanced' ? 1.1 : 1.75);
}
