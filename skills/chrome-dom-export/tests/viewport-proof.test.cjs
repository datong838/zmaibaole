const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
function env(){
 const style={display:'block',visibility:'visible',opacity:'1',transform:'none',clipPath:'none',maskImage:'none',contentVisibility:'visible',webkitLineClamp:'none',overflowX:'visible',overflowY:'visible',position:'static'};
 function element(name,rect={left:10,top:10,right:200,bottom:30,width:190,height:20}){return {innerText:name,parentElement:null,clientLeft:0,clientTop:0,clientWidth:rect.width,clientHeight:rect.height,scrollWidth:rect.width,scrollHeight:rect.height,style:{...style},descendants:[],querySelectorAll(){return this.descendants},getClientRects(){return [rect]},getBoundingClientRect(){return rect},contains(n){return this.descendants.includes(n)}}}
 const root=element('',{left:0,top:0,right:1000,bottom:700,width:1000,height:700});
 const date=element('2026-10-16 ~ 2026-10-19'),header=element('违规原因',{left:10,top:40,right:200,bottom:60,width:190,height:20}),row=element('ID:notice-1 主体 处置方式',{left:10,top:70,right:200,bottom:90,width:190,height:20});
 for(const el of [date,header,row])el.parentElement=root;
 row.tagName='TR';
 const map={'#date':date,'#header':header,'#row':row};let mutation;
 const document={documentElement:root,visibilityState:'visible',hasFocus:()=>true,querySelectorAll:()=>Object.values(map)};
 const tree={kind:'DOM-derived semantic tree (not native AX)',url:'https://life.douyin.com/p/test',root:{name:'fixture',children:[]},truncated:false};
 const frames=[];
 const context={requestAnimationFrame:fn=>frames.push(fn),document,location:{href:'https://life.douyin.com/p/test?groupid=123'},getComputedStyle:e=>e.style,MutationObserver:class {constructor(cb){mutation=cb}observe(){}},addEventListener(){},TextEncoder,URL,crypto:crypto.webcrypto};
 vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/../extension/viewport-proof.js','utf8'),context);
 const elements=[['d','date-filter','#date',date.innerText,null],['h','header','#header',header.innerText,null],['r','row','#row',row.innerText,'notice-1']].map(([key,kind,selector,expected_text,notice_id])=>({key,kind,locator:{by:'selector',value:selector},expected_text,notice_id}));
 const cmd={op:'viewport-proof',tabId:5,windowId:3,groupid:'123',source_sha256:'a'.repeat(64),dom_sha256:crypto.createHash('sha256').update(JSON.stringify(tree)).digest('hex'),elements,channel:'local-dom-export-v1'};
 return {context,map,root,row,header,date,tree,cmd,element,frames,mutation:()=>mutation(),run:()=>context.__localViewportProof.proof(cmd,q=>map[q.value],()=>tree)};
}
test('public proof contains booleans and semantic bindings, no rectangles',async()=>{const e=env(),r=await e.run();assert.equal(r.all_fully_visible,true);const s=JSON.stringify(r);for(const key of ['left','right','top','bottom','width','height','x','y'])assert.equal(new RegExp('"'+key+'"\\s*:').test(s),false);assert.equal(r.dom_sha256,e.cmd.dom_sha256)});
test('partially offscreen row is not covered',async()=>{const e=env();e.row.getClientRects=()=>[{left:1,top:690,right:50,bottom:730,width:49,height:40}];const r=await e.run();assert.equal(r.all_fully_visible,false);assert.equal(r.elements[2].viewport_contained,false)});
test('ancestor scroll clip rejects row coverage',async()=>{const e=env();const parent=e.element('container',{left:0,top:0,right:100,bottom:20,width:100,height:20});parent.style.overflowY='auto';parent.parentElement=e.root;e.row.parentElement=parent;const r=await e.run();assert.equal(r.elements[2].fully_visible,false)});
test('line clamp and overflowing text are rejected',async()=>{for(const key of ['clamp','overflow']){const e=env();if(key==='clamp'){e.row.style.webkitLineClamp='2';e.row.scrollHeight=e.row.clientHeight+20;}else{e.row.style.overflowX='hidden';e.row.scrollWidth=999}assert.equal((await e.run()).elements[2].text_unclipped,false)}});
test('possible positioned overlay fails closed without point probing',async()=>{const e=env();const overlay=e.element('overlay');overlay.getClientRects=e.row.getClientRects;overlay.style.position='fixed';e.map.overlay=overlay;assert.equal((await e.run()).elements[2].possible_overlay_absent,false)});
test('unsupported transform fails closed',async()=>{const e=env();e.row.style.transform='matrix(1,0,0,1,0,0)';assert.equal((await e.run()).all_fully_visible,false)});
test('wrong source DOM hash and changed visible text reject',async()=>{const e=env();e.cmd.dom_sha256='f'.repeat(64);await assert.rejects(e.run(),/observed-dom-sha-mismatch/);const a=env();a.row.innerText='different';await assert.rejects(a.run(),/semantic-text-changed/)});
test('DOM mutation during asynchronous SHA rejects',async()=>{const e=env();e.context.crypto={subtle:{digest:async(...args)=>{e.mutation();return crypto.webcrypto.subtle.digest(...args)}}};await assert.rejects(e.run(),/dom-or-layout-changed/)});
test('generic missing row IDs or duplicate semantic keys reject',async()=>{const e=env();e.cmd.elements[2].notice_id='missing-id';await assert.rejects(e.run(),/notice-id-invalid/);const a=env();a.cmd.elements[1].key='d';await assert.rejects(a.run(),/key-invalid/)});

test('zero area row cannot be covered',async()=>{const e=env();e.row.getClientRects=()=>[{left:10,top:10,right:10,bottom:10,width:0,height:0}];assert.equal((await e.run()).elements[2].fully_visible,false)});
test('legacy clip opacity and filter still fail closed',async()=>{for(const [field,value] of [['clip','rect(0px,0px,0px,0px)'],['opacity','0.1'],['filter','opacity(0)']]){const e=env();e.row.style[field]=value;assert.equal((await e.run()).all_fully_visible,false,field)}});
test('static and relative overlays fail closed too',async()=>{for(const position of ['static','relative']){const e=env();const cover=e.element('cover');cover.getClientRects=e.row.getClientRects;cover.style.position=position;e.map.cover=cover;assert.equal((await e.run()).all_fully_visible,false)}});
test('ID span cannot impersonate a semantic record row',async()=>{const e=env();e.row.tagName='SPAN';await assert.rejects(e.run(),/row-semantics-missing/)});
test('internal layout position drift invalidates a prior proof epoch without exporting coordinates',async()=>{const e=env();const a=await e.run();e.row.getClientRects=()=>[{left:20,top:70,right:210,bottom:90,width:190,height:20}];const b=await e.run();assert.notEqual(a.epoch,b.epoch);assert.equal(b.all_fully_visible,true)});

test('frame monitor catches out-and-back layout drift between two equal visible proofs',async()=>{const e=env(),a=await e.run(),original=e.row.getClientRects;e.row.getClientRects=()=>[{left:1,top:900,right:100,bottom:920,width:99,height:20}];e.frames.shift()();e.row.getClientRects=original;e.frames.shift()();const b=await e.run();assert.equal(a.all_fully_visible,true);assert.equal(b.all_fully_visible,true);assert.notEqual(a.epoch,b.epoch)});


test('idle transition and animation declarations permit stable complete coverage',async()=>{
 for(const owner of ['row','root']){const e=env();e[owner].style.transitionDuration='0s, 2s';e[owner].style.animationName='move';e[owner].getAnimations=()=>[];assert.equal((await e.run()).all_fully_visible,true,owner)}
});
test('finished or idle instantiated animations permit stable complete coverage',async()=>{
 for(const playState of ['finished','idle']){const e=env();e.row.style.animationName='move';e.row.getAnimations=()=>[{playState,pending:false}];assert.equal((await e.run()).all_fully_visible,true,playState)}
});
test('running and pending animations reject even with unchanged instantaneous geometry',async()=>{
 for(const owner of ['row','root'])for(const animation of [{playState:'running',pending:false},{playState:'idle',pending:true}]){const e=env();e[owner].getAnimations=()=>[animation];assert.equal((await e.run()).elements[2].unsupported_css_absent,false,owner)}
});
test('a declared line clamp with fully fitting text is not truncation',async()=>{
 const e=env();e.row.style.webkitLineClamp='2';e.row.style.overflowY='hidden';assert.equal((await e.run()).elements[2].text_unclipped,true);assert.equal((await e.run()).all_fully_visible,true)
});
test('actual clamped descendant text overflow remains ineligible',async()=>{
 const e=env();const child=e.element('body',e.row.getBoundingClientRect());child.parentElement=e.row;child.style.webkitLineClamp='2';child.scrollHeight=child.clientHeight+40;e.row.descendants.push(child);assert.equal((await e.run()).elements[2].text_unclipped,false)
});

test('bounded overlay diagnostics preserve failure and omit text/background URI',async()=>{
 const e=env();for(let i=0;i<15;i++){
  const cover=e.element('PRIVATE TEXT '+i);cover.tagName='DIV';cover.nodeType=1;cover.getAttribute=k=>k==='class'?'watermark':'';cover.style.position='fixed';cover.style.pointerEvents='none';cover.style.backgroundColor='rgba(0, 0, 0, 0)';cover.style.backgroundImage='url(https://private.invalid/token=secret)';cover.getClientRects=e.row.getClientRects;e.map['cover'+i]=cover;
 }
 const r=await e.run(),row=r.elements[2],diag=row.possible_overlay_diagnostic;
 assert.equal(row.possible_overlay_absent,false);assert.equal(row.fully_visible,false);assert.equal(r.all_fully_visible,false);
 assert.equal(diag.candidates.length,12);assert.equal(diag.candidate_count,15);assert.equal(diag.truncated,true);
 assert.equal(diag.candidates[0].has_text,true);assert.equal(diag.candidates[0].background_image_present,true);assert.equal(r.pixel_coordinates_returned,false);assert.equal(r.pixel_actions_used,false);
 assert.equal(JSON.stringify(r).includes('PRIVATE TEXT'),false);assert.equal(JSON.stringify(r).includes('private.invalid'),false);assert.equal(JSON.stringify(r).includes('token=secret'),false);
});
test('diagnostic contains no coordinates and no-overlay visibility unchanged',async()=>{const e=env(),clean=await e.run();assert.equal(clean.all_fully_visible,true);assert.equal(clean.pixel_coordinates_returned,false);const cover=e.element('cover');cover.tagName='DIV';cover.nodeType=1;cover.getClientRects=e.row.getClientRects;e.map.cover=cover;const r=await e.run();for(const key of ['left','right','top','bottom','width','height','x','y'])assert.equal(new RegExp('\"'+key+'\"\\s*:').test(JSON.stringify(r)),false);assert.equal(r.elements[2].fully_visible,false)});
test('new diagnostic build replaces a stale global module',()=>{const e=env();assert.equal(e.context.__localViewportProof.build,'viewport-notice-business-cells-v9-provider-manual-preview-v2');e.context.__localViewportProof={build:'old'};vm.runInContext(fs.readFileSync(__dirname+'/../extension/viewport-proof.js','utf8'),e.context);assert.equal(typeof e.context.__localViewportProof.proof,'function')});

test('containment diagnostic identifies exact ancestor axis without changing flags',async()=>{
 const e=env(),parent=e.element('container',{left:0,top:0,right:100,bottom:20,width:100,height:20});
 parent.nodeType=1;parent.tagName='DIV';parent.id='clip';parent.parentElement=e.root;parent.style.overflowY='auto';e.row.parentElement=parent;e.context.CSS={escape:x=>x};
 const r=await e.run(),row=r.elements[2],d=row.containment_diagnostic;
 assert.equal(row.viewport_contained,false);assert.equal(row.fully_visible,false);assert.equal(d.scope,'target-and-descendants');assert.equal(d.reason_count,1);assert.equal(d.reasons[0].ancestor_selector,'#clip');assert.equal(d.reasons[0].axis,'y');assert.equal(d.reasons[0].reason,'ancestor-overflow');assert.equal(d.truncated,false);
 assert.equal(r.pixel_coordinates_returned,true);assert.equal(d.coordinate_space,'CSS-viewport-diagnostic-only');assert.equal(d.reasons[0].axis_excess.trailing,70);assert.equal(d.reasons[0].ancestor.clientHeight,20);
});
test('viewport diagnostics specify axis and ancestor diagnostics are bounded with explicit truncation',async()=>{
 const e=env();e.row.getClientRects=()=>[{left:-10,top:710,right:300,bottom:740,width:310,height:30}];let last=e.root;
 for(let i=0;i<15;i++){const p=e.element('',{left:0,top:0,right:100,bottom:20,width:100,height:20});p.nodeType=1;p.tagName='DIV';p.id='clip'+i;p.parentElement=last;p.style.overflowX='hidden';p.style.overflowY='auto';last=p;}e.row.parentElement=last;e.context.CSS={escape:x=>x};
 const row=(await e.run()).elements[2],d=row.containment_diagnostic;assert.equal(row.viewport_contained,false);assert.equal(d.reasons.length,12);assert.equal(d.truncated,true);assert.equal(d.reason_count,32);assert.equal(d.reasons[0].reason,'outside-viewport');assert.equal(d.reasons[0].axis,'x');assert.equal(d.reasons[1].axis,'y');
});
test('fully contained element has empty containment diagnostic with unchanged true flags',async()=>{const row=(await env().run()).elements[2];assert.equal(row.viewport_contained,true);assert.equal(row.fully_visible,true);assert.equal(row.containment_diagnostic.reason_count,0);assert.equal(row.containment_diagnostic.truncated,false)});

test('actual offending descendant and exact public clip metrics are diagnostic only',async()=>{
 const e=env(),frame=e.element('frame',{left:0,top:0,right:300,bottom:100,width:300,height:100}),child=e.element('SECRET CHILD TEXT',{left:10,top:75,right:200,bottom:110,width:190,height:35});
 e.context.CSS={escape:x=>x};for(const [el,id] of [[frame,'frame'],[e.row,'target'],[child,'offender']]){el.nodeType=1;el.tagName='DIV';el.id=id;}e.row.tagName='TR';
 frame.clientTop=1;frame.clientHeight=99;frame.scrollTop=0;frame.style.overflowY='auto';frame.style.borderTopWidth='0.8px';frame.style.paddingTop='3.2px';frame.parentElement=e.root;e.row.parentElement=frame;child.parentElement=e.row;e.row.descendants.push(child);
 const result=await e.run(),row=result.elements[2],reason=row.containment_diagnostic.reasons.find(x=>x.offender_selector==='#offender');
 assert.equal(row.viewport_contained,false);assert.equal(row.fully_visible,false);assert.equal(result.pixel_coordinates_returned,true);assert.equal(result.pixel_actions_used,false);assert.equal(reason.target_selector,'#target');assert.equal(reason.ancestor_selector,'#frame');assert.equal(reason.axis,'y');assert.equal(reason.axis_excess.trailing,10);assert.equal(reason.ancestor.style.borderTopWidth,'0.8px');assert.equal(reason.ancestor.style.paddingTop,'3.2px');assert.equal(reason.offender.rect.bottom,110);assert.equal(reason.checked_rect.bottom,110);assert.equal(reason.clip_box.bottom,100);assert.equal(JSON.stringify(row.containment_diagnostic).includes('SECRET'),false);
});

test('stable hidden padding clip uses exact fractional borders, legacy still rounds',()=>{
 const e=env(),f=e.element('frame',{left:287.998046875,top:390.595703125,right:1712.001953125,bottom:1509.0625,width:1424.00390625,height:1118.466796875});
 Object.assign(f,{clientLeft:1,clientTop:1,clientWidth:1423,clientHeight:1117});Object.assign(f.style,{display:'flex',overflowX:'hidden',overflowY:'hidden',scrollbarGutter:'auto',borderLeftWidth:'0.625px',borderTopWidth:'0.625px',borderRightWidth:'0.625px',borderBottomWidth:'0.625px'});
 const api=e.context.__localViewportProof,box=api.overflowClipBox(f,f.style,f.getBoundingClientRect(),true);assert.equal(box.left,288.623046875);assert.equal(box.top,391.220703125);assert.equal(api.overflowClipBox(f,f.style,f.getBoundingClientRect()).left,288.998046875);
 const child=e.element('th',{left:288.623046875,top:391.220703125,right:558.623046875,bottom:444.84375,width:270,height:53.623046875});child.parentElement=f;f.parentElement=e.root;
 assert.equal(api.geometry(child,{left:0,top:0,right:1800,bottom:2000}).viewport_contained,false);assert.equal(api.geometry(child,{left:0,top:0,right:1800,bottom:2000},true).viewport_contained,true);
 child.getClientRects=()=>[{left:288.523046875,top:391.220703125,right:558.623046875,bottom:444.84375,width:270.1,height:53.623046875}];assert.equal(api.geometry(child,{left:0,top:0,right:1800,bottom:2000},true).viewport_contained,false);
});
test('actual fractional clamp box passes exact edge, any real tiny excess still rejects',()=>{
 const e=env(),rect={left:1334.619140625,top:407.216796875,right:1414.619140625,bottom:429.21875,width:80,height:22.001953125},p=e.element('clamp',rect),child=e.element('span',rect);Object.assign(p,{clientWidth:80,clientHeight:22});Object.assign(p.style,{display:'inline-block',overflowX:'hidden',overflowY:'hidden',scrollbarGutter:'auto',borderLeftWidth:'0px',borderTopWidth:'0px',borderRightWidth:'0px',borderBottomWidth:'0px'});p.parentElement=e.root;child.parentElement=p;const api=e.context.__localViewportProof,view={left:0,top:0,right:1800,bottom:2000};
 assert.equal(api.geometry(child,view).viewport_contained,false);assert.equal(api.geometry(child,view,true).viewport_contained,true);child.getClientRects=()=>[{...rect,bottom:rect.bottom+0.001,height:rect.height+0.001}];assert.equal(api.geometry(child,view,true).viewport_contained,false);
});
test('auto scroll clip unknown gutters transforms and invalid border facts retain old conservative box',()=>{
 for(const change of [{overflowY:'auto'},{overflowX:'scroll'},{scrollbarGutter:'stable'},{scrollbarGutter:undefined},{transform:'matrix(1,0,0,1,0,0)'},{borderLeftWidth:'unknown'},{borderRightWidth:'-1px'}]){
  const e=env(),p=e.element('frame',{left:0,top:0,right:100.5,bottom:100.5,width:100.5,height:100.5});Object.assign(p,{clientLeft:1,clientTop:1,clientWidth:99,clientHeight:99});Object.assign(p.style,{display:'flex',overflowX:'hidden',overflowY:'hidden',scrollbarGutter:'auto',borderLeftWidth:'0.625px',borderTopWidth:'0.625px',borderRightWidth:'0.625px',borderBottomWidth:'0.625px'},change);const api=e.context.__localViewportProof;assert.deepEqual(api.overflowClipBox(p,p.style,p.getBoundingClientRect(),true),api.overflowClipBox(p,p.style,p.getBoundingClientRect(),false));
 }
});

test('saved actual v4 padding edge errors resolve but a truly clipped filter icon remains rejected',()=>{
 const base=require('node:path').resolve(__dirname,'../../../work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/screenshot-observations/009-page1-anchor-stable5v4-viewport-raw-reply.json'),saved=JSON.parse(fs.readFileSync(base,'utf8')).result;
 const e=env(),api=e.context.__localViewportProof;let aligned=0;const stillClipped=[];
 for(const header of saved.elements.filter(e=>e.kind==='header'))for(const reason of header.containment_diagnostic.reasons){
  const a=reason.ancestor,node={...a,getAnimations:()=>[]},style={...a.style,transform:'none',opacity:'1',scrollbarGutter:'auto'};
  // Fixture supplies actual recorded rect/borders/client sizes. Explicit supported
  // no-transform/no-gutter conditions are test inputs, not added live evidence.
  const box=api.overflowClipBox(node,style,a.rect,true),r=reason.checked_rect;
  if(r.left>=box.left&&r.right<=box.right&&r.top>=box.top&&r.bottom<=box.bottom)aligned++;else stillClipped.push({header:header.key,topExcess:box.top-r.top});
 }
 assert.equal(aligned,8);assert.equal(stillClipped.length,1);assert.equal(stillClipped[0].header,'gov-records-stable5-v1:header4');assert.equal(stillClipped[0].topExcess,1.494140625);
});
