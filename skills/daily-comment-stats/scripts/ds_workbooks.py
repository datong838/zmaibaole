"""Validated XLSX input and mutually exclusive counts. No browser/network dependencies."""
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from ds_common import FlowError

REQUIRED = ['门店名称', '用户昵称', '评价时间', '推荐等级', '文本内容', '图片内容', '视频内容']
EMPTY = {'', '-', '—', '无', '[]', 'null', 'None'}
CATEGORIES = ['图文好评','纯星好评','图文差评','纯星差评','有文无图好评','有文无图差评','无文有图好评','无文有图差评','有视频内容好评','有视频内容差评']

def empty(value): return value is None or str(value).strip() in EMPTY

def rating(value):
    matched = re.fullmatch(r'([1-5])(?:\.0+)?\s*(?:星|心)?', str(value).strip())
    if not matched: raise FlowError('rating-invalid', 'Unrecognized recommendation level: %r' % value)
    return int(matched.group(1))

def review_day(value, epoch):
    if isinstance(value, datetime):
        if value.tzinfo: value = value.astimezone(ZoneInfo('Asia/Shanghai'))
        return value.date()
    if isinstance(value, date): return value
    if isinstance(value, (int, float)):
        from openpyxl.utils.datetime import from_excel
        parsed = from_excel(value, epoch)
        if isinstance(parsed, datetime): return parsed.date()
        raise FlowError('date-invalid', 'Invalid Excel review timestamp')
    text = str(value or '').strip().replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '')
    try:
        parsed=datetime.fromisoformat(text)
        return parsed.astimezone(ZoneInfo('Asia/Shanghai')).date() if parsed.tzinfo else parsed.date()
    except ValueError:
        try: return datetime.strptime(text, '%Y-%m-%d %H:%M:%S').date()
        except ValueError: raise FlowError('date-invalid', 'Unrecognized review time: %r' % value)

def category(text, image, video, stars):
    suffix = '好评' if stars >= 4 else '差评'
    if not empty(video): return '有视频内容' + suffix
    if not empty(text) and not empty(image): return '图文' + suffix
    if empty(text) and empty(image): return '纯星' + suffix
    return ('有文无图' if not empty(text) else '无文有图') + suffix

def load_reviews(path, start, end):
    import openpyxl
    from openpyxl.utils.exceptions import InvalidFileException
    from zipfile import BadZipFile
    path = Path(path)
    if path.suffix.lower() != '.xlsx': raise FlowError('source-format', 'Only real .xlsx exports are supported')
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    try: wb = openpyxl.load_workbook(path, data_only=False, read_only=False)
    except (OSError, InvalidFileException, ValueError, BadZipFile) as e: raise FlowError('source-unreadable', str(e))
    try:
        ws = wb.worksheets[0]
        headers = [str(c.value).strip() if c.value is not None else '' for c in ws[1]]
        if len([h for h in headers if h]) != len(set(h for h in headers if h)): raise FlowError('source-schema', 'Duplicate column names')
        missing = set(REQUIRED) - set(headers)
        if missing: raise FlowError('source-schema', 'Missing columns: ' + ','.join(sorted(missing)))
        idx = {name:i for i,name in enumerate(headers)}; reviews = []
        for cells in ws.iter_rows(min_row=2):
            values = [c.value for c in cells]
            if all(empty(v) for v in values): continue
            for name in REQUIRED:
                if cells[idx[name]].data_type == 'f': raise FlowError('source-formula', 'Required review fields must be literal exported values')
            day = review_day(values[idx['评价时间']], wb.epoch)
            if not first <= day <= last: raise FlowError('source-date-mismatch', 'Export has review outside requested range on row %d' % cells[0].row)
            store = str(values[idx['门店名称']] or '').strip()
            if not store: raise FlowError('store-missing', 'Missing store on row %d' % cells[0].row)
            stars = rating(values[idx['推荐等级']])
            reviews.append({'day':day.isoformat(), 'store':store, 'stars':stars,
                'category':category(values[idx['文本内容']],values[idx['图片内容']],values[idx['视频内容']],stars)})
        return reviews, headers
    finally: wb.close()

def aggregate(reviews):
    daily, stores = defaultdict(Counter), defaultdict(Counter)
    for r in reviews:
        for counts in (daily[r['day']], stores[(r['day'],r['store'])]):
            counts[r['category']] += 1; counts['好评总数' if r['stars'] >= 4 else '差评总数'] += 1; counts['当日总计'] += 1
    for counts in list(daily.values()) + list(stores.values()):
        if sum(counts[c] for c in CATEGORIES) != counts['当日总计'] or counts['好评总数']+counts['差评总数'] != counts['当日总计']: raise FlowError('reconciliation-failed')
    return daily, stores

def dom_reviews(data):
    """Normalize only verified visible records, preserving normal/folded scope."""
    result=[]
    for row in data['rows']:
        if row['section']=='folded' and (row['has_text'] or row['has_image'] or row['has_video']):
            raise FlowError('dom-folded-not-pure-stars')
        stars=row['rating']
        if type(stars)is not int or stars not in (1,2,3,5):raise FlowError('dom-rating-unverified')
        prefix=('有视频内容' if row['has_video'] else '图文' if row['has_text'] and row['has_image'] else '纯星' if not row['has_text'] and not row['has_image'] else '有文无图' if row['has_text'] else '无文有图')
        result.append({'day':row['review_day'],'store':row['store'],'stars':stars,'category':prefix+('好评' if stars>=4 else '差评'),'section':row['section']})
    if len(result)!=data['summary']['visible_rating_records']:raise FlowError('dom-count-conflict')
    return result

def dom_report_facts(data,source):
    """Verified DOM facts, explicitly absent export-only fields remain absent."""
    from ds_common import sha256
    reviews=dom_reviews(data);totals=Counter(r['category']for r in reviews);daily,_=aggregate(reviews);stores={}
    for r in reviews:
        item=stores.setdefault(r['store'],Counter());item['total']+=1;item['good'if r['stars']>=4 else'bad']+=1
    bad=[]
    for index,row in enumerate(data['rows'],1):
        if row['rating']>3:continue
        bad.append({'row':index,'store':row['store'],'time':row['review_day']+'（筛选日期；页面显示'+row['visible_relative_time']+'）','stars':row['rating'],
                    'text':row['text']or'无文字内容','image':row['has_image'],'video':row['has_video'],
                    'product':'未采集','source':'页面评价（'+('正常'if row['section']=='normal'else'折叠纯星')+'）','reply':'未采集','reply_text':None})
    return {'company':data['job']['company'],'start':data['job']['date_range']['start'],'end':data['job']['date_range']['end'],
            'source':str(Path(source).resolve()),'sha256':sha256(source),'rows':len(reviews),'good':sum(r['stars']>=4 for r in reviews),
            'bad':len(bad),'totals':dict(totals),'daily':{k:dict(v)for k,v in sorted(daily.items())},'stores':{k:dict(v)for k,v in sorted(stores.items())},
            'bad_details':bad,'test_only':True,'source_basis':{'kind':'daily-visible-dom-source-v1','counts':data['summary'],
            'download_verified':False,'source_is_authoritative_export':False,'missing_fields':data['missing_fields']}}

def write_stats(path, company, reviews):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    daily, stores = aggregate(reviews)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = '每日四象限统计'
    summary = ['公司名称','日期','好评总数','图文好评','纯星好评','差评总数','图文差评','纯星差评','中间态合计','当日总计','中间态明细']
    detail = ['公司名称','日期','门店名称','新增评总数','好评总数','图文好评','纯星好评','差评反馈总数','图文差评','纯星差评','中间态合计'] + CATEGORIES[4:]
    ws.append(summary)
    def middle(c): return sum(c[k] for k in CATEGORIES[4:])
    for day,c in sorted(daily.items()):
        ws.append([company,day,c['好评总数'],c['图文好评'],c['纯星好评'],c['差评总数'],c['图文差评'],c['纯星差评'],middle(c),c['当日总计'],'; '.join('%s：%d'%(k,c[k]) for k in CATEGORIES[4:] if c[k]) or '无'])
    ws2 = wb.create_sheet('按门店每日明细'); ws2.append(detail)
    for (day,store),c in sorted(stores.items()):
        ws2.append([company,day,store,c['当日总计'],c['好评总数'],c['图文好评'],c['纯星好评'],c['差评总数'],c['图文差评'],c['纯星差评'],middle(c)]+[c[k] for k in CATEGORIES[4:]])
    for sheet in wb:
        sheet.freeze_panes = 'C2'; sheet.auto_filter.ref = sheet.dimensions; sheet.sheet_view.showGridLines = False
        for cell in sheet[1]:
            cell.font=Font(name='Microsoft YaHei',bold=True,color='FFFFFF',size=11)
            cell.fill=PatternFill('solid',fgColor='1F4E79'); cell.alignment=Alignment(vertical='center',wrap_text=True)
        sheet.row_dimensions[1].height=34
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value,str): cell.data_type='s'
                cell.font=Font(name='Microsoft YaHei',size=11); cell.alignment=Alignment(vertical='top',wrap_text=True)
                if cell.row%2==0: cell.fill=PatternFill('solid',fgColor='EEF3F8')
                if isinstance(cell.value,int): cell.number_format='0'
            sheet.row_dimensions[row[0].row].height=48 if sheet==ws else 36
        for i,cell in enumerate(sheet[1],1):
            sheet.column_dimensions[openpyxl.utils.get_column_letter(i)].width=40 if cell.value in ('公司名称','门店名称') else 64 if cell.value=='中间态明细' else 17
        sheet.print_title_rows='1:1'; sheet.sheet_properties.pageSetUpPr.fitToPage=True
        sheet.page_setup.orientation='landscape'; sheet.page_setup.paperSize=sheet.PAPERSIZE_A3; sheet.page_setup.fitToWidth=1; sheet.page_setup.fitToHeight=0
    wb.save(path); wb.close(); verify_stats(path, company, len(reviews))
    return {'days':len(daily),'store_days':len(stores),'good':sum(c['好评总数'] for c in daily.values()),'bad':sum(c['差评总数'] for c in daily.values()),'rows':len(reviews)}

def verify_stats(path, company, expected):
    import openpyxl
    wb=openpyxl.load_workbook(path,data_only=True)
    try:
        if wb.sheetnames != ['每日四象限统计','按门店每日明细']: raise FlowError('output-invalid','Unexpected worksheets')
        for sheet, total in [(wb.worksheets[0],'当日总计'),(wb.worksheets[1],'新增评总数')]:
            headers=[c.value for c in sheet[1]]
            if headers[0]!='公司名称': raise FlowError('output-invalid','Missing company column')
            records=list(sheet.iter_rows(min_row=2,values_only=True))
            if any(row[0]!=company for row in records): raise FlowError('output-invalid','Mixed company values')
            if sum(row[headers.index(total)] for row in records)!=expected: raise FlowError('output-invalid','Workbook totals differ from source')
    finally: wb.close()
