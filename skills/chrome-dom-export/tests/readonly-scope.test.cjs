// Fake Chrome only. Original execute/content code runs; no OS/browser/HTTP.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const extension=path.join(__dirname,'../extension');
function setup(mode){
 let enumerations=0,targets=0,injections=0,messages=[],inputs=0,now=0,events=[];
 const deny=async()=>{inputs++;throw Error('INPUT FORBIDDEN');};
 const context={URL,AbortSignal,Date,crypto:require('node:crypto').webcrypto,performance:{now:()=>++now},
 chrome:{runtime:{id:'a'.repeat(32),getManifest:()=>({version:'1.0.21'}),getURL:s=>'chrome-extension://'+'a'.repeat(32)+'/'+s,onInstalled:{addListener:()=>{}},onStartup:{addListener:()=>{}},onMessage:{addListener:()=>{}}},alarms:{onAlarm:{addListener:()=>{}},create:async()=>{}},action:{onClicked:{addListener:()=>{}}},
 windows:{getAll:async opts=>{assert.deepEqual(JSON.parse(JSON.stringify(opts)),{populate:true});events.push('tabs');enumerations++;if(mode==='error'&&enumerations===2)throw Error('original-enumeration-error');const windowId=mode==='window'&&enumerations===2?99:8;const tab={id:9,windowId,title:'original title',active:mode!=='inactive',url:mode==='site'?'https://evil.test/':'https://life.douyin.com/p/home?groupid=222'};return [{id:windowId,type:'normal',focused:mode!=='inactive',tabs:mode==='duplicate'?[tab,tab]:[tab]}];},update:deny},
 tabs:{get:async id=>{assert.equal(id,9);targets++;return {id,windowId:8,url:'https://life.douyin.com/p/home?groupid=222'};},sendMessage:async(id,m,frame)=>{messages.push(m.op);assert.equal(frame.frameId,0);if(m.op==='ping'){events.push('ping');return {ok:true,result:{version:mode==='version'?'old':'dom-only-20261021-11',safety:'DOM-only',url:'https://life.douyin.com/p/home'}};}events.push('tree');return {ok:true,result:{url:'https://life.douyin.com/p/home',truncated:false,root:{children:[]}}};},update:deny,create:deny},scripting:{executeScript:async opts=>{injections++;assert.equal(opts.world,'ISOLATED');assert.deepEqual(JSON.parse(JSON.stringify(opts.files)),['policy.js','viewport-proof.js','review-proof.js','region-proof.js','content.js']);}},downloads:{search:deny},storage:{session:{get:deny,set:deny}}}};
 context.importScripts=(...names)=>{for(const name of names){if(name==='config.js')context.LOCAL_BRIDGE_CONFIG={base:'http://127.0.0.1:17341',bridgeToken:'fake'};else vm.runInContext(fs.readFileSync(path.join(extension,name),'utf8'),context);}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(extension,'sw15.js'),'utf8'),context);
 return {run:async c=>{for(let i=0;i<10;i++)await Promise.resolve();return vm.runInContext(`execute(${JSON.stringify(c)})`,context);},stats:()=>({enumerations,targets,injections,messages,inputs,events})};
}
(async()=>{
 let h=setup();const command={op:'readonly-scope',tabId:9,windowId:8};let result=await h.run(command);result=JSON.parse(JSON.stringify(result));assert.equal(result.schema,'readonly-scope-v1');assert.deepEqual(result.commands,[{op:'tabs'},{op:'ping',tabId:9},{op:'tree',tabId:9},{op:'tabs'}]);assert.deepEqual(h.stats(),{enumerations:2,targets:2,injections:2,messages:['ping','ping','tree'],inputs:0,events:['tabs','ping','ping','tree','tabs']});assert.deepEqual(result.timing.steps.map(x=>x.op),['tabs','ping','tree','tabs']);assert.ok(result.timing.steps.every(x=>x.elapsed_ms===1));assert.equal(result.timing.clock,'worker-performance-now');assert.ok(result.timing.elapsed_ms>=4);assert.equal(result.before[0].tabs[0].title,'original title');assert.equal(result.after[0].focused,true);
 // New scope performs the exact original APIs twice; active/focus are retained.
 h=setup('inactive');result=await h.run(command);assert.equal(result.before[0].focused,false);assert.equal(result.after[0].tabs[0].active,false);
 for(const mode of ['window','site','duplicate','version','error']){h=setup(mode);await assert.rejects(()=>h.run(command));assert.equal(h.stats().inputs,0);assert.ok(h.stats().enumerations<=2);}
 for(const bad of [{...command,ops:['click']},{...command,locator:{by:'selector',value:'body'}},{...command,tabId:true},{...command,tabId:-1},{...command,windowId:1.5},{...command,windowId:9007199254740992}]){h=setup();await assert.rejects(()=>h.run(bad),/fields-denied/);assert.equal(h.stats().enumerations,0);assert.equal(h.stats().inputs,0);}
 // Old individual operation contract and unsupported arbitrary API stay intact.
 h=setup();result=await h.run({op:'tabs'});assert.equal(result[0].tabs[0].allowed,true);assert.equal(h.stats().enumerations,1);await assert.rejects(()=>h.run({op:'evaluate',script:'bad'}),/unsupported operation/);
 console.log('readonly-scope fixed sequence/public API counts/fields/clock/cap/errors/legacy operations PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
