import sys,json,copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import normal_paging as p

def node(tag='div',cl='',name='',children=None,selector=None):
 return {'tag':tag,'attributes':{'class':cl},'name':name,'selector':selector or '#'+cl+name,'children':children or [],'disabled':False}
def pg(index,total=54):
 pages=(total+9)//10
 def button(disabled,label):return node(cl='button-j4VxiA'+(' isDisabled-unTBS6' if disabled else ''),selector='#'+label,children=[{**node('svg','icon-v6i0WU',children=[node('g',children=[node('path')])]),'role':'presentation'}])
 return node(cl='pagination-GXvAPk',children=[node(cl='text-bjyZFG',name=f'共{total}条记录'),node(cl='buttonGroup-GDbp9Y',children=[button(index==1,'previous'),node(cl='text-bjyZFG',name=f'{index}/{pages}'),button(index==pages,'next')])])
class ContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();source=self.root/'source.xlsx';source.write_bytes(b'synthetic source bytes; load_export parser separately tested')
  self.job={'company':'公司','groupid':'123','identity':{'provider':'服务商1','account_id':'2','manager':'经理'},'account_verified':True,'start':'2026-09-21','end_exclusive':'2026-10-21','source_work_order_id':'original-month'}
  receipt={'company':'公司','groupid':'123','identity':self.job['identity'],'identity_before':self.job['identity'],'account_verified':True,'download_verified':True,'source_is_authoritative_export':True,'work_order_id':'original-month','date_range':{'start':'2026-09-21','end':'2026-10-20'},'source':str(source),'src_sha256':p.A.digest(source),'recorded_at':'2026-10-23T01:00:00+00:00','backend':'local-dom-bridge','operator_skill':'douyin-laike-operator','bytes':source.stat().st_size,'page_filtered':100,'record_url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123','transport_proof':{'safety':'DOM-only','reviewed_extension_ready':True,'safety_version':'dom-only-20261021-11'}}
  f=self.root/'receipt.json';f.write_text(json.dumps(receipt));self.ref={'path':str(f),'sha256':p.A.digest(f)};self.job.update(source_receipt=str(f),source_receipt_sha256=self.ref['sha256'])
  self.profile={'contract':p.CONTRACT,'status':'pending-live-multipage-validation','text_schema':'public-visible-text-v2'}
  self.export=[{'review_id':'r'+str(i),'match':('店',f'客{i}',f'正文{i}'),'store':'店','customer':f'客{i}','text':f'正文{i}','stars':1,'date':'2026-10-01','time':'2026-10-01T00:00:00+08:00','product':'商品','id_source':'verified-export-tuple','canonical_sha256':str(i),'source_row':i+2} for i in range(44)]
  from dom_evidence import review_filter_fields
  fields={k:{'attributes':{'value':v}} for k,v in [('评价时间','2026-09-21 ~ 2026-10-20'),('评价类型','全部'),('评价来源','全部'),('评价状态','全部')]}
  self.patches=[patch.object(p.n,'public_identity'),patch('dom_evidence.all_store_scope'),patch('dom_evidence.review_filter_fields',return_value=fields),patch.object(p.A,'load_export',return_value=(self.export,[]))]
  for q in self.patches:q.start();self.addCleanup(q.stop)
 def page(self,index,terminal=False):
  cards=[]
  for i in range((index-1)*10,min(index*10,44)):
   body=node(cl='text-Hl9jZe',name=f'正文{i}');body['public_visible_text']={'method':'visible-innerText-v1','value':f'正文{i}','complete':True}
   cards.append(node(cl='commentItem-jrXo5p',selector='#card'+str(i),children=[node(cl='poiName-W9HDFV',name='店'),node(cl='nickName-wB7fZf',name=f'客{i}'),body,node(cl='button-vhqEd7',name='查看投诉结果')]))
  boundary=[node(cl='foldTitleContainer-DwIByI',selector='#boundary',children=[node(name='以下为平台折叠评价'),node(name='FOLDED_TEXT_MUST_NOT_BECOME_NORMAL')])] if terminal else []
  root=node(cl=p.LIST,children=[node(cl=p.HEAD,children=[node(name='已筛选44条')]),*cards,*boundary,pg(index)])
  return {'tab':{'tabId':7,'windowId':8,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'},'tree':{'kind':'DOM-derived semantic tree (not native AX)','url':'https://life.douyin.com/p/life_comment/management','truncated':False,'root':node('body',children=[node(cl='option-YmRyn3 isSelected-ov8pOi',name='中差评（1-3心）'),root,node(cl='src-components-HeaderV2-components-Profile-index-module__title--test',name='服务商1')])},'observed_at':f'2026-10-23T02:00:0{index}+00:00'}
 def finish_pages(self):
  pages=[self.page(i,terminal=i==5) for i in range(1,6)];profile=copy.deepcopy(self.profile);profile['status']='live-validated';profile['terminal_layout']={'page_sha256s':[p.A.data_hash(pages[-1])],'boundary_matcher':{'attributes':{'class':'foldTitleContainer-DwIByI'}},'boundary_label':'以下为平台折叠评价'};return pages,profile
 def pairs(self,pages,profile):
  pairs=[]
  for page in pages:
   before=copy.deepcopy(page);before['observed_at']=page['observed_at'].replace('02:00:','01:59:');pairs.append([before,page])
  if profile.get('terminal_layout'):
   profile['terminal_layout']['page_sha256s']=[p.A.data_hash(x) for x in pairs[-1]]
  return pairs
 def test_page1_separate_counts_exact_join_no_completion(self):
  result=p.inspect_page(self.job,self.page(1),self.profile,self.ref);self.assertEqual((result['normal_header_count'],result['pager']['platform_pager_total'],len(result['rows'])),(44,54,10));self.assertFalse(result['all_normal_read']);self.assertFalse(result['profile_live_validated']);p.n.public_identity.assert_called_once()
 def test_first_page_only_or_unknown_terminal_layout_cannot_finalize(self):
  with self.assertRaisesRegex(ValueError,'awaits-live-validation'):p.finalize_pages(self.job,[self.page(1)],self.profile,self.ref,stable_pairs=self.pairs([self.page(1)],self.profile))
  with self.assertRaisesRegex(ValueError,'awaits-live-profile'):p.inspect_page(self.job,self.page(5,True),self.profile,self.ref)
 def test_full_synthetic_44_normal_terminal_page5_next_enabled_is_not_fold_count(self):
  pages,profile=self.finish_pages();result=p.finalize_pages(self.job,pages,profile,self.ref,stable_pairs=self.pairs(pages,profile));self.assertTrue(result['all_normal_read']);self.assertEqual(result['filtered_count'],44);self.assertEqual(result['platform_pager_total'],54);self.assertIsNone(result['folded_rows_observed']);self.assertTrue(result['next_may_remain_enabled_for_excluded_scope']);self.assertNotIn('FOLDED_TEXT',json.dumps(result));self.assertFalse(result['complaint_time_all_history_proven'])
 def test_missing_reordered_repeated_and_post_boundary_pages_refuse(self):
  pages,profile=self.finish_pages()
  for bad in [pages[1:],pages[:2]+pages[3:],list(reversed(pages)),pages+[pages[-1]]]:
   with self.assertRaises(ValueError):p.finalize_pages(self.job,bad,profile,self.ref,stable_pairs=self.pairs(bad,profile))
 def test_source_hash_identity_and_exact_nickname_still_fail_closed(self):
  page=self.page(1);bad=copy.deepcopy(page);bad['tab']['url']='https://life.douyin.com/p/life_comment/management?groupid=456'
  with self.assertRaises(ValueError):p.inspect_page(self.job,bad,self.profile,self.ref)
  bad=copy.deepcopy(page);bad['tree']['root']['children'][1]['children'][1]['children'][1]['name']='changed nickname'
  with self.assertRaisesRegex(ValueError,'exact-negative-join'):p.inspect_page(self.job,bad,self.profile,self.ref)
  with patch.object(p.n,'public_identity',side_effect=ValueError('account-changed')),self.assertRaisesRegex(ValueError,'account-changed'):p.inspect_page(self.job,page,self.profile,self.ref)
  Path(self.ref['path']).write_text('{}')
  with self.assertRaises(ValueError):p.inspect_page(self.job,page,self.profile,self.ref)
 def test_scope_window_or_count_drift_refuse(self):
  pages,profile=self.finish_pages();pages[1]['tab']['windowId']=9
  with self.assertRaisesRegex(ValueError,'scope-changed'):p.finalize_pages(self.job,pages,profile,self.ref,stable_pairs=self.pairs(pages,profile))
 def state(self):
  fp=hashlib.sha256(json.dumps(self.job,sort_keys=True,ensure_ascii=False).encode()).hexdigest();s={'fingerprint':fp,'tab_id':7,'phase':'observeNegative','calls':[{'key':'date-confirmed','state':'confirmed'}],'revision':3};raw=json.dumps(s).encode();up=p.parser_upgrade(raw,self.job,hashlib.sha256(raw).hexdigest(),first_page=self.page(1),profile=self.profile,receipt_ref=self.ref);self.assertEqual(up['calls'],s['calls']);self.assertEqual(up['revision'],3);return up
 def test_upgrade_and_single_intent_unknown_never_rekeys_or_replays(self):
  s=self.state();value=p.prepare_adjacent_intent(s,self.job,self.page(1),self.profile,self.ref,'next');self.assertTrue(value['requires_atomic_save_before_dispatch']);self.assertEqual(len(s['calls']),1);intent=value['state'];self.assertEqual(intent['calls'][-1]['state'],'unknown')
  with self.assertRaisesRegex(ValueError,'unknown-no-replay'):p.prepare_adjacent_intent(intent,self.job,self.page(1),self.profile,self.ref,'next')
  intent['calls'][-1]['state']='confirmed';out=p.prepare_adjacent_intent(intent,self.job,self.page(1),self.profile,self.ref,'next');self.assertIsNone(out['command']);self.assertEqual(out['read_only_verify_target_page'],2)
 def test_upgrade_hash_unknown_and_end_boundary_refuse(self):
  s=self.state();raw=json.dumps(s).encode()
  with self.assertRaises(ValueError):p.parser_upgrade(raw,self.job,'0'*64)
  with self.assertRaises(ValueError):p.prepare_adjacent_intent(s,self.job,self.page(1),self.profile,self.ref,'previous')
  pages,profile=self.finish_pages()
  with self.assertRaisesRegex(ValueError,'boundary'):p.prepare_adjacent_intent(s,self.job,pages[-1],profile,self.ref,'next')
  previous=p.prepare_adjacent_intent(s,self.job,pages[-1],profile,self.ref,'previous');self.assertEqual(previous['expected_target_page'],4);self.assertEqual(previous['command']['locator']['value'],'#previous')
 def test_unstable_pair_duplicate_across_pages_and_short_coverage_refuse(self):
  pages,profile=self.finish_pages();pairs=self.pairs(pages,profile);pairs[1][0]['tree']['root']['children'][1]['children'][1]['children'][-1]['name']='投诉审核中'
  with self.assertRaisesRegex(ValueError,'not-stable'):p.finalize_pages(self.job,pages,profile,self.ref,stable_pairs=pairs)
  pages,profile=self.finish_pages();pages[1]['tree']['root']['children'][1]['children'][1]=copy.deepcopy(pages[0]['tree']['root']['children'][1]['children'][1])
  with self.assertRaisesRegex(ValueError,'repeat'):p.finalize_pages(self.job,pages,profile,self.ref,stable_pairs=self.pairs(pages,profile))
  pages,profile=self.finish_pages();del pages[-1]['tree']['root']['children'][1]['children'][1]
  with self.assertRaisesRegex(ValueError,'coverage-incomplete'):p.finalize_pages(self.job,pages,profile,self.ref,stable_pairs=self.pairs(pages,profile))
 def test_without_two_real_read_evidence_never_finalize(self):
  pages,profile=self.finish_pages()
  with self.assertRaisesRegex(ValueError,'stable-pairs'):p.finalize_pages(self.job,pages,profile,self.ref)
  pairs=[[page,page] for page in pages]
  with self.assertRaisesRegex(ValueError,'distinct-read-times'):p.finalize_pages(self.job,pages,profile,self.ref,stable_pairs=pairs)
 def test_new_envelope_rejoins_authority_but_keeps_old_contract_separate(self):
  pages,profile=self.finish_pages();pairs=self.pairs(pages,profile);identity=copy.deepcopy(pairs[0][0]);env={'source':'local-dom-bridge','company':self.job['company'],'groupid':self.job['groupid'],'identity_evidence':identity,'pages':pages,'stable_page_pairs':pairs}
  source=p.joined_envelope(self.job,env,profile,self.ref);self.assertEqual(len(source['rows']),44);self.assertEqual(source['authority_binding']['receipt_sha256'],self.ref['sha256']);self.assertEqual(source['excluded_folded_count'],0);self.assertIsNone(source['observed_folded']);self.assertEqual(source['rows'][0]['stars'],1)
 def full(self):
  pages,profile=self.finish_pages();pairs=self.pairs(pages,profile);env={'source':'local-dom-bridge','company':self.job['company'],'groupid':self.job['groupid'],'identity_evidence':copy.deepcopy(pairs[0][0]),'pages':pages,'stable_page_pairs':pairs};source=p.joined_envelope(self.job,env,profile,self.ref);return env,profile,source
 def test_case_reader_requires_whole_source_and_exact_target_page(self):
  env,profile,source=self.full();row=source['rows'][0];current=copy.deepcopy(env['pages'][0]);current['observed_at']='2026-10-23T03:00:00+00:00';result=p.current_page_for_case(current,self.job,env,profile,source,row);self.assertEqual(result['pager']['page'],1)
  with self.assertRaisesRegex(ValueError,'current-page-scope'):p.current_page_for_case(env['pages'][1],self.job,env,profile,source,row)
  with self.assertRaisesRegex(ValueError,'complete-source-required'):p.current_page_for_case(current,self.job,env,profile,{},row)
 def test_case_reader_foreign_provider_or_changed_order_never_pass(self):
  env,profile,source=self.full();row=source['rows'][0];current=copy.deepcopy(env['pages'][0]);current['tree']['root']['children'][-1]['name']='服务商9'
  with self.assertRaisesRegex(ValueError,'provider-unverified'):p.current_page_for_case(current,self.job,env,profile,source,row)
  current=copy.deepcopy(env['pages'][0]);cards=current['tree']['root']['children'][1]['children'];cards[1],cards[2]=cards[2],cards[1]
  with self.assertRaisesRegex(ValueError,'ordered-page-changed'):p.current_page_for_case(current,self.job,env,profile,source,row)
 def test_terminal_case_fresh_read_anchors_old_verified_boundary_not_old_timestamp(self):
  env,profile,source=self.full();row=source['rows'][-1];current=copy.deepcopy(env['pages'][-1]);current['observed_at']='2026-10-23T03:05:00+00:00';result=p.current_page_for_case(current,self.job,env,profile,source,row);self.assertEqual(result['pager']['page'],5);self.assertFalse(result['all_normal_read']);self.assertIsNotNone(result['terminal_boundary'])
if __name__=='__main__':unittest.main()
