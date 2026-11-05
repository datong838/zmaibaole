"""Finite public-notice wording, not AI or human review. Unknown pairs fail."""
import hashlib,json,re
KIND='violation-deterministic-copy-v1'
VERSION='reviewed-public-notice-template-v1'
# Exact reason/object pairs come from reviewed archived notices and this batch.
TEMPLATES={
 ('门店近90天不接待问题超标','门店'):'近期门店接待情况建议重点关注',
 ('门店近90天三率超标','门店'):'近期门店服务相关指标建议进一步改善',
 ('三率超标','门店'):'门店服务相关指标建议进一步改善',
 ('商品资质缺失','商品'):'相关商品的资质信息有待补充完善',
 ('宣传套餐内容与商详页不一致','直播'):'直播介绍与商品详情内容建议保持一致',
 ('涉及绝对化用语','直播'):'直播中的部分表述建议调整得更客观、准确',
 ('低质引流品履约差处置','商品'):'相关商品的履约表现建议进一步改善',
 ('直播间中长时间无互动','直播'):'直播互动安排建议进一步完善',
 ('门店商品缺货','商品'):'相关商品的库存与供给信息建议及时核对',
 ('以不当方式引导用户私下建立联系并交易','直播'):'直播联系及交易引导方式建议规范调整',
 ('店铺存在利诱好评行为','门店'):'门店的评价引导方式建议规范调整',
 ('内容涉及不友善用语','评价'):'相关商家回复的措辞建议更友善',
}
NEW_TEMPLATES={
 ('即送商家三率超标','商家'):'商家即送服务相关指标建议进一步改善',
 ('所售食品存在安全风险','门店'):'相关食品安全情况需要尽快核查',
 ('可配门店覆盖率管控','商品'):'商品可配送门店覆盖情况建议及时核对',
 ('门面照片拍摄不完整','门店'):'门面照片建议按平台展示要求补充完善',
 ('门店经营异常管控','门店'):'门店营业状态建议及时核对',
 ('门店不接单率超标','门店'):'门店接单服务相关指标建议进一步改善',
 ('温馨提醒：锚点类型选择有误','短视频'):'温馨提醒：锚点类型选择有误',
}

FORBIDDEN=('规则编号','规则依据','内部规则','判定明细','风控命中','算法判定','恶意商家','欺诈商家','垃圾信息发布者')
def need(ok,code):
 if not ok:raise ValueError(code)
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def document(source_sha,records):
 need(isinstance(source_sha,str) and re.fullmatch('[a-f0-9]{64}',source_sha),'template-source-sha-required')
 need(type(records) is list and records,'template-empty-records')
 ids=[r.get('notice_id') for r in records];need(all(type(i) is str and i for i in ids) and len(ids)==len(set(ids)),'template-notice-ids-invalid')
 forbidden=list(FORBIDDEN)+[r[k] for r in records for k in ('internal_rule_basis','internal_judgment_detail') if r.get(k)]
 templates=dict(TEMPLATES)
 if any((r.get('reason'),r.get('object_type')) in NEW_TEMPLATES for r in records):templates.update(NEW_TEMPLATES)
 items=[]
 for r in records:
  pair=(r.get('reason'),r.get('object_type'));need(pair in templates,'unsupported-public-notice-template')
  if pair==('温馨提醒：锚点类型选择有误','短视频'):need(r.get('notice_kind')=='platform-anchor-reminder' and r.get('not_business_violation') is True and r.get('platform_non_violation_statement')=='该情况不属于违规，不会影响您的视频流量和账号。','template-anchor-reminder-proof-required')
  if pair==('内容涉及不友善用语','评价'):need(r.get('object_subtype')=='商家回复','unsupported-public-notice-template')
  need(r.get('detail_read') is True and all(type(r.get(k)) is str and r[k].strip() for k in ('subject','object_name','effectiveness_status','public_recommendation')),'template-public-facts-missing')
  need(type(r.get('actions')) is list and r['actions'] and all(type(a) is str and a.strip() for a in r['actions']),'template-actions-missing')
  reason=templates[pair]+'。'
  recommendation='烦请参考页面建议：'+r['public_recommendation']
  need(not any(word in reason+recommendation for word in forbidden),'template-internal-or-accusatory-text')
  items.append({'notice_id':r['notice_id'],'gentle_reason':reason,'recommendation':recommendation})
 rules=[{'reason':a,'object_type':b,'wording':v} for (a,b),v in sorted(templates.items())]
 return {'kind':KIND,'source_sha256':source_sha,'producer':{'method':VERSION,'rules_sha256':digest(rules),'facts_sha256':digest([{k:r.get(k) for k in ('notice_id','subject','reason','object_type','object_subtype','object_name','actions','effectiveness_status','action_details','disposal_stage_text','public_recommendation')} for r in records])},'items':items}
