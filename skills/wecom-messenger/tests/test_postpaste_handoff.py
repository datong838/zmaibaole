"""Stateful native-contract double, real image proof/recipient/send state machine."""
import copy,json,tempfile,unittest,sys,hashlib
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).parents[1]/'scripts'),str(Path(__file__).parent)]
import files as f,messenger as m,ui
from datetime import datetime
class FixedDatetime(datetime):
 @classmethod
 def now(cls,tz=None):return cls(2026,10,23,12,0,0,tzinfo=tz)
from test_images import image_snapshot
class NativeContract:
 def __init__(self):self.pid=123;self.input_generation=0;self.by_path={};self.keys=[];self.reads=0;self.draft='';self.sent=False;self.after_focus=None;self.path=None;self.closed=0
 def tree(self):
  self.reads+=1;self.by_path={};s=image_snapshot(self.draft,with_image=self.sent);s['read_scope']='application-windows-complete'
  if self.after_focus and self.input_generation>=6:self.after_focus(s)
  return s
 def focus(self,node):self.input_generation+=1
 def key(self,code,*args,**kw):
  self.input_generation+=1;self.keys.append(code)
  saved=json.loads(self.path.read_text())
  if code==9:
   assert saved['send_intent_at'] and saved['image_paste_seed'];self.draft='\ufffc'
  if code==36:
   assert saved['image_return_intent_at'] and saved['phase']=='image-verify-sent';self.draft='';self.sent=True
 def close(self):self.closed+=1
@contextmanager
def clipboard(path):yield {'assert_owned':lambda:{'change_count':7,'types':['public.file-url'],'file_url_verified':True},'restored':True,'concurrent_change':False}
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.addCleanup(patch.stopall);patch.object(f,'file_url',clipboard).start();patch.object(f.time,'sleep').start();patch('datetime.datetime',FixedDatetime).start();patch.object(f,'datetime',FixedDatetime).start();patch.object(m,'datetime',FixedDatetime).start()
 def job(self,key):
  source=self.root/(key+'.png');source.write_bytes(b'fake-png');p,s=m.prepare(key,'group','测试群请忽略',file=source,directory=self.root/key);n=NativeContract();n.path=p;return p,n
 def test_real_flow_single_use_read_saved_and_same_owned_checks_events(self):
  # Control reproduces old separate advance boundary by discarding only handoff;
  # all actual stage/bind/confirm functions and NativeContract operations run.
  p,n=self.job('new');initial=json.loads(p.read_text());new=m.advance(p,lambda:n);self.assertEqual(new['phase'],'image-verify-sent');self.assertEqual(n.keys,[53,9,36]);self.assertEqual(n.reads,5)
  q=p;o=NativeContract();o.path=q;m.atomic(q,initial);stage=f.stage_file
  def discard(*a,**kw):stage(*a,**kw)
  with patch.object(f,'stage_file',side_effect=discard):old=m.advance(q,lambda:o)
  self.assertEqual(old['phase'],'file-confirm');old=m.advance(q,lambda:o);self.assertEqual(o.reads,6);self.assertEqual(o.keys,n.keys)
  self.assertEqual(json.dumps(new,sort_keys=True,ensure_ascii=False).encode(),json.dumps(old,sort_keys=True,ensure_ascii=False).encode());self.__class__.evidence={'state_bytes_equal':True,'state_sha256':hashlib.sha256(json.dumps(new,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'candidate_full_reads_before_client_confirmation':n.reads,'control_full_reads_before_client_confirmation':o.reads,'candidate_keys':n.keys[:],'control_keys':o.keys[:],'events':[e['stage'] for e in new['events']],'fixed_clock':'2026-10-23T12:00:00+08:00','native_calls_real':False};self.assertEqual([e['stage'] for e in new['events']],[e['stage'] for e in old['events']]);self.assertEqual(new['image_transcript_baseline'],old['image_transcript_baseline']);self.assertFalse(new['ui_confirmed'])
  result=m.advance(p,lambda:n);self.assertEqual(result['status'],'complete');self.assertTrue(result['ui_confirmed']);self.assertFalse(result['delivery_confirmed']);self.assertEqual(n.keys,[53,9,36])
 def test_focus_new_read_recipient_draft_transcript_pid_changes_refuse(self):
  for mode in ('recipient','draft','transcript','pid','truncated'):
   p,n=self.job(mode)
   def mutate(s):
    if mode=='pid':s['pid']=999
    elif mode=='truncated':s['truncated']=True
    else:
     ctx=ui.context(s)
     if mode=='recipient':ctx['header']['AXValue']='other'
     elif mode=='draft':ctx['composer']['AXValue']='different'
     else:ctx['transcript']['children']=[]
   n.after_focus=mutate;result=m.advance(p,lambda:n)
   with self.subTest(mode=mode):self.assertEqual(result['status'],'unknown');self.assertTrue(result.get('error'));self.assertEqual(n.keys,[53,9]);self.assertNotIn('image_return_intent_at',result)
 def test_ticket_cleanup_generation_mapping_snapshot_and_pid_fail_closed(self):
  for mode in ('input','mapping','snapshot','pid'):
   p,n=self.job('cleanup-'+mode);original=f._wait_image_binding
   def wait(*a,**kw):
    ticket=original(*a,**kw)
    if mode=='input':n.input_generation+=1
    elif mode=='mapping':n.by_path={}
    elif mode=='snapshot':ticket.read.snapshot['pid']=0
    else:n.pid=999
    return ticket
   with patch.object(f,'_wait_image_binding',side_effect=wait):result=m.advance(p,lambda:n)
   self.assertEqual(result['status'],'unknown');self.assertIn('handoff-',result['error']);self.assertEqual(n.keys,[53,9])
 def test_owned_proof_and_source_changed_after_binding_refuse_without_return(self):
  for mode in ('source','proof','seed'):
   p,n=self.job('state-'+mode);original=f._wait_image_binding
   def wait(*a,**kw):
    ticket=original(*a,**kw);state=a[1]
    if mode=='source':Path(state['job']['file']).write_bytes(b'changed')
    elif mode=='proof':state['owned_image_paste']['pid']=999
    else:state['image_paste_seed']['target']='other'
    return ticket
   with patch.object(f,'_wait_image_binding',side_effect=wait):result=m.advance(p,lambda:n)
   with self.subTest(mode=mode):self.assertEqual(result['status'],'unknown');self.assertTrue(result.get('error'));self.assertEqual(n.keys,[53,9])
 def test_return_exception_remains_unknown_and_no_replay(self):
  p,n=self.job('unknown');original=n.key
  def fail(code,*args,**kw):
   original(code,*args,**kw)
   if code==36:raise RuntimeError('send-outcome-unknown')
  n.key=fail;result=m.advance(p,lambda:n);self.assertEqual(result['status'],'unknown');self.assertTrue(result['image_return_intent_at']);self.assertEqual(n.keys,[53,9,36])
  m.advance(p,lambda:n);self.assertEqual(n.keys,[53,9,36])
if __name__=='__main__':unittest.main()
