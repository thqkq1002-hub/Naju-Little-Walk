import type {DestinationId} from './destinations.ts';

/**
 * Background loops by Kevin MacLeod (incompetech.com), licensed CC BY 4.0.
 * Changes: re-encoded from the 265–320 kbps originals to 96 kbps stereo MP3 without cover art.
 */
export const bgmTracks={
  'meditation-impromptu-02':{title:'Meditation Impromptu 02',mood:'역사 장소의 고요한 산책'},
  'meditation-impromptu-01':{title:'Meditation Impromptu 01',mood:'영산강 옛 포구의 정취'},
  'wallpaper':{title:'Wallpaper',mood:'숲과 강변의 상쾌한 걸음'},
  'easy-lemon':{title:'Easy Lemon',mood:'밝고 깨끗한 혁신도시'},
  'fluffing-a-duck':{title:'Fluffing a Duck',mood:'경쾌한 학교 나들이'},
} as const;
export type BgmTrackId=keyof typeof bgmTracks;

export const bgmForDestination:Record<DestinationId,BgmTrackId>={
  geumseonggwan:'meditation-impromptu-02',bogam:'meditation-impromptu-02','bogam-museum':'meditation-impromptu-02','yeongsanpo-history':'meditation-impromptu-02',
  yeongsanpo:'meditation-impromptu-01','yeongsanpo-literature':'meditation-impromptu-01',
  'naju-arboretum':'wallpaper',deudeulgang:'wallpaper',neureoji:'wallpaper',
  bitgaram:'easy-lemon','bitgaram-park':'easy-lemon','bitgaram-kepco':'easy-lemon','bitgaram-kentech':'easy-lemon','bitgaram-observatory':'easy-lemon',
  dasi:'fluffing-a-duck',
};

export const bgmUrl=(id:BgmTrackId)=>`/audio/bgm/${id}.mp3`;
export const bgmCredit=(id:BgmTrackId)=>`“${bgmTracks[id].title}” Kevin MacLeod (incompetech.com)`;
export const BGM_SOURCE_URL='https://incompetech.com/music/royalty-free/music.html';
export const BGM_LICENSE_URL='https://creativecommons.org/licenses/by/4.0/';
