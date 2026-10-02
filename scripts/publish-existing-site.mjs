// Minimal fallback for an existing Sites source checkout when the bundled workflow is unavailable.
// Credential is accepted only in memory over stdin, never saved or printed.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
const git='C:/Program Files/Git/cmd/git.exe';
const node=process.execPath;
const run=(command,args,cwd,env=process.env)=>new Promise((resolve,reject)=>{
 const p=spawn(command,args,{cwd,env,stdio:['ignore','pipe','pipe']});let output='';
 p.stdout.on('data',b=>output+=b);p.stderr.on('data',b=>output+=b);
 p.on('error',reject);p.on('close',code=>code===0?resolve(output.trim()):reject(new Error(`${path.basename(command)} failed (${code}): ${output}`)));
});
const inputReader=readline.createInterface({input:process.stdin,output:process.stdout,terminal:!!process.stdin.isTTY});
inputReader._writeToOutput=()=>{};
console.log('READY_FOR_SITE_INPUT');
inputReader.once('line',async input=>{
 inputReader.close();
 try{
  const p=JSON.parse(input.split(/[\r\n]/)[0]),c=p.credential;
  if(c.auth_mode!=='http_extra_header'||!c.remote_url.startsWith('https://git.chatgpt-team.site/')||c.branch!=='main')throw Error('Unexpected existing source credential');
  const cwd=path.resolve(p.checkout),hosting=JSON.parse(fs.readFileSync(path.join(cwd,'.openai/hosting.json')));
  if(hosting.project_id!==p.project_id)throw Error('Project mismatch');
  const manifestName=p.manifest??'access-publish-files.json';
  if(!/^[a-z0-9-]+-publish-files\.json$/.test(manifestName))throw Error('Invalid scoped manifest name');
  const approvedManifest=path.resolve(cwd,'..',manifestName);
  const files=JSON.parse(fs.readFileSync(approvedManifest,'utf8'));
  if(!Array.isArray(files)||files.length<1||files.length>100||new Set(files).size!==files.length||files.some(f=>typeof f!=='string'||f==='.'||f.includes('..')||path.isAbsolute(f)||f.endsWith('.glb')||!path.resolve(cwd,f).startsWith(cwd+path.sep)))throw Error('Unexpected approved file manifest');
  const base=['-c',`safe.directory=${cwd.replaceAll('\\','/')}`];
  const head=await run(git,[...base,'rev-parse','HEAD'],cwd);
  if(head!==p.expected_head)throw Error('Publisher HEAD changed; inspect before continuing');
  await run(git,[...base,'add','--',...files],cwd);
  await run(git,[...base,'commit','-m',p.message??'Correct observatory approach and finish arboretum avenue'],cwd);
  const sha=await run(git,[...base,'rev-parse','HEAD'],cwd);
  console.log('SOURCE_COMMIT',sha);
  await run(node,['node_modules/typescript/bin/tsc','--noEmit'],cwd);
  console.log(await run(node,['--max-old-space-size=4096','node_modules/vite/bin/vite.js','build','--config','vite.static.config.ts'],cwd));
  const env={...process.env,GIT_CONFIG_COUNT:'2',GIT_CONFIG_KEY_0:'safe.directory',GIT_CONFIG_VALUE_0:cwd.replaceAll('\\','/'),GIT_CONFIG_KEY_1:`http.${c.remote_url}.extraHeader`,GIT_CONFIG_VALUE_1:`Authorization: Bearer ${c.token}`,GIT_TERMINAL_PROMPT:'0'};
  await run(git,['push',c.remote_url,`HEAD:refs/heads/${c.branch}`],cwd,env);
  await run('C:/Windows/System32/tar.exe',['-czf',p.archive,'-C',cwd,'.openai/hosting.json','dist/client'],cwd);
  console.log('SITE_SOURCE_PUSHED_AND_PACKAGED',JSON.stringify({commit_sha:sha,archive:p.archive}));process.exit(0);
 }catch(e){console.error(e.message);process.exit(1);}
});
