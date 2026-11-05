"""Synthetic call doubles only; never connects to localhost or reads config."""
import importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('bridge_timing_candidate',Path(__file__).resolve().parents[1]/'scripts/bridge.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
class Timing(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)/'diagnostic';self.addCleanup(patch.stopall);patch.dict(os.environ,{'BRIDGE_REQUEST_PERFORMANCE_DIR':str(self.out)}).start();patch.object(b,'read_config',side_effect=AssertionError('must not read config')).start()
 def logs(self):return [json.loads(p.read_text()) for p in self.out.glob('*.json')]
 def test_once_original_payload_timeout_and_return_identity(self):
  result={'ok':True,'result':{'secret':'do not log'}};command={'op':'tabs'}
  with patch.object(b,'call',return_value=result) as call,patch.object(b.time,'perf_counter_ns',side_effect=[100,150]):
   self.assertIs(b.request(command,timeout=43),result)
  call.assert_called_once_with('/v1/request',{'command':command,'timeout':43});row=self.logs()[0];self.assertEqual(row,{'schema':'bridge-request-timing-v1','op':'tabs','elapsed_monotonic_ns':50,'ok':True,'outcome':'success','exception':False})
 def test_exception_instance_and_no_retry(self):
  error=RuntimeError('SECRET_PATH token cookie body')
  with patch.object(b,'call',side_effect=error) as call:
   with self.assertRaises(RuntimeError) as got:b.request({'op':'tabs'})
  self.assertIs(got.exception,error);self.assertEqual(call.call_count,1);self.assertEqual(self.logs()[0]['outcome'],'exception');self.assertNotIn('SECRET',next(self.out.glob('*.json')).read_text())
 def test_unknown_not_delivered_and_failed_outcome_fixed(self):
  for outcome in ['unknown','not-delivered','arbitrary SECRET']:
   result={'ok':False,'outcome':outcome,'error':'SECRET'}
   with patch.object(b,'call',return_value=result):self.assertIs(b.request({'op':'tabs'}),result)
  self.assertEqual({x['outcome'] for x in self.logs()},{'unknown','not-delivered','failed'})
 def test_disabled_no_clock_no_file_and_one_call(self):
  with patch.dict(os.environ,{'BRIDGE_REQUEST_PERFORMANCE_DIR':''}),patch.object(b.time,'perf_counter_ns',side_effect=AssertionError('disabled clock')),patch.object(b,'call',return_value=7) as call:self.assertEqual(b.request({'op':'tabs'}),7)
  self.assertEqual(call.call_count,1);self.assertFalse(self.out.exists())
 def test_relative_directory_does_not_enable(self):
  with patch.dict(os.environ,{'BRIDGE_REQUEST_PERFORMANCE_DIR':'relative'}),patch.object(b.time,'perf_counter_ns',side_effect=AssertionError('disabled clock')),patch.object(b,'call',return_value=7):self.assertEqual(b.request({'op':'tabs'}),7)
  self.assertFalse(self.out.exists())
 def test_clock_output_failure_keeps_return_and_exception(self):
  with patch.object(b.time,'perf_counter_ns',side_effect=OSError('clock')),patch.object(b,'call',return_value=8):self.assertEqual(b.request({'op':'tabs'}),8)
  error=RuntimeError('original')
  with patch.object(b.Path,'mkdir',side_effect=OSError('write')),patch.object(b,'call',side_effect=error):
   with self.assertRaises(RuntimeError) as got:b.request({'op':'tabs'})
  self.assertIs(got.exception,error)
 def test_invalid_command_records_no_payload_no_network(self):
  with patch.object(b,'call',side_effect=AssertionError('network')) as call:
   with self.assertRaises(ValueError):b.request({'op':'SECRET_COMPANY','token':'SECRET_TOKEN'})
  call.assert_not_called();self.assertEqual(self.logs()[0]['op'],'unknown');raw=next(self.out.glob('*.json')).read_text();self.assertNotIn('SECRET',raw)
 def test_valid_sensitive_command_only_fixed_op_and_fields(self):
  command={'op':'find','tabId':123,'locator':{'by':'text','value':'SECRET_COMPANY'}}
  with patch.object(b,'call',return_value={'ok':True,'result':command}):b.request(command)
  raw=next(self.out.glob('*.json')).read_text();self.assertNotIn('SECRET',raw);self.assertEqual(set(self.logs()[0]),{'schema','op','elapsed_monotonic_ns','ok','outcome','exception'})
if __name__=='__main__':unittest.main()
