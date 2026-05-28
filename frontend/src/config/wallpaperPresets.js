/**
 * Готовые «обои»-градиенты. Используются и в поповере (свотчи),
 * и в App.vue (резолв фонового слоя по prefs.wallpaper.presetId).
 * Значение `css` подставляется в background фонового слоя как есть.
 */
export const WALLPAPER_PRESETS = [
  {
    id: 'aurora',
    name: 'Aurora',
    css: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 45%, #0ea5e9 100%)',
  },
  {
    id: 'dusk',
    name: 'Dusk',
    css: 'linear-gradient(135deg, #4c1d95 0%, #7c3aed 50%, #db2777 100%)',
  },
  {
    id: 'forest',
    name: 'Forest',
    css: 'linear-gradient(135deg, #064e3b 0%, #047857 55%, #65a30d 100%)',
  },
  {
    id: 'graphite',
    name: 'Graphite',
    css: 'linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%)',
  },
  {
    id: 'sunset',
    name: 'Sunset',
    css: 'linear-gradient(135deg, #7c2d12 0%, #ea580c 50%, #f59e0b 100%)',
  },
  {
    id: 'ocean',
    name: 'Ocean',
    css: 'linear-gradient(135deg, #0c4a6e 0%, #0891b2 55%, #14b8a6 100%)',
  },
]

export const getWallpaperPreset = (id) =>
  WALLPAPER_PRESETS.find((p) => p.id === id) || null
