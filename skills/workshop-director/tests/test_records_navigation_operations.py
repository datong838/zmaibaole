"""Explicit synthetic normal-navigation operations; real public command/reply
parsers, supplied already-verified page tuples (scope tested in parent suite).
"""
import copy,json,sys,unittest
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from test_records_navigation_progress import m,d,D
from governance_rates_recovery import target_page_command
class Ops(unittest.TestCase):
 def setUp(self):
  raw=json.loads((H/'fixtures/records-navigation/observation.json').read_text());job=json.loads((H/'fixtures/records-navigation/job.json').read_text());q=json.loads((H/'fixtures/records-navigation/query.json').read_text());page=d.normal_page(raw['tree'],job,q);raw['observed_at']='2026-10-23T01:00:00+00:00';after=copy.deepcopy(raw);after['observed_at']='2026-10-23T01:00:02+00:00';self.refs=[{'path':'/synthetic/before.json','sha256':'a'*64},{'path':'/synthetic/after.json','sha256':'b'*64}];self.entries=[(raw,page),(after,copy.deepcopy(page))];self.q=q;self.tab=raw['tab_id'];self.op={'key':'synthetic-key-001','request':{'action':'row','page':None,'notice_id':page['rows'][0]['notice_id']},'state':'complete','before':self.refs[0],'before_page':page['page'],'intent_at':'2026-10-23T01:00:00.100000+00:00','response_at':'2026-10-23T01:00:01+00:00','after':self.refs[1],'completed_at':'2026-10-23T01:00:03+00:00'};self.scroll()
 def scroll(self,action='row'):
  before,page=self.entries[0];self.op['request']={'action':action,'page':None,'notice_id':page['rows'][0]['notice_id'] if action=='row' else None};selector=page['rows'][0]['selector'] if action=='row' else d.g.date_input(before['tree'])['selector'];node=d.g.one([n for n in d.g.nodes(before['tree']) if n.get('selector')==selector],'synthetic-node');self.op['command']={'op':'scroll','tabId':self.tab,'locator':{'by':'selector','value':selector}};self.op['result']={'version':d.nav.VERSION,'scrolled':{'selector':selector,'tag':node['tag'],'name':'dynamic aggregate deliberately ignored'}};self.op['raw_reply']={'ok':True,'result':copy.deepcopy(self.op['result'])}
 def verify(self):m.verify_operations([self.op],self.refs,self.entries,self.q,self.tab,d,d.g,target_page_command)
 def test_row_and_anchor_complete(self):self.verify();self.scroll('anchor');self.verify()
 def test_noop_same_page_only_without_input(self):
  self.op={k:v for k,v in self.op.items() if k not in ('after','completed_at','response_at','result','raw_reply')};self.op.update(command=None,request={'action':'page','page':1,'notice_id':None});self.verify();self.op['result']={}
  with self.assertRaises(ValueError):self.verify()
 def page(self):
  raw,page=self.entries[0];pager=d.g.one(d.g.classnodes(d.g.root(raw['tree'],d.g.RECORDS),'governance_merchant-pager'),'synthetic-pager');li=copy.deepcopy(d.g.one([n for n in d.g.walk(pager) if 'governance_merchant-pager-item-checked' in d.g.cls(n)],'synthetic-current'));li.update(name='2',selector=li['selector']+'-synthetic-page2',children=[]);li['attributes']['class']='governance_merchant-pager-item';pager['children'].append(li);self.q=copy.deepcopy(self.q);self.q['pages'].append({'page':2});self.op['request']={'action':'page','page':2,'notice_id':None};self.op['command']={**target_page_command(raw['tree'],2),'tabId':self.tab};self.op['result']={'kind':'navigation','version':d.nav.VERSION,'clicked':copy.deepcopy(li)};self.op['raw_reply']={'ok':True,'result':copy.deepcopy(self.op['result'])};self.entries[1][1]['page']=2
 def test_page_command_and_resulting_effect(self):self.page();self.verify();self.entries[1][1]['page']=1;self.assertRaises(ValueError,self.verify)
 def test_tampered_command_reply_or_reference(self):
  original=copy.deepcopy(self.op)
  for field in ('command','reply','after','time','request'):
   self.op=copy.deepcopy(original)
   if field=='command':self.op['command']['locator']['value']='arbitrary'
   elif field=='reply':self.op['raw_reply']['ok']=False
   elif field=='after':self.op['after']=self.refs[0]
   elif field=='time':self.op['completed_at']='2026-10-23T00:00:00+00:00'
   else:self.op['request']['extra']='unreviewed'
   with self.assertRaises(ValueError):self.verify()
 def test_page_reply_and_unique_key(self):
  self.page();self.op['result']['clicked']['name']='wrong';self.op['raw_reply']['result']=copy.deepcopy(self.op['result']);self.assertRaises(ValueError,self.verify)
 def test_unknown_confirmed_and_special_reconcile_hold(self):
  for state in ('unknown','confirmed'):
   self.op['state']=state;self.assertRaises(ValueError,self.verify)
  self.op['state']='complete';self.op['completion_kind']='readonly-scroll-effect-reconciled';self.assertRaises(ValueError,self.verify)
if __name__=='__main__':unittest.main()
