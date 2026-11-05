const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const extension=path.join(__dirname,'../extension');
test('runtime version remains visible when polling replaces status',async()=>{
  const elements=new Map(['identity','loaded-version','status','refresh'].map(key=>[key,{textContent:'',addEventListener(){}}]));
  let interval,reply={control_protocol:'local-dom-control-v1',request_accepted:true,busy:true},reloads=0;
  const context={document:{getElementById:key=>elements.get(key)},performance:{now:()=>0},setInterval:fn=>interval=fn,chrome:{runtime:{id:'synthetic-extension-id',getManifest:()=>({version:'1.0.20'}),reload:()=>reloads++,sendMessage:async()=>reply}}};
  vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(extension,'control.js'),'utf8'),context);await new Promise(setImmediate);
  assert.equal(JSON.parse(elements.get('status').textContent).state,'busy');
  assert.equal(elements.get('loaded-version').textContent,'已加载扩展版本：1.0.20');
  reply={control_protocol:'local-dom-control-v1',request_accepted:true,connected:true,idle:true};
  await interval();
  assert.equal(JSON.parse(elements.get('status').textContent).state,'connected');
  assert.equal(elements.get('loaded-version').textContent,'已加载扩展版本：1.0.20');
  assert.equal(reloads,0);
  assert.match(fs.readFileSync(path.join(extension,'control.html'),'utf8'),/<pre id="loaded-version"><\/pre><pre id="status">/);
});
