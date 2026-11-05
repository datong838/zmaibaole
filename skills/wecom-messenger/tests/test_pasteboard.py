"""Exercise clipboard restoration without accessing the real system clipboard."""
import copy
import ctypes as C
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pasteboard

class FakeObjC:
    instance=None
    oversized=False
    def __init__(self):
        FakeObjC.instance=self;self.count=7;self.items=[{'public.utf8-plain-text':b'original','custom.type':b'\x00\x01'}];self.original=copy.deepcopy(self.items);self.buffers=[]
        self.pb=object()
    def cls(self,name):return name
    def string(self,text):return text
    def text(self,text):return text
    def length(self,obj):return len(obj)
    def item(self,obj,index):return obj[index]
    def call(self,r,sel,*args,result=C.c_void_p):
        a=[v for _,v in args]
        if sel=='alloc':return {'class':r}
        if sel=='init':return {} if r.get('class')=='NSPasteboardItem' else r
        if sel in ('drain','release'):return None
        if r=='NSPasteboard' and sel=='generalPasteboard':return self.pb
        if r is self.pb:
            if sel=='changeCount':return self.count
            if sel=='pasteboardItems':return self.items
            if sel=='clearContents':self.items=[];self.count+=1;return self.count
            if sel=='writeObjects:':self.items=copy.deepcopy(a[0]);self.count+=1;return True
            if sel=='stringForType:':return self.items[0].get(a[0])
        if sel=='types':return list(r)
        if sel=='dataForType:':return {'raw':r[a[0]]}
        if sel=='length':return 33*1024*1024 if self.oversized else len(r['raw'])
        if sel=='bytes':
            b=C.create_string_buffer(r['raw']);self.buffers.append(b);return C.cast(b,C.c_void_p)
        if r=='NSURL' and sel=='fileURLWithPath:':return {'public.file-url':Path(a[0]).as_uri()}
        if r=='NSArray' and sel=='arrayWithObject:':return [a[0]]
        if r=='NSMutableArray' and sel=='array':return []
        if r=='NSData' and sel=='dataWithBytes:length:':return C.string_at(a[0],a[1])
        if sel=='setData:forType:':r[a[1]]=a[0];return True
        if sel=='addObject:':r.append(copy.deepcopy(a[0]));return None
        raise AssertionError((r,sel,a))

class ClipboardTest(unittest.TestCase):
    def test_all_formats_restored_after_file_paste(self):
        with patch.object(pasteboard,'ObjC',FakeObjC):
            with pasteboard.file_url('/tmp/test.xlsx') as result:
                fake=FakeObjC.instance;self.assertEqual(fake.items,[{'public.file-url':'file:///tmp/test.xlsx'}])
            self.assertEqual(fake.items,fake.original);self.assertTrue(result['restored'])
    def test_restore_even_if_send_raises(self):
        with patch.object(pasteboard,'ObjC',FakeObjC):
            with self.assertRaisesRegex(RuntimeError,'send failed'):
                with pasteboard.file_url('/tmp/test.xlsx'):raise RuntimeError('send failed')
            fake=FakeObjC.instance;self.assertEqual(fake.items,fake.original)
    def test_concurrent_copy_not_overwritten(self):
        with patch.object(pasteboard,'ObjC',FakeObjC):
            with pasteboard.file_url('/tmp/test.xlsx') as result:
                fake=FakeObjC.instance;fake.items=[{'new':b'user copied'}];fake.count+=1
            self.assertEqual(fake.items,[{'new':b'user copied'}]);self.assertFalse(result['restored']);self.assertTrue(result['concurrent_change'])
    def test_own_clipboard_url_type_count_and_change_verified(self):
        with patch.object(pasteboard,'ObjC',FakeObjC):
            with pasteboard.file_url('/tmp/test.png') as result:
                proof=result['assert_owned']();self.assertTrue(proof['file_url_verified']);self.assertIn('public.file-url',proof['types'])
                fake=FakeObjC.instance;fake.count+=1
                with self.assertRaisesRegex(pasteboard.PasteboardError,'owned-clipboard-changed'):result['assert_owned']()
    def test_oversized_original_clipboard_is_never_cleared(self):
        with patch.object(pasteboard,'ObjC',FakeObjC),patch.object(FakeObjC,'oversized',True):
            with self.assertRaisesRegex(pasteboard.PasteboardError,'too-large'):
                with pasteboard.file_url('/tmp/test.xlsx'):pass
            fake=FakeObjC.instance;self.assertEqual(fake.items,fake.original);self.assertEqual(fake.count,7)

if __name__=='__main__':unittest.main()
