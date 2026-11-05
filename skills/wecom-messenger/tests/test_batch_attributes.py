import ctypes as C,sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native import Native,AXError
class BulkTests(unittest.TestCase):
    def setup_native(self,values,error=0):
        n=Native.__new__(Native);n.refs=[];n._attribute_batches={('AXRole','AXValue'):10};self.calls=0
        def bulk(e,keys,options,out):
            self.calls+=1;self.assertEqual(options,0);out._obj.value=20;return error
        def readerr(v,typ,out):out._obj.value=values[v];return True
        n.ax=SimpleNamespace(AXUIElementCopyMultipleAttributeValues=bulk,AXValueGetTypeID=lambda:3,AXValueGetType=lambda v:5,AXValueGetValue=readerr)
        n.cf=SimpleNamespace(CFGetTypeID=lambda v:1 if v==20 else 3 if v in values and isinstance(values[v],int) else 2,CFArrayGetTypeID=lambda:1,CFArrayGetCount=lambda _:2,CFArrayGetValueAtIndex=lambda arr,i:100+i)
        n.decode=lambda v:values.get(v);n.get=lambda e,k:(_ for _ in ()).throw(AssertionError('no serial IPC'))
        return n
    def test_all_fields_one_public_call_in_same_order(self):
        n=self.setup_native({100:'AXTextArea',101:'complete text'})
        self.assertEqual(n.node_attributes(1,['AXRole','AXValue']),{'AXRole':'AXTextArea','AXValue':'complete text'})
        self.assertEqual(self.calls,1);self.assertEqual(n.batch_attribute_reads,1)
    def test_unsupported_field_is_not_transport_failure(self):
        n=self.setup_native({100:'AXGroup',101:-25205})
        self.assertEqual(n.node_attributes(1,['AXRole','AXValue'])['AXValue'],None)
    def test_unsupported_input_value_is_not_proof_of_empty_draft(self):
        n=self.setup_native({100:'AXTextArea',101:-25205})
        with self.assertRaisesRegex(AXError,'input-value-unreadable'):n.node_attributes(1,['AXRole','AXValue'])
    def test_timeout_cannot_become_empty_composer(self):
        n=self.setup_native({100:'AXTextArea',101:-25204})
        with self.assertRaisesRegex(AXError,'batch-attribute-unavailable:AXValue:-25204'):n.node_attributes(1,['AXRole','AXValue'])
    def test_optional_description_failure_is_explicit_not_an_empty_value(self):
        n=self.setup_native({100:'AXGroup',101:-25200})
        n._attribute_batches={('AXRole','AXDescription'):10};n.get=lambda e,key:None
        out=n.node_attributes(1,['AXRole','AXDescription'])
        self.assertIsNone(out['AXDescription']);self.assertEqual(out['__attribute_errors__'],{'AXDescription':-25200})
    def test_generic_input_value_failure_is_never_ignored(self):
        n=self.setup_native({100:'AXTextArea',101:-25200});n.get=lambda e,key:'should not be called'
        with self.assertRaisesRegex(AXError,'AXValue:-25200'):n.node_attributes(1,['AXRole','AXValue'])
    def test_missing_batch_result_cannot_be_complete(self):
        n=self.setup_native({100:'AXTextArea',101:'draft'});n.cf.CFArrayGetCount=lambda _:1
        with self.assertRaisesRegex(AXError,'incomplete'):n.node_attributes(1,['AXRole','AXValue'])
    def test_bulk_illegal_argument_only_falls_back_on_verified_ax_element(self):
        n=self.setup_native({100:'AXTextArea',101:'verified draft'},-25201)
        n.ax.AXUIElementGetTypeID=lambda:2
        n.ax.AXUIElementCopyAttributeValue=lambda *args:0
        seen=[]
        n.single_node_attributes=lambda e,keys:seen.append((e,keys)) or {'AXRole':'AXTextArea','AXValue':'verified draft'}
        self.assertEqual(n.node_attributes(1,['AXRole','AXValue'])['AXValue'],'verified draft');self.assertEqual(len(seen),1)
        n.ax.AXUIElementGetTypeID=lambda:999
        with self.assertRaisesRegex(AXError,'element-unverified'):n.node_attributes(1,['AXRole','AXValue'])
    def test_single_fallback_keeps_input_failure_strict(self):
        n=self.setup_native({},-25201);n.string=lambda key:key;n.cf.CFRelease=lambda _:None
        def single(e,key,out):
            if key=='AXRole':out._obj.value=100;return 0
            return -25204
        n.ax.AXUIElementCopyAttributeValue=single;n.decode=lambda v:'AXTextArea' if v==100 else None
        with self.assertRaisesRegex(AXError,'single-attribute-unavailable:AXValue:-25204'):n.single_node_attributes(1,['AXRole','AXValue'])
    def test_not_implemented_falls_back_to_same_fields(self):
        n=self.setup_native({},-25208);seen=[]
        n.get=lambda e,k:seen.append(k) or k
        self.assertEqual(n.node_attributes(1,['AXRole','AXValue']),{'AXRole':'AXRole','AXValue':'AXValue'})
        self.assertEqual(seen,['AXRole','AXValue'])
if __name__=='__main__':unittest.main()
