"""Actual057 semantic/geometry binding; synthetic renderer transport, no UI."""
import sys,json,copy,unittest,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
import business_cells_capture as b
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class OwnOverflow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=ROOT/'work/live-acceptance/violations/business-text-geometry-diagnostic-v10/actual-original-base-diagnostic-cli.json';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='f313de218db1d38e82ecaf76fe2750a09184c4fc63e4a7d35b570c36fcb63f73';a=json.loads(raw);cls.diag=json.loads(json.loads(a['stdout'])['error'].split('business-text-geometry-unreviewed:')[1]);cls.obs=json.loads((BASE/'.records-region-navigation/7bb6a631114b5351e9d54b7370e2af2a8d4a38e63676a74c98fabee0a4118d2d/evidence/0036.json').read_text());cls.nodes=list(b.gp.walk(cls.obs['tree']['root']));cls.tr=next(n for n in cls.nodes if n.get('tag')=='tr' and 'ZS202610164743539487' in n.get('name',''))
 def setup_case(self):
  cells=[{'index':i,'field':b.FIELDS[i],'selector':n['selector'],'text_selectors':[x['selector'] for x in b.gp.walk(n) if x.get('name')]} for i,n in enumerate(self.tr['children'][:5])];row={'notice_id':'ZS202610164743539487','tr_selector':self.tr['selector'],'cells':copy.deepcopy(cells)};spec={'rows':[{'notice_id':row['notice_id'],'tr_selector':row['tr_selector'],'cells':cells}]}
  boxes=[]
  for i,(left,width) in enumerate(zip([288.66668701171875,558.6666870117188,818.6666870117188,1138.6666870117188,1318.6666870117188],[270,260,320,180,330])):boxes.append({'left':left,'top':806.90625,'right':left+width,'bottom':932.90625,'width':width,'height':126})
  union={'left':boxes[0]['left'],'right':boxes[-1]['right'],'top':806.90625,'bottom':932.90625,'width':1360.,'height':126}
  # Exact operations derive all five selectors/order from the immutable source.
  union['width']=union['right']-union['left'];d=copy.deepcopy(self.diag);d['build']='viewport-notice-business-cells-v11-manual-own-text-overflow-v2';item={'classification':'source-own-horizontal-text-overflow-v1','notice_id':row['notice_id'],'tr_selector':row['tr_selector'],'union_box':union,'diagnostic':d,'original_rejection':'business-text-geometry-unreviewed','quality_review_required':True,'text_complete_in_image':False,'coverage_certified':False}
  for c in row['cells']:c['geometry']={}
  row['cells'][2]['geometry']={'unresolved_own_text_overflow':[item]};base={'diagnostic_build':d['build'],'business_cells':[row],'manual_preview_viewport':{'width':1920,'height':1017}};previews={row['notice_id']:{'cells':[{'raw_box':box} for box in boxes]}};return base,spec,previews
 def test_real_js_geometry_is_consumed_by_python_and_legacy_rejects_extra_contract(self):
  script="const fs=require('fs'),vm=require('vm');const p="+json.dumps(str(ROOT/'skills/chrome-dom-export/tests/manual-own-text-overflow.test.cjs'))+";const code=fs.readFileSync(p,'utf8').split(\"\\ntest('actual057\")[0];const c={require,__dirname:require('path').dirname(p),console};vm.createContext(c);vm.runInContext(code+';globalThis.result=setup().manual();',c);process.stdout.write(JSON.stringify(c.result));"
  g=json.loads(subprocess.check_output(['/Users/feibing/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node','-e',script]));selectors=['#cell-under-test','#node-under-test'];b.validate_geometry(g,allow_ellipsis=True,selectors=selectors,manual=True)
  with self.assertRaises(ValueError):b.validate_geometry(g,allow_ellipsis=True,selectors=selectors)
  forged=copy.deepcopy(g);forged['text_unclipped']=True
  with self.assertRaises(ValueError):b.validate_geometry(forged,allow_ellipsis=True,selectors=selectors,manual=True)
 def test_actual_source_descendant_and_union_bind_with_explicit_quality_ack(self):
  base,spec,p=self.setup_case();b.validate_own_text_overflows(base,spec,p);item=base['business_cells'][0]['cells'][2]['geometry']['unresolved_own_text_overflow'][0];self.assertIn(item['diagnostic']['node']['selector'],spec['rows'][0]['cells'][2]['text_selectors']);facts={'capture_subcontract':b.LOCAL,'unresolved_own_text_overflow':[item],'cell_text_completeness':{}};self.assertTrue(b.expected_visibility('rows',facts)['source_own_horizontal_text_overflow_acknowledged'])
 def test_wrong_source_view_cross_row_union_and_false_certification_refuse(self):
  for mode in ('source','union','vertical','view','certified','node','build','ancestor'):
   base,spec,p=self.setup_case();item=base['business_cells'][0]['cells'][2]['geometry']['unresolved_own_text_overflow'][0];d=item['diagnostic']
   if mode=='source':item['notice_id']='foreign'
   elif mode=='union':item['union_box']['right']+=1
   elif mode=='vertical':d['text_rect']['bottom']=933
   elif mode=='view':d['text_rect']['right']=2000
   elif mode=='certified':item['coverage_certified']=True
   elif mode=='node':d['node']['selector']='#foreign'
   elif mode=='build':base['diagnostic_build']='old'
   else:item['original_rejection']='business-text-ancestor-clip-unreviewed';d['failed_conditions']={'ancestor_clip_x':True,'ancestor_clip_y':False};d['ancestor']={'selector':'#foreign'}
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.validate_own_text_overflows(base,spec,p)
if __name__=='__main__':unittest.main()
