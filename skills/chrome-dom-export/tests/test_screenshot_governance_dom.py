"""Pure offline real-shape screenshot adapters; no browser or screenshot request."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import frame_capture as f
import verified_capture as v
import test_frame_capture as fixtures
node=fixtures.node

class GovernanceDomTests(unittest.TestCase):
 def test_real_header_wrapper_and_unreviewed_wrappers(self):
  title=node('#title','违规原因',attributes={'class':'governance_merchant-Table-HeadCellContentTitle'})
  h={**node('#h','违规原因','columnheader',{'class':'governance_merchant-Table-Cell'},[node('#wrap','违规原因',children=[title])]),'tag':'th'}
  self.assertEqual(v.explicit_header_text(h),'违规原因')
  bad=copy.deepcopy(h);bad['tag']='div'
  with self.assertRaisesRegex(ValueError,'not-reviewed'):v.explicit_header_text(bad)
  bad=copy.deepcopy(h);bad['children'].append(node('#extra','其他内容'))
  with self.assertRaisesRegex(ValueError,'extra-visible'):v.explicit_header_text(bad)
 def test_actual_css_scope_unread_and_pager(self):
  alltab={**node('#all','全部21',attributes={'class':'governance_merchant-tab-bar-item governance_merchant-tab-bar-item-active'}),'tag':'div'}
  self.assertEqual(f.governance_all(alltab),21)
  self.assertRaises(ValueError,f.governance_all,alltab,20)
  alltab['attributes']['class']='governance_merchant-tab-bar-item';self.assertRaises(ValueError,f.governance_all,alltab)
  icon={**node('#icon',attributes={'class':'governance_merchant-checkbox-icon governance_merchant-checkbox-icon-uncheck'}),'tag':'span'}
  unread={**node('#unread','只看未读',attributes={'class':'governance_merchant-checkbox'},children=[icon]),'tag':'label'}
  f.governance_unread_off(unread);icon['attributes']['class']='governance_merchant-checkbox-icon governance_merchant-checkbox-icon-check'
  self.assertRaises(ValueError,f.governance_unread_off,unread)
  nxt={**node('#next',attributes={'class':'governance_merchant-pager-item governance_merchant-pager-item-disabled'}),'tag':'li','disabled':False}
  self.assertTrue(f.governance_next_disabled(nxt));nxt['attributes']['class']='governance_merchant-pager-item';self.assertFalse(f.governance_next_disabled(nxt))
 def test_notice_id_only_from_real_first_td(self):
  p={'domProfile':'governance-records-v1','noticeIdMode':'first-cell-text-v1'}
  row={**node('#row','',role='row',attributes={'class':'governance_merchant-Table-Row'},children=[{**node('#cell','一般 原因 ID: 202610204779150548',role='cell'),'tag':'td'},{**node('#subject','门店ID: wrong',role='cell'),'tag':'td'}]),'tag':'tr'}
  self.assertEqual(f.row_notice_id(row,p),'202610204779150548')
  row['children'][0]['name']='无通知书编号';self.assertRaises(ValueError,f.row_notice_id,row,p)
  row['children'][0]['name']='ID: a ID: b';self.assertRaises(ValueError,f.row_notice_id,row,p)
  row['role']='generic';self.assertRaises(ValueError,f.row_notice_id,row,p)
 def test_full_page_inputs_support_reviewed_css_and_first_cell_ids(self):
  fixture=fixtures.FrameTests('test_foreign_profile_revision_rejected_even_when_marked_accepted');fixture.setUp();self.addCleanup(fixture.doCleanups)
  profile=fixture.profile['records'];profile.update(domProfile='governance-records-v1',noticeIdMode='first-cell-text-v1');profile.pop('idAttribute');f.atomic(fixture.profile_path,fixture.profile);fixture.profile_ref=fixture.ref(fixture.profile_path)
  obs=fixture.observation(1);children=obs['tree']['root']['children'];by={n['selector']:n for n in children}
  by['#all'].update(tag='div',name='全部3',attributes={'class':'governance_merchant-tab-bar-item governance_merchant-tab-bar-item-active'},children=[node('#all-label','全部3')])
  by['#total'].update(tag='div',name='全部3',attributes={'class':'governance_merchant-tab-bar-item governance_merchant-tab-bar-item-active'})
  by['#unread'].update(tag='label',attributes={'class':'governance_merchant-checkbox'},children=[{**node('#unread-icon',attributes={'class':'governance_merchant-checkbox-icon governance_merchant-checkbox-icon-uncheck'}),'tag':'span'}])
  by['#page'].update(tag='li',attributes={'class':'governance_merchant-pager-item governance_merchant-pager-item-checked'})
  by['#next'].update(tag='li',attributes={'class':'governance_merchant-pager-item'})
  for row in by['#rows']['children']:
   row.update(tag='tr');row['attributes']['class']='governance_merchant-Table-Row';row['attributes'].pop('data-notice-id');row['children'].insert(0,{**node(row['selector']+'-reason','原因 '+row['name'].split()[0],role='cell'),'tag':'td'})
  path=fixture.root/'reviewed-shape.json';f.atomic(path,obs);result=f.page_inputs(fixture.source_ref,fixture.ref(path),fixture.profile_ref);self.assertEqual([r['notice_id'] for r in result['scope']['page_rows']],['notice-1','notice-2']);self.assertFalse(result['scope']['last_page'])
 def test_actual_recorded_dom_helpers_without_claiming_live_acceptance(self):
  path=Path(__file__).resolve().parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/profile-discovery-evidence/001-records.json'
  if not path.exists():self.skipTest('optional recorded public DOM absent')
  obs=json.loads(path.read_text());ns=v.allnodes(obs['tree']);headers=[n for n in ns if n.get('role')=='columnheader'];self.assertEqual([v.explicit_header_text(n) for n in headers[:5]],list(f.HEADERS))
  rows=[n for n in ns if n.get('tag')=='tr' and 'governance_merchant-Table-Row' in f.css_tokens(n) and 'ID:' in n.get('name','')];self.assertTrue(rows)
  for row in rows:self.assertTrue(f.row_notice_id(row,{'domProfile':'governance-records-v1','noticeIdMode':'first-cell-text-v1'}))
if __name__=='__main__':unittest.main()
