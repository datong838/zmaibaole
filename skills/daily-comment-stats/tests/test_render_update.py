import sys
from pathlib import Path
import tempfile
import unittest
import openpyxl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from render_update import build,render

class UpdateTest(unittest.TestCase):
    def make(self,path,rows):
        w=openpyxl.Workbook();s=w.active
        s.append(['门店名称','用户昵称','评价时间','推荐等级','文本内容','图片内容','视频内容','商家是否回复','消费商品','评价来源'])
        for r in rows:s.append(r)
        w.save(path);w.close()
    def test_raw_details_and_zero_daily_bad_are_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.xlsx';self.make(p,[['甲店','匿名','2026-10-17 12:00:00','1星','原文，不新鲜','图片',None,'否','商品甲','团购'],['乙店','匿名','2026-10-18 12:00:00','5星','满意',None,None,'是','商品乙','其他']])
            data=build(p,'公司','2026-10-17','2026-10-18');text=render(data,'品牌','目标群')
            self.assertEqual((data['rows'],data['good'],data['bad']),(2,1,1))
            self.assertIn('10.18：新增1条，好评1条，中差评0条',text)
            self.assertIn('顾客原文：原文，不新鲜',text)
            self.assertIn('商家回复：未回复',text)
            self.assertNotIn('投诉处理进度',text)
            self.assertNotIn('违规方面',text)
            self.assertIn('有文无图1条',text)
            self.assertNotIn('数据说明：',text)
            self.assertIn('仅发测试群',text)
            self.assertNotIn('历史Excel',text)
            self.assertNotIn('非实时采集',text)
            online=render(data,'品牌','目标群','online')
            self.assertNotIn('仅发测试群',online);self.assertNotIn('非实时采集',online);self.assertNotIn('拟发群',online)
    def test_zero_rows_never_make_report(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.xlsx';self.make(p,[])
            with self.assertRaisesRegex(ValueError,'zero-rows'):build(p,'公司','2026-10-17','2026-10-18')

if __name__=='__main__':unittest.main()
