// Builds a self-contained Windows folder for playing 나주 산책 without internet, e.g. from a USB stick.
// Run `npm run package:usb` (builds first). Output: ../나주산책-USB next to this repository, or the path given.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.resolve(process.argv[2]??path.join(repo,'..','나주산책-USB'));
const dist=path.join(repo,'dist','client');
if(!fs.existsSync(path.join(dist,'index.html')))throw new Error('dist/client is missing: run npm run build first');
if(fs.existsSync(out)&&!fs.existsSync(path.join(out,'runtime','serve.mjs')))throw new Error(`Refusing to replace a folder that is not a USB package: ${out}`);

fs.rmSync(out,{recursive:true,force:true});
fs.mkdirSync(path.join(out,'runtime'),{recursive:true});
fs.cpSync(dist,path.join(out,'app'),{recursive:true});
fs.copyFileSync(path.join(repo,'scripts','usb','serve.mjs'),path.join(out,'runtime','serve.mjs'));
fs.copyFileSync(process.execPath,path.join(out,'runtime','node.exe'));

const crlf=s=>s.replace(/\r?\n/g,'\r\n');
fs.writeFileSync(path.join(out,'나주산책-실행.bat'),crlf(`@echo off
chcp 65001 >nul
title Naju Walk
"%~dp0runtime\\node.exe" "%~dp0runtime\\serve.mjs"
if errorlevel 1 pause
`));

const bgm=fs.readFileSync(path.join(repo,'knowledge','bgm-2026-10-06.md'),'utf8').match(/\| `public\/audio\/bgm\/[^|]+\| ([^|]+) \|/g)?.map(row=>row.split('|')[2].trim())??[];
fs.writeFileSync(path.join(out,'사용법.txt'),crlf(`나주 산책 · 오프라인 실행판 (Windows)

[실행]
1. 이 폴더 전체를 USB나 컴퓨터에 복사합니다. 폴더 안의 파일 위치는 바꾸지 마세요.
2. "나주산책-실행.bat"을 더블클릭합니다.
3. 검은 창이 열리고 잠시 뒤 기본 브라우저에서 나주 산책이 열립니다.
   열리지 않으면 검은 창에 표시된 주소(예: http://127.0.0.1:3000/)를 Chrome이나 Edge에 입력하세요.
4. 다 쓰면 검은 창을 닫습니다.

[알아 두기]
- 인터넷 없이 동작합니다. 앱은 이 컴퓨터 안(127.0.0.1)에서만 열리며 다른 기기에서는 접속되지 않습니다.
- Chrome 또는 Edge 최신 버전을 권장합니다. 3D 화면이라 그래픽 성능이 낮은 PC에서는 느릴 수 있습니다.
- 안내 캐릭터 음성은 Windows의 한국어 음성(Microsoft Heami)을 사용합니다.
  없으면 [설정 > 시간 및 언어 > 음성]에서 한국어 음성을 추가하세요. 음성이 없으면 글로 안내합니다.
- "Windows의 PC 보호" 창이 뜨면 [추가 정보 > 실행]을 누르세요.
- 화면 안의 출처 링크(지도·사진·음악)는 인터넷이 연결되어 있을 때만 열립니다.

[포함된 자료와 이용 조건]
- 지도 자료: © OpenStreetMap 기여자, ODbL (https://www.openstreetmap.org/copyright)
- 배경음악: Kevin MacLeod (incompetech.com), CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
  ${bgm.join(', ')} · 웹용 96kbps로 변환
- 실행기: Node.js ${process.version} (runtime/node.exe), MIT 라이선스 · runtime/NODE-LICENSE.txt 참고
- 각 장소의 참고 자료와 한계는 앱의 "자료·제작 정보"에서 볼 수 있습니다.

만든 날: ${new Date().toISOString().slice(0,10)}
`));

fs.writeFileSync(path.join(out,'runtime','NODE-LICENSE.txt'),crlf(`Node.js ${process.version}

Node.js is licensed for use as follows:

Copyright Node.js contributors. All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

The binary also bundles third-party components (V8, libuv, OpenSSL, ICU and others)
under their own licenses. The complete text is at
https://github.com/nodejs/node/blob/${process.version}/LICENSE
`));

const size=dir=>fs.readdirSync(dir,{withFileTypes:true}).reduce((s,e)=>s+(e.isDirectory()?size(path.join(dir,e.name)):fs.statSync(path.join(dir,e.name)).size),0);
console.log(`USB package: ${out} (${(size(out)/1048576).toFixed(0)} MB)`);
