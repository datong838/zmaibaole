/* Public DOM geometry is returned only for evidence cropping, never UI input. */
(()=>{
 const BUILD='region-notice-business-cells-v12-manual-date-fragment-v2';
 const PAINT_REVISION='normal-review-exact-zero-ancestor-v2';
 if(globalThis.__localRegionProof?.build===BUILD&&globalThis.__localRegionProof?.paintVisibilityRevision===PAINT_REVISION)return;
 const need=(v,c)=>{if(!v)throw Error(c)},norm=v=>String(v??'').replace(/\s+/g,' ').trim();
 const finiteRect=r=>[r.left,r.top,r.right,r.bottom,r.width,r.height].every(Number.isFinite)&&r.width>0&&r.height>0;
 const intersects=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
 const inside=(a,b)=>a.left>=b.left&&a.top>=b.top&&a.right<=b.right&&a.bottom<=b.bottom;
 const rect=e=>{const r=e.getBoundingClientRect();need(finiteRect(r),'region-element-no-rectangle');return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
 function painted(el){const s=getComputedStyle(el);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0)return false;
  const color=s.backgroundColor||'';const background=color&&color!=='transparent'&&!/^rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(color);
  return Boolean(background||s.backgroundImage&&s.backgroundImage!=='none'||['IMG','SVG','CANVAS','VIDEO','IFRAME'].includes(el.tagName)||!el.children.length&&norm(el.innerText));
 }
 // Normal-review foreign paint only. A standard opacity:0 ancestor composites
 // the entire subtree to zero. No epsilon/low-alpha or class-name exception.
 function zeroOpacityAncestor(el){
  const chain=[];let zero=false;
  for(let n=el;n;n=n.parentElement){const s=getComputedStyle(n),text=String(s.opacity??'').trim(),opacity=Number(text);if(!text||!Number.isFinite(opacity)||opacity<0||opacity>1)return null;chain.push({node:n,opacity});if(n!==el&&opacity===0)zero=true;}
  if(!zero)return null;
  for(const {node}of chain){
   // Top-layer boxes escape ordinary ancestor compositing; never infer absence.
   if(typeof node.matches!=='function'||typeof node.getAnimations!=='function')return null;
   try{if(node.matches(':modal')||node.matches(':popover-open')||document.fullscreenElement===node)return null;}catch{return null;}
   if(node.getAnimations().some(a=>a.pending||a.playState==='running'))return null;
  }
  return chain;
 }
 function sameZeroOpacityAncestor(el,before){const after=zeroOpacityAncestor(el);return after&&after.length===before.length&&after.every((a,i)=>a.node===before[i].node&&a.opacity===before[i].opacity);}
 function stableVisible(el){for(let p=el;p;p=p.parentElement){const s=getComputedStyle(p);need(s.display!=='none'&&s.visibility!=='hidden'&&s.visibility!=='collapse'&&Number(s.opacity)!==0,'region-element-hidden');need(!s.transform||s.transform==='none','region-unsupported-transform');if(typeof p.getAnimations==='function')need(!p.getAnimations().some(a=>a.pending||a.playState==='running'),'region-running-animation');}}
 const hashBytes=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
 function safeSVG(text){
  const xml=text.replace(/^\s*<\?xml\s+[^?]*\?>/i,'');
  need(!/<!|<\?|\b(?:href|xlink:href)\s*=|\bon[a-z]+\s*=|url\s*\(|@import|@font-face/i.test(xml),'unsafe-static-svg-source');
  need(typeof DOMParser==='function','static-svg-parser-unavailable');const doc=new DOMParser().parseFromString(xml,'image/svg+xml');
  need(doc.documentElement?.localName==='svg'&&!doc.querySelector('parsererror'),'invalid-static-svg');
  const tags=new Set(['svg','g','path','rect','circle','ellipse','line','polyline','polygon','text','tspan']);
  const attributes=new Set(['xmlns','width','height','viewbox','preserveaspectratio','x','y','x1','x2','y1','y2','cx','cy','r','rx','ry','d','points','fill','fill-opacity','fill-rule','stroke','stroke-opacity','stroke-width','stroke-linecap','stroke-linejoin','transform','opacity','font-family','font-size','font-weight','text-anchor','style']);const counts={};
  const all=[doc.documentElement,...doc.documentElement.querySelectorAll('*')];need(all.length<=1000,'static-svg-structure-limit');
  for(const el of all){need(tags.has(el.localName),'unsafe-static-svg-element');counts[el.localName]=(counts[el.localName]||0)+1;
   for(const attr of el.attributes){const key=attr.name.toLowerCase(),value=attr.value;need(attributes.has(key)&&!/^on/.test(key)&&!/url\s*\(|href|@|[\\]/i.test(value),'unsafe-static-svg-attribute');
    if(key==='xmlns')need(value==='http://www.w3.org/2000/svg','unsafe-static-svg-namespace');
    if(key==='style')for(const item of value.split(';').filter(Boolean)){const k=item.split(':',1)[0].trim();need(['fill','fill-opacity','stroke','stroke-opacity','stroke-width','opacity','font-family','font-size','font-weight','text-anchor'].includes(k),'unsafe-static-svg-style');}
   }
  }
  return {safe_static_svg:true,tags:counts,external_resources:false,script_or_events:false};
 }
 function gradientAlpha(bg){
  if(!/^(?:repeating-)?(?:linear|radial|conic)-gradient\(/i.test(bg)||/url\s*\(|var\s*\(|@|[\\]/i.test(bg)||(bg.match(/gradient\(/gi)||[]).length!==1)return null;
  const alpha=[];let rest=bg.replace(/rgba?\(([^()]*)\)/gi,(_,inside)=>{const slash=inside.split('/');let a=1;if(slash.length===2){const t=slash[1].trim();a=t.endsWith('%')?Number(t.slice(0,-1))/100:Number(t);}else{const p=inside.split(',');if(p.length===4){const t=p[3].trim();a=t.endsWith('%')?Number(t.slice(0,-1))/100:Number(t);}}alpha.push(a);return ' COLOR ';});
  rest=rest.replace(/#[0-9a-f]{3,8}\b/gi,v=>{const h=v.slice(1);if(![3,4,6,8].includes(h.length)){alpha.push(NaN);return '';}alpha.push(h.length===4?parseInt(h[3],16)/15:h.length===8?parseInt(h.slice(6),16)/255:1);return ' COLOR ';}).replace(/\btransparent\b/gi,()=>{alpha.push(0);return ' COLOR ';});
  rest=rest.replace(/(?:\d+(?:\.\d*)?|\.\d+)(?:deg|turn|rad|grad|px|em|rem)\b/gi,'');
  rest=rest.replace(/(?:repeating-)?(?:linear|radial|conic)-gradient/gi,'').replace(/\b(?:COLOR|to|top|bottom|left|right|center|circle|ellipse|closest-side|closest-corner|farthest-side|farthest-corner|at|from|in|srgb|oklab|deg|turn|rad|grad|px|em|rem)\b/gi,'');
  if(!alpha.length||alpha.some(a=>!Number.isFinite(a)||a<0||a>1)||/[a-z_]/i.test(rest))return null;
  return {max:Math.max(...alpha)*255,bound_method:'maximum-single-gradient-stop-alpha',stop_count:alpha.length};
 }
 async function backgroundDetails(bg){
  const d={present:Boolean(bg&&bg!=='none'),length:bg.length};if(!d.present)return d;d.sha256=await hashBytes(new TextEncoder().encode(bg));
  const gradient=gradientAlpha(bg);if(gradient){d.type='safe-css-gradient';d.source_kind='single-css-gradient';d.gradient_kind=bg.match(/^[a-z-]+/i)[0];d.alpha=gradient;return d;}
  if(!/^url\(/i.test(bg)){d.type='uninspected-css-image';d.source_kind=/gradient\(/i.test(bg)?'gradient-alpha-unproven':'other-css-image';return d;}
  let uri=bg.slice(bg.indexOf('(')+1,-1).trim();if((uri[0]==='"'||uri[0]==="'")&&uri.at(-1)===uri[0])uri=uri.slice(1,-1);
  if(!/^data:/i.test(uri)){d.type='uninspected-image-uri';d.source_kind='non-data-uri';d.uri_scheme=/^[a-z][a-z0-9+.-]*:/i.exec(uri)?.[0]?.slice(0,-1)||'relative';return d;}
  const comma=uri.indexOf(',');if(comma<0){d.type='invalid-data-uri';return d;}const header=uri.slice(5,comma).split(';'),mime=header[0].toLowerCase();d.data_subtype=/^[a-z0-9.+/-]{1,80}$/.test(mime)?mime:'unrecognized';d.encoding=header.some(x=>x.toLowerCase()==='base64')?'base64':'percent-or-text';d.source_kind='data-uri';d.type='uninspected-data-image';
  if(!['image/png','image/jpeg','image/webp','image/svg+xml'].includes(mime)||bg.length>3000000||typeof Image!=='function')return d;
  try{
   const payload=uri.slice(comma+1);let bytes;
   if(d.encoding==='base64')bytes=Uint8Array.from(atob(payload),c=>c.charCodeAt(0));
   else if(mime==='image/svg+xml')bytes=new TextEncoder().encode(decodeURIComponent(payload));
   else{const values=[];for(let i=0;i<payload.length;i++){if(payload[i]==='%'){need(/^[0-9a-f]{2}$/i.test(payload.slice(i+1,i+3)),'invalid-inline-image-percent-byte');values.push(parseInt(payload.slice(i+1,i+3),16));i+=2;}else{need(payload.charCodeAt(i)<=255,'invalid-inline-image-byte');values.push(payload.charCodeAt(i));}}bytes=new Uint8Array(values);}
   d.tile_sha256=await hashBytes(bytes);
   if(mime==='image/svg+xml'){d.svg_validation=safeSVG(new TextDecoder('utf-8',{fatal:true}).decode(bytes));d.type='safe-static-inline-svg';}else d.type='inline-'+mime.slice(6);
   const im=await new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(Error('inline-image-decode-failed'));image.src=uri;});const w=im.naturalWidth,h=im.naturalHeight;d.width=w;d.height=h;
   if(w>0&&h>0&&w*h<=1000000){const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(im,0,0);const rgba=ctx.getImageData(0,0,w,h).data;let max=0,min=255,nonzero=0,sum=0,opaque=0;for(let i=3;i<rgba.length;i+=4){const a=rgba[i];max=Math.max(max,a);min=Math.min(min,a);sum+=a;if(a)nonzero++;if(a===255)opaque++;}d.alpha={min,max,mean:sum/(w*h),nonzero_fraction:nonzero/(w*h),opaque_fraction:opaque/(w*h)};}
  }catch(e){d.decode_error=String(e.message||e).replace(/[^a-zA-Z0-9_-]/g,'').slice(0,100);}
  return d;
 }

 async function overlayDetails(el){
  const s=getComputedStyle(el);let node=el,path=[];for(let depth=0;node&&depth<12;depth++,node=node.parentElement){const tag=(node.tagName||'').toLowerCase();const peers=node.parentElement?[...node.parentElement.children].filter(x=>x.tagName===node.tagName):[node];path.unshift(tag+':nth-of-type('+(peers.indexOf(node)+1)+')');}
  const d={diagnostic_build:'region-notice-business-cells-v7',selector:path.join(' > '),tag:el.tagName,class:String(el.getAttribute?.('class')||'').slice(0,160),position:s.position||'',pointer_events:s.pointerEvents||'',opacity:s.opacity||'',z_index:s.zIndex||'',background_color:s.backgroundColor||'',background_repeat:s.backgroundRepeat||'',background_size:s.backgroundSize||'',background_position:s.backgroundPosition||'',has_text:Boolean(norm(el.innerText)),children:[...el.children].slice(0,16).map(c=>({tag:c.tagName,has_text:Boolean(norm(c.innerText))}))};
  d.background_image=await backgroundDetails(s.backgroundImage||'');
  return d;
 }
 function decorative(details,el,box,view,selectedBounds){
  const s=getComputedStyle(el),bg=details.background_image,transparent=!s.backgroundColor||s.backgroundColor==='transparent'||/^rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(s.backgroundColor);
  let opacity=1,opacityValid=true;for(let p=el;p;p=p.parentElement){const n=Number(getComputedStyle(p).opacity);if(!Number.isFinite(n)||n<0||n>1){opacityValid=false;break;}opacity*=n;}
  const alpha=bg?.alpha?.max,tab=el.getAttribute?.('tabindex'),role=el.getAttribute?.('role');
  // CSS floating-point roundoff only; not an invented toolbar or visual offset.
  const tolerance=1e-6,covers=selectedBounds.every(r=>r.left>=box.left-tolerance&&r.top>=box.top-tolerance&&r.right<=box.right+tolerance&&r.bottom<=box.bottom+tolerance);
  const conditions={fixed:s.position==='fixed',pointer_events_none:s.pointerEvents==='none',transparent_background:Boolean(transparent),empty_leaf:el.children.length===0&&!norm(el.innerText),not_interactive:(tab==null||/^-\d+$/.test(tab)&&Number(tab)<0)&&!['button','link','textbox','checkbox','radio','combobox','menuitem','tab'].includes(role)&&el!==document.activeElement,contains_selected_region:covers,repeat_background:['repeat','repeat repeat'].includes(norm(s.backgroundRepeat)),supported_static_background:['inline-png','inline-webp','inline-jpeg','safe-static-inline-svg','safe-css-gradient'].includes(bg?.type),alpha_measured:Number.isFinite(alpha),ancestor_opacity_valid:opacityValid,low_effective_alpha:Number.isFinite(alpha)&&alpha>=0&&opacityValid&&alpha/255*opacity<=0.2};
  details.decoration_conditions=conditions;details.decoration_geometry={box,view,selected_bounds:selectedBounds,tolerance_css_pixels:tolerance};details.tabindex=tab??null;details.ancestor_opacity=opacityValid?opacity:null;
  if(Object.values(conditions).every(Boolean))return {...details,classification:'noninteractive-translucent-repeating-static-decoration',effective_alpha_max:alpha/255*opacity,approved_alpha_limit:0.2,original_pixels_preserved:true};
  return null;
 }
 const BUSINESS='notice-five-business-cells-v1',MANUAL='notice-five-business-cells-v2',LOCAL='manual-local-business-preview-v2';
 function manualDateFragment(base){
  const d=base.business_date,g=d?.geometry,c=g?.text_clips;
  return base.preview_contract===MANUAL&&g.rendered===true&&g.box_viewport_contained===true&&g.unsupported_css_absent===true&&g.text_unclipped===false&&g.evidence_eligible===false&&Array.isArray(c)&&c.length===1&&c[0].selector===d.selector&&c[0].supported===false&&c[0].text_overflow==='clip'&&c[0].line_clamp==='none'&&c[0].overflow_x==='clip'&&c[0].overflow_y==='clip'&&['client_width','client_height','scroll_width','scroll_height'].every(k=>Number.isFinite(c[0][k])&&c[0][k]>0)&&c[0].scroll_width>c[0].client_width&&c[0].scroll_height===c[0].client_height;
 }
 function businessAllowed(base){
  need(base.evidence_contract===BUSINESS&&base.business_headers?.length===5&&Array.isArray(base.business_cells),'region-business-contract-invalid');
  if(base.preview_contract===MANUAL)return [...[base.business_date,...base.business_headers].filter(a=>a.geometry.evidence_eligible||a===base.business_date&&manualDateFragment(base)).map(a=>a.selector),...(base.manual_local_previews||[]).flatMap(p=>{need(p.contract===LOCAL&&p.quality_review_required===true&&p.coverage_certified===false&&p.cells.length===5,'region-manual-contract-invalid');return p.cells.map(c=>c.selector);})];
  const partial=(base.partial_cell_previews||[]).flatMap(p=>{need(p.contract==='partial-cell-original-clip-preview-v1'&&p.quality_review_required===true&&p.original_full_flags_unchanged===true&&p.cells.length===5,'region-partial-preview-invalid');return p.cells.map(c=>c.selector);});return [...new Set([...partial,...[base.business_date,...base.business_headers,...base.business_cells.flatMap(r=>r.cells)].filter(e=>e.geometry.evidence_eligible).map(e=>e.selector)])];
 }
 function businessCoverage(base,selectors){
  if(base.preview_contract===MANUAL){
   const notice_ids=[],cell_text_completeness={};
   for(const row of base.business_cells){const selected=row.cells.map(c=>selectors.includes(c.selector));if(selected.some(Boolean)){need(selected.every(Boolean)&&(base.manual_local_previews||[]).some(p=>p.notice_id===row.notice_id),'region-manual-five-cells-required');notice_ids.push(row.notice_id);cell_text_completeness[row.notice_id]=row.cells.map(c=>({field:c.field,text_complete_in_image:false}));}}
   const anchors=[base.business_date,...base.business_headers],as=anchors.map(a=>a.selector),anchor=JSON.stringify(selectors)===JSON.stringify(as);
   need(anchor?!notice_ids.length&&(base.business_date.geometry.evidence_eligible||manualDateFragment(base))&&base.business_headers.every(a=>a.geometry.evidence_eligible):notice_ids.length>0&&selectors.length===notice_ids.length*5&&!selectors.some(s=>as.includes(s)),'region-manual-anchor-or-rows-exclusive');
   const fragment=anchor&&manualDateFragment(base);return {contract:BUSINESS,capture_subcontract:LOCAL,notice_ids,date_filter_visible:anchor&&!fragment,list_headers_visible:anchor,cell_text_completeness,coverage_certified:false,...(fragment?{date_visible_fragment_in_image:true,date_text_complete_in_image:false,date_fragment_source_value:base.business_date.text}:{})};
  }
  const notice_ids=[],cell_text_completeness={},partial_cell_original_clips=[];
  for(const row of base.business_cells){const selected=row.cells.map(c=>selectors.includes(c.selector));
   if(selected.some(Boolean)){const partial=(base.partial_cell_previews||[]).find(p=>p.notice_id===row.notice_id);need(row.cells.length===5&&selected.every(Boolean)&&row.cells.every((c,i)=>c.index===i&&(c.geometry.evidence_eligible||partial?.cells[i]?.selector===c.selector)),'region-business-partial-five-cells');notice_ids.push(row.notice_id);cell_text_completeness[row.notice_id]=row.cells.map(c=>({field:c.field,text_complete_in_image:partial?false:c.geometry.text_unclipped}));if(partial)partial_cell_original_clips.push(partial);}
  }
  return {contract:BUSINESS,...(partial_cell_original_clips.length?{capture_subcontract:'partial-cell-original-clip-preview-v1',partial_cell_original_clips}:{}),notice_ids,date_filter_visible:selectors.includes(base.business_date.selector)&&base.business_date.geometry.evidence_eligible,list_headers_visible:base.business_headers.every(h=>selectors.includes(h.selector)&&h.geometry.evidence_eligible),cell_text_completeness};
 }
 function singlePhysicalBorder(style,side){
  const value=style['border'+side+'Width'],dpr=devicePixelRatio;
  if(style['border'+side+'Style']!=='solid'||style['border'+side+'Color']!=='rgba(0, 24, 61, 0.08)'||typeof value!=='string'||!/^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?px$/.test(value)||!Number.isFinite(dpr)||dpr<.25||dpr>16)return false;
  const width=Number.parseFloat(value),physical=width*dpr,tolerance=.5e-6*dpr+1e-12;return width>0&&width<=4&&Math.abs(physical-1)<=tolerance;
 }
 function foreignEffectsAbsent(el,allowShadow=false,adjacentBorderSide=null){
  const s=getComputedStyle(el);
  if(!allowShadow&&s.boxShadow!=='none'||s.textShadow!=='none'||!(s.outlineStyle==='none'||s.outlineWidth==='0px')||s.filter!=='none'||s.backdropFilter!=='none')return false;
  for(const side of ['Top','Right','Bottom','Left'])if(!(s['border'+side+'Style']==='none'||s['border'+side+'Width']==='0px')){if(side===adjacentBorderSide&&singlePhysicalBorder(s,side))continue;return false;}
  for(const pseudo of ['::before','::after']){const p=getComputedStyle(el,pseudo);if(!['none','normal'].includes(p.content)&&p.display!=='none'&&p.visibility!=='hidden'&&Number(p.opacity)!==0)return false;}
  return true;
 }
 function foreignEffectDiagnostic(el){
  const s=getComputedStyle(el),safe=value=>String(value||'').replace(/url\([^)]*\)/gi,'url(<uri-omitted>)').slice(0,240);let node=el,path=[];
  for(let depth=0;node&&depth<12;depth++,node=node.parentElement){const tag=(node.tagName||'').toLowerCase(),peers=node.parentElement?[...node.parentElement.children].filter(x=>x.tagName===node.tagName):[node];path.unshift(tag+':nth-of-type('+(peers.indexOf(node)+1)+')');}
  const borders={};for(const side of ['Top','Right','Bottom','Left'])borders[side.toLowerCase()]={style:safe(s['border'+side+'Style']),width:safe(s['border'+side+'Width']),color:safe(s['border'+side+'Color'])};
  const pseudo={};for(const kind of ['::before','::after']){const p=getComputedStyle(el,kind);pseudo[kind]={has_generated_content:!['none','normal'].includes(p.content),display:safe(p.display),visibility:safe(p.visibility),opacity:safe(p.opacity)};}
  const r=el.getBoundingClientRect();return {diagnostic_build:'region-notice-business-cells-v7',purpose:'readonly-foreign-CSS-effect-diagnostic-only',selector:path.join(' > '),selector_depth_truncated:Boolean(node),tag:el.tagName,class:safe(el.getAttribute?.('class')),position:safe(s.position),pointer_events:safe(s.pointerEvents),opacity:safe(s.opacity),z_index:safe(s.zIndex),has_text:Boolean(norm(el.innerText)),background_color:safe(s.backgroundColor),has_background_image:Boolean(s.backgroundImage&&s.backgroundImage!=='none'),effects:{box_shadow:safe(s.boxShadow),text_shadow:safe(s.textShadow),outline_style:safe(s.outlineStyle),outline_width:safe(s.outlineWidth),filter:safe(s.filter),backdrop_filter:safe(s.backdropFilter),borders,pseudo},bounds:{left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height},coordinate_space:'CSS-viewport-diagnostic-only',pixel_coordinates_returned:true,pixel_input_actions:false};
 }
 function tableEdgeShadow(el,elements){
  const cls=n=>String(n?.getAttribute?.('class')||'').trim().split(/\s+/).sort().join(' '),exact=(n,names)=>n?.tagName==='DIV'&&cls(n)===names.split(' ').sort().join(' ');
  if(!exact(el,'governance_merchant-Table-ColumnShadow governance_merchant-Table-ColumnShadow_end')||el.children.length||norm(el.innerText))return null;
  const parent=el.parentElement,container=parent?.parentElement,frame=container?.parentElement;
  if(!(['governance_merchant-Table-Shadow_head','governance_merchant-Table-Shadow_sticky'].some(kind=>exact(parent,'governance_merchant-Table-Shadow '+kind)))||!exact(container,'governance_merchant-Table-Container governance_merchant-Table-Container_scrollable')||!exact(frame,'governance_merchant-Table-Frame'))return null;
  const tables=[...container.querySelectorAll('table')].filter(n=>n.tagName==='TABLE'&&cls(n)==='governance_merchant-Table-Implement');if(tables.length!==1||!elements.some(e=>tables[0].contains(e)))return null;
  const s=getComputedStyle(el),role=el.getAttribute('role'),tab=el.getAttribute('tabindex');
  if(s.position!=='sticky'||s.pointerEvents!=='none'||s.opacity!=='1'||s.zIndex!=='auto'||s.backgroundImage!=='none'||!/^rgba\(0,\s*0,\s*0,\s*0\)$/.test(s.backgroundColor)||!foreignEffectsAbsent(el,true)||el===document.activeElement||role!==null&&role!==undefined||tab!==null&&tab!==undefined)return null;
  const known='rgba(16, 17, 20, 0.08) -12px 0px 12px -12px, rgba(16, 17, 20, 0.04) -4px 0px 4px -4px, rgba(16, 17, 20, 0.08) -1px 0px 1px -1px';if(norm(s.boxShadow)!==known)return null;
  let opacity=1;for(let n=el;n;n=n.parentElement){const a=Number(getComputedStyle(n).opacity);if(!Number.isFinite(a)||a<0||a>1)return null;opacity*=a;}
  const upper=1-(1-.08)*(1-.04)*(1-.08);return {classification:'noninteractive-translucent-table-edge-shadow',structure:'governance-table-column-shadow-end-v1',class:el.getAttribute('class'),parent_class:parent.getAttribute('class'),container_class:container.getAttribute('class'),frame_class:frame.getAttribute('class'),box_shadow:s.boxShadow,layer_alphas:[.08,.04,.08],composited_alpha_upper_bound:upper,effective_alpha_upper_bound:upper*opacity,ancestor_opacity:opacity,approved_alpha_limit:.2,original_pixels_preserved:true,visual_review_required:true,foreign_css_effects_absent_except_known_shadow:true};
 }
 function noPaintProof(el){
  const all=[el,...el.querySelectorAll('*')];if(all.length>64)return null;
  const transparent=c=>c==='transparent'||/^rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(c||'');
  for(const n of all){
   const s=getComputedStyle(n),tag=n.tagName,role=n.getAttribute?.('role'),tab=n.getAttribute?.('tabindex');
   if(['IMG','SVG','CANVAS','VIDEO','IFRAME','OBJECT','EMBED','PICTURE','INPUT','TEXTAREA','SELECT','BUTTON'].includes(tag)||tag==='A'&&n.getAttribute('href')||tab!==null&&tab!==undefined&&(!/^-\d+$/.test(tab)||Number(tab)>=0)||['button','link','textbox','checkbox','radio','combobox','menuitem','tab'].includes(role)||n===document.activeElement)return null;
   if(norm(n.innerText)||!transparent(s.backgroundColor)||s.backgroundImage!=='none'||!foreignEffectsAbsent(n))return null;
   for(const side of ['Top','Right','Bottom','Left'])if(!(s['border'+side+'Style']==='none'||s['border'+side+'Width']==='0px'))return null;
   for(const pseudo of ['::before','::after']){const p=getComputedStyle(n,pseudo);if(!['none','normal'].includes(p.content)&&p.display!=='none'&&p.visibility!=='hidden'&&Number(p.opacity)!==0)return null;}
  }
  return {classification:'public-CSS-no-painted-content',checked_nodes:all.length,background_absent:true,borders_absent:true,shadows_absent:true,pseudo_absent:true,text_absent:true,images_absent:true,interactive_absent:true};
 }

 // Source-neighbor paint is NOT certified absent: retain its true geometry
 // only in a mandatory local preview. No epsilon or extra notice coverage.
 function sourceNeighborOverlap(el,elements,bounds,base,one){
  if(base.preview_contract!==MANUAL||!['TR','TD'].includes(el.tagName))return null;
  const rows=base.business_cells,row=el.tagName==='TR'?el:el.parentElement,index=rows.findIndex(r=>one({by:'selector',value:r.tr_selector})===row);
  if(index<0)return null;const source=rows[index],body=row.parentElement,table=body?.parentElement;
  const cl=n=>String(n?.getAttribute?.('class')||''),attr=(n,k)=>n?.getAttribute?.(k);
  const valid=n=>n?.tagName==='TR'&&cl(n)==='governance_merchant-Table-Row'&&attr(n,'role')==='row'&&n.children.length===10&&[...n.children].every(c=>c.tagName==='TD'&&attr(c,'role')==='cell');
  if(!valid(row)||!source.cells.every((c,i)=>one({by:'selector',value:c.selector})===row.children[i])||body?.tagName!=='TBODY'||cl(body)!=='governance_merchant-Table-Body'||attr(body,'role')!=='rowgroup'||table?.tagName!=='TABLE'||cl(table)!=='governance_merchant-Table-Implement'||attr(table,'role')!=='table')return null;
  if(el!==row&&!source.cells.some((c,i)=>i<5&&one({by:'selector',value:c.selector})===el&&row.children[i]===el))return null;
  for(let n=el;n;n=n.parentElement){const s=getComputedStyle(n);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)!==1||s.transform&&s.transform!=='none'||s.zoom&&s.zoom!=='1'||typeof n.getAnimations==='function'&&n.getAnimations().some(a=>a.pending||a.playState==='running'))return null;}
  if(getComputedStyle(row).position!=='static'||getComputedStyle(el).position!=='static'||el===document.activeElement)return null;
  const rr=rect(row),r=rect(el);if(!inside(r,rr))return null;const matches=[],siblings=[...body.children];
  for(let k=0;k<elements.length;k++){
   const b=bounds[k];if(!intersects(b,r))continue;const cell=elements[k],target=cell.parentElement,j=rows.findIndex(x=>one({by:'selector',value:x.tr_selector})===target);
   if(j<0||Math.abs(j-index)!==1||!valid(target)||target.parentElement!==body||![...target.children].slice(0,5).includes(cell)||!rows[j].cells.every((c,i)=>one({by:'selector',value:c.selector})===target.children[i]&&elements.includes(target.children[i])))return null;
   const a=siblings.indexOf(row),z=siblings.indexOf(target);if(Math.abs(a-z)!==1||Math.sign(a-z)!==Math.sign(index-j))return null;
   const t=rect(target),above=index<j;
   if(above?!(rr.top<t.top&&rr.bottom>t.top&&rr.bottom<t.bottom&&b.top===t.top):!(rr.top>t.top&&rr.top<t.bottom&&rr.bottom>t.bottom&&b.bottom===t.bottom))return null;
   matches.push({selected_notice_id:rows[j].notice_id,selected_row:rows[j].tr_selector,selected_source_index:j,foreign_source_index:index,selected_dom_row_index:z,foreign_dom_row_index:a,direction:above?'preceding-row-bottom':'following-row-top',selected_raw_row_rect:t,selected_visible_cell_rect:b});
  }
  if(!matches.length)return null;
  return {contract:'unresolved-source-neighbor-overlap-v1',source_sha256:base.source_sha256,foreign_notice_id:source.notice_id,foreign_row:source.tr_selector,foreign_selector:el===row?source.tr_selector:source.cells.find(c=>one({by:'selector',value:c.selector})===el).selector,tag:el.tagName,table_selector:source.tr_selector.slice(0,source.tr_selector.lastIndexOf(' > tbody')),tbody_selector:source.tr_selector.slice(0,source.tr_selector.lastIndexOf(' > tr')),foreign_rect:r,foreign_row_rect:rr,matches,paint_status:'unresolved-source-row-paint',original_pixels_preserved:true,visual_review_required:true,coverage_added:false};
 }
 // A float seam is not an occluder only for two actual immediate sibling
 // governance table rows. Raw region/crop coordinates are never rounded.
 const TABLE_SEAM_LIMIT=2**-15;
 function adjacentTableSeam(el,elements,bounds,base,one){
  if(!['TR','TD'].includes(el.tagName))return null;
  const row=el.tagName==='TR'?el:el.parentElement;
  const rows=base.business_cells||[],index=rows.findIndex(r=>one({by:'selector',value:r.tr_selector})===row);
  if(index<0)return null;
  const tbody=row?.parentElement,table=tbody?.parentElement;
  const attr=(n,k)=>n?.getAttribute?.(k),cl=n=>String(attr(n,'class')||'').trim();
  const validRow=n=>n?.tagName==='TR'&&attr(n,'role')==='row'&&cl(n)==='governance_merchant-Table-Row'&&n.children.length===10&&[...n.children].every((c,i)=>c.tagName==='TD'&&attr(c,'role')==='cell'&&cl(c)===('governance_merchant-Table-Cell'+(i===0?' governance_merchant-Table-Cell_noneStickyFirst':i===4?' governance_merchant-Table-Cell_maxLines_3':i===9?' governance_merchant-Table-Cell_sticky governance_merchant-Table-Cell_stickyEnd':'')));
  if(!validRow(row)||tbody?.tagName!=='TBODY'||attr(tbody,'role')!=='rowgroup'||cl(tbody)!=='governance_merchant-Table-Body'||table?.tagName!=='TABLE'||attr(table,'role')!=='table'||cl(table)!=='governance_merchant-Table-Implement'||(el!==row&&![...row.children].slice(0,5).includes(el)))return null;
  for(let n=el;n;n=n.parentElement){const css=getComputedStyle(n);if(css.display==='none'||css.visibility==='hidden'||css.visibility==='collapse'||Number(css.opacity)!==1||css.transform&&css.transform!=='none'||css.zoom&&css.zoom!=='1'||css.clipPath&&css.clipPath!=='none'||css.maskImage&&css.maskImage!=='none'||css.webkitMaskImage&&css.webkitMaskImage!=='none'||typeof n.getAnimations==='function'&&n.getAnimations().some(a=>a.pending||a.playState==='running'))return null;}
  const st=getComputedStyle(el),rs=getComputedStyle(row);
  if(!['static','relative'].includes(st.position)||!['static','relative'].includes(rs.position)||!foreignEffectsAbsent(row)||el===document.activeElement)return null;
  const r=rect(el),rr=rect(row);if(!inside(r,rr))return null;
  const matches=[];
  for(let k=0;k<elements.length;k++){
   const b=bounds[k];if(!intersects(b,r))continue;
   const cell=elements[k],other=cell.parentElement,j=rows.findIndex(x=>one({by:'selector',value:x.tr_selector})===other);
   if(j<0||Math.abs(j-index)!==1||!validRow(other)||other.parentElement!==tbody||![...other.children].slice(0,5).includes(cell))return null;
   const siblings=[...tbody.children],a=siblings.indexOf(row),z=siblings.indexOf(other);if(Math.abs(a-z)!==1||Math.sign(a-z)!==Math.sign(index-j))return null;
   const o=rect(other);if(!inside(b,o))return null;
   const above=index<j,depth=above?r.bottom-b.top:b.bottom-r.top,rowDepth=above?rr.bottom-o.top:o.bottom-rr.top;
   if(!(depth>0&&depth<=TABLE_SEAM_LIMIT&&rowDepth>0&&rowDepth<=TABLE_SEAM_LIMIT))return null;
   if(above?(r.bottom!==rr.bottom||b.top!==o.top):(r.top!==rr.top||b.bottom!==o.bottom))return null;
   matches.push({selected_notice_id:rows[j].notice_id,selected_row:rows[j].tr_selector,direction:above?'preceding-row-bottom':'following-row-top',overlap_css_px:depth,row_overlap_css_px:rowDepth});
  }
  if(!matches.length)return null;
  let preservedBorder=null;
  if(!foreignEffectsAbsent(el)){
   // Only the observed same-table TD's border facing the proved float seam.
   // This is real paint retained in the PNG, never a no-paint exception.
   const directions=new Set(matches.map(m=>m.direction));if(el.tagName!=='TD'||directions.size!==1)return null;
   const side=matches[0].direction==='preceding-row-bottom'?'Bottom':'Top',width=Number.parseFloat(st['border'+side+'Width']),physical=width*devicePixelRatio;
   if(!foreignEffectsAbsent(el,false,side)||!singlePhysicalBorder(st,side))return null;
   const borders={};for(const name of ['Top','Right','Bottom','Left'])borders[name.toLowerCase()]={style:st['border'+name+'Style'],width:st['border'+name+'Width'],color:st['border'+name+'Color']};
   preservedBorder={classification:'observed-adjacent-TD-single-physical-pixel-border-v1',side:side.toLowerCase(),borders,device_pixel_ratio:devicePixelRatio,physical_width:physical,maximum_physical_rounding_error:.5e-6*devicePixelRatio+1e-12,css_serialization_decimal_places:6,original_pixels_preserved:true,visual_review_required:true};
  }
  return {classification:'verified-adjacent-table-float-seam-v1',foreign_notice_id:rows[index].notice_id,foreign_row:rows[index].tr_selector,foreign_selector:el===row?rows[index].tr_selector:rows[index].cells[[...row.children].indexOf(el)].selector,tag:el.tagName,tolerance_css_px:TABLE_SEAM_LIMIT,original_pixels_preserved:true,matches,...(preservedBorder?{preserved_border:preservedBorder}:{})};
 }
 async function proof(c,one,readTree){
  need(Object.keys(c).sort().join(',')==='base,channel,groupid,op,purpose,selectors,tabId,windowId','region-command-fields-invalid');
  need(c.op==='dom-region-proof'&&c.purpose==='evidence-crop-only'&&Array.isArray(c.selectors)&&c.selectors.length>0&&c.selectors.length<=100&&new Set(c.selectors).size===c.selectors.length,'region-explicit-crop-only-required');
  const base={...c.base,channel:c.channel};need(['review-viewport-proof','viewport-proof'].includes(base.op)&&['tabId','windowId','groupid'].every(k=>base[k]===c[k]),'region-base-scope-mismatch');
  const api=base.op==='review-viewport-proof'?globalThis.__localReviewProof:globalThis.__localViewportProof;need(api,'region-base-proof-unavailable');
  const result=await api.proof(base,one,readTree),view={left:0,top:0,right:document.documentElement.clientWidth,bottom:document.documentElement.clientHeight};
  const business=result.evidence_contract===BUSINESS,manual=business&&result.preview_contract===MANUAL;
  const allowed=business?businessAllowed(result):base.op==='review-viewport-proof'?result.reviews.filter(r=>r.card_visible).map(r=>r.card):result.elements.filter(e=>e.fully_visible&&e.locator.by==='selector').map(e=>e.locator.value);
  need(c.selectors.every(s=>typeof s==='string'&&allowed.includes(s)),'region-selector-not-verified-by-base');
  if(base.op==='review-viewport-proof')need(c.selectors.length===1,'region-one-review-card-required');
  const elements=c.selectors.map(s=>one({by:'selector',value:s}));elements.forEach(stableVisible);const rawBounds=elements.map(rect),partialCells=business?(manual?result.manual_local_previews||[]:result.partial_cell_previews||[]).flatMap(p=>p.cells):[],bounds=rawBounds.map((r,i)=>{const p=partialCells.find(p=>p.selector===c.selectors[i]);if(!p)return r;need(JSON.stringify(r)===JSON.stringify(p.raw_box),'region-partial-raw-box-changed');return p.visible_box;});
  const region={left:Math.min(...bounds.map(r=>r.left)),top:Math.min(...bounds.map(r=>r.top)),right:Math.max(...bounds.map(r=>r.right)),bottom:Math.max(...bounds.map(r=>r.bottom))};region.width=region.right-region.left;region.height=region.bottom-region.top;need(inside(region,view),'region-outside-css-viewport');
  let action=null;
  if(base.op==='review-viewport-proof'){
   const actions=[...elements[0].querySelectorAll('.button-vhqEd7')].filter(e=>{const text=norm(e.innerText),cl=e.getAttribute('class');return cl==='button-vhqEd7'?text==='投诉':String(cl||'').split(/\s+/).includes('isHighlight-DoxxP4')&&['投诉','查看投诉结果','投诉审核中'].includes(text);});need(actions.length===1&&['投诉','查看投诉结果','投诉审核中'].includes(norm(actions[0].innerText)),'region-review-action-not-unique');stableVisible(actions[0]);need(inside(rect(actions[0]),region),'region-review-action-outside-card');action=norm(actions[0].innerText);
   for(const other of document.querySelectorAll('.commentItem-jrXo5p'))if(other!==elements[0]){const r=other.getBoundingClientRect();need(!finiteRect(r)||!intersects(region,r),'region-other-review-overlap');}
  }
  const preserved=[],unresolved=[],unpainted=[],tableShadows=[],tableSeams=[],sourceNeighbors=[],zeroSuppressed=[];
  for(const el of document.querySelectorAll('*')){
   if(elements.some(e=>el===e||e.contains(el)||el.contains(e)))continue;
   const r=el.getBoundingClientRect();if(!finiteRect(r)||!bounds.some(b=>intersects(b,r)))continue;
   if(!business){const zero=zeroOpacityAncestor(el);if(zero){zeroSuppressed.push({el,chain:zero});continue;}}
   if(business){const neighbor=manual?sourceNeighborOverlap(el,elements,bounds,result,one):null;if(neighbor){need(sourceNeighbors.length<50,'region-source-neighbor-limit');sourceNeighbors.push(neighbor);continue;}const seam=adjacentTableSeam(el,elements,bounds,result,one);if(seam){need(tableSeams.length<50,'region-table-seam-limit');tableSeams.push(seam);continue;}const s=getComputedStyle(el);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0)continue;const noPaint=noPaintProof(el);if(noPaint){need(unpainted.length<100,'region-unpainted-diagnostic-limit');unpainted.push({tag:el.tagName,class:String(el.getAttribute?.('class')||'').slice(0,160),...noPaint});continue;}need(!['BUTTON','INPUT','TEXTAREA','SELECT','SUMMARY'].includes(el.tagName)&&!(el.tagName==='A'&&el.getAttribute('href'))&&!(Number.isInteger(el.tabIndex)&&el.tabIndex>=0)&&!['button','link','textbox','checkbox','radio','combobox','menuitem','tab'].includes(el.getAttribute?.('role')),'region-business-interactive-overlap');if(manual&&!String(el.innerText||'').trim()&&!['IMG','SVG','IFRAME','CANVAS','VIDEO'].includes(el.tagName)){need(unresolved.length<100,'region-manual-overlay-limit');unresolved.push({classification:'unresolved-empty-public-decoration',tag:el.tagName,visual_review_required:true});continue;}if(!foreignEffectsAbsent(el)){const shadow=tableEdgeShadow(el,elements);if(shadow){need(tableShadows.length<4,'region-table-shadow-limit');tableShadows.push(shadow);continue;}need(false,'region-business-foreign-effect-overlap:'+JSON.stringify(foreignEffectDiagnostic(el)));}}else if(!painted(el))continue;
   // For table unions, verified selected descendants are permitted, unrelated
   // painted content in the crop is not silently accepted.
   const details=await overlayDetails(el),decoration=decorative(details,el,r,view,bounds);if(decoration){preserved.push(decoration);continue;}
   const conditions=details.decoration_conditions;const external=details.background_image?.source_kind==='non-data-uri'&&['https','http'].includes(details.background_image?.uri_scheme);
   if(external&&Object.entries(conditions).every(([k,v])=>['supported_static_background','alpha_measured','low_effective_alpha'].includes(k)||v===true)){unresolved.push({...details,classification:'unmeasured-presented-static-background',visual_review_required:true});continue;}
   need(false,'region-painted-external-overlap:'+JSON.stringify(details));
  }
  const after=await api.proof(base,one,readTree);for(const entry of zeroSuppressed)need(sameZeroOpacityAncestor(entry.el,entry.chain),'region-transparent-ancestor-changed');need(JSON.stringify(result)===JSON.stringify(after)&&JSON.stringify(rawBounds)===JSON.stringify(elements.map(rect)),'region-dom-or-geometry-changed');
  const coverage=business?businessCoverage(result,c.selectors):null,fragment=business&&Object.values(coverage.cell_text_completeness).some(fields=>fields.some(f=>!f.text_complete_in_image));
  return {source:'local-dom-bridge',method:'public-DOM-evidence-region-proof',geometry_purpose:'evidence-crop-only',pixel_input_actions:false,scope:result.scope,url:result.url,base_proof:result,selectors:c.selectors,region,viewport:{width:view.right,height:view.bottom,device_pixel_ratio:devicePixelRatio,visual_scale:visualViewport?.scale??1},review_action:action,external_painted_overlap:unresolved.length||sourceNeighbors.length?'unresolved':false,unresolved_overlay:unresolved,...(manual?{manual_preview_unresolved:true,...(sourceNeighbors.length?{unresolved_source_neighbor_overlap:sourceNeighbors}:{})}:{}),quality_review_required:manual||unresolved.length>0||tableShadows.length>0||tableSeams.some(s=>s.preserved_border)||Boolean(fragment),occlusion_verified:false,...(business?{evidence_contract:BUSINESS,derived_business_coverage:coverage,unpainted_elements:unpainted,preserved_table_shadows:tableShadows,adjacent_table_seams:tableSeams,paint_audit:{contract:'public-DOM-business-paint-audit-v1',unpainted_count:unpainted.length,preserved_count:preserved.length+tableShadows.length,unresolved_count:unresolved.length,roundoff_count:tableSeams.length,...(sourceNeighbors.length?{source_neighbor_unresolved_count:sourceNeighbors.length}:{})}}:{}),preserved_translucent_backgrounds:preserved,region_build:manual?BUILD:'region-notice-business-cells-v7'};
 }
 globalThis.__localRegionProof={proof,build:BUILD,paintVisibilityRevision:PAINT_REVISION};
})();
