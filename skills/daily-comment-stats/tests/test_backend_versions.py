import ast,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ds_common import acquisition_backend_valid
class BackendVersions(unittest.TestCase):
    def test_loaded_bridge_package_version_is_accepted_by_handoff(self):
        bridge=Path(__file__).resolve().parents[2]/'chrome-dom-export/scripts/bridge.py'
        module=ast.parse(bridge.read_text())
        versions=[n.value.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SAFETY_VERSION' for t in n.targets)]
        self.assertEqual(len(versions),1)
        self.assertTrue(acquisition_backend_valid({'operator_skill':'douyin-laike-operator','backend':'local-dom-bridge','transport_proof':{'safety_version':versions[0],'safety':'DOM-only','reviewed_extension_ready':True}}),'Bridge upgrade must update the validated acquisition handoff before live loading')
    def test_reviewed_current_and_historical_versions(self):
        for version in range(3,12):
            self.assertTrue(acquisition_backend_valid({'operator_skill':'douyin-laike-operator','backend':'local-dom-bridge','transport_proof':{'safety_version':f'dom-only-20261021-{version}','safety':'DOM-only','reviewed_extension_ready':True}}))
    def test_unreviewed_or_unready_is_rejected(self):
        base={'operator_skill':'douyin-laike-operator','backend':'local-dom-bridge','transport_proof':{'safety_version':'dom-only-20261021-7','safety':'DOM-only','reviewed_extension_ready':True}}
        for k,v in [('safety_version','dom-only-20261021-12'),('safety','debugger'),('reviewed_extension_ready',False)]:
            obj={**base,'transport_proof':{**base['transport_proof'],k:v}};self.assertFalse(acquisition_backend_valid(obj))
if __name__=='__main__':unittest.main()
