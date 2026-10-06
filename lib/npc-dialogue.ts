import {destinations, type DestinationId} from './destinations.ts';
import type {GuideGesture} from './npc-animation.ts';

export type GuideReply = {text: string; gesture: GuideGesture};
/** Local scene guidance and gesture requests. No remote AI or microphone upload. */
export function guideReply(input: string, destinationId: DestinationId, name: string): GuideReply {
  const text = input.trim().slice(0, 240);
  if (/끄덕|동의|맞지|맞아/.test(text)) return {text: '네, 고개를 끄덕여볼게요.', gesture: 'Nod'};
  if (/안녕|인사|손.*흔|반가/.test(text)) return {text: `안녕하세요! 저는 ${name}예요. 함께 둘러볼까요?`, gesture: 'Greeting'};
  if (/가만|멈춰|쉬어|기본.*자세/.test(text)) return {text: '편하게 서서 기다릴게요.', gesture: 'Idle'};
  if (/들어.*줘|들어봐|경청/.test(text)) return {text: '네, 듣고 있어요.', gesture: 'Listen'};
  if(destinationId==='geumseonggwan'){
    if(/지붕|기와|처마/.test(text))return {text:'금성관 정청은 정면 5칸, 측면 4칸의 겹처마 팔작지붕 건물이에요. 전체 보기에서 확대해 기와 골과 처마를 살펴보세요.',gesture:'Explain'};
    if(/단청|기둥|천장|공포/.test(text))return {text:'정청 마루에 들어가면 높은 기둥과 천장, 처마를 받치는 익공을 가까이 볼 수 있어요. 목재의 장식과 단청을 함께 살펴보세요.',gesture:'Explain'};
    if(/문루|망화루|중문|익헌/.test(text))return {text:'남쪽의 망화루에서 중문과 박석길을 따라 정청으로 이어집니다. 정청 양옆에는 동서 익헌이 있어요. 경내 안내도로 원하는 곳으로 이동할 수 있습니다.',gesture:'Explain'};
  }
  const place = destinations[destinationId];
  return {text: `${place.name}에 오신 걸 환영해요. ${place.introduction.join(' ')} 이동은 방향 버튼이나 W A S D, 시선은 화면을 드래그해서 바꿀 수 있어요.`, gesture: 'Explain'};
}
