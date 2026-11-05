"""Real public AppKit image decoder test; no app UI or external sends."""
import ctypes as C
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pasteboard import ObjC
from image_verify import pixels,verify_rtf,ImageProofError

@unittest.skipUnless(sys.platform=='darwin','macOS public image frameworks')
class ImageTests(unittest.TestCase):
    def test_actual_image_decoder_is_deterministic(self):
        # Existing locally rendered fixture image, not a business export.
        candidates=list((Path(__file__).resolve().parents[3]/'work/development-validation/violation-notifier').glob('fixture-small/batches/*/*完整表格-01.png'))
        if not candidates:self.skipTest('fixture PNG not generated')
        o=ObjC();pool=o.call(o.call(o.cls('NSAutoreleasePool'),'alloc'),'init')
        try:
            data=o.call(o.cls('NSData'),'dataWithContentsOfFile:',(C.c_void_p,o.string(str(candidates[0]))))
            first=pixels(o,data);second=pixels(o,data)
            self.assertEqual(first,second);self.assertGreater(first['width'],100);self.assertGreater(first['height'],50)
        finally:o.call(pool,'drain',result=None)
    def test_source_hash_change_rejected_before_rtf_decode(self):
        source=Path(__file__)
        with self.assertRaisesRegex(ImageProofError,'source-file-changed'):verify_rtf(b'invalid',{'file':str(source),'file_sha256':'bad'})
if __name__=='__main__':unittest.main()
