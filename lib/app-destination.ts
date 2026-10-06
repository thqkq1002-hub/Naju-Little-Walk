import {destinationFromSearch, type DestinationId} from './destinations.ts';

/** Preserve the detailed default precinct and all regional/deep-link entrances. */
export const activeDestinationId: DestinationId = 'geumseonggwan';
export function appDestinationFromSearch(search: string): DestinationId {
  return destinationFromSearch(search);
}
