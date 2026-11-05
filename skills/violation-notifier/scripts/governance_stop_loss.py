# -*- coding: utf-8 -*-
"""Exact observed stop-loss notice parser. Produces facts/return command only; no UI."""
import re
from urllib.parse import urlsplit,parse_qs
import governance_dom as g
from governance_detail import nav,document
PATH='/p/govern_fulfillment_v2/violation_stop_lose_notice'
LABELS=['问题描述','处置方式','门店信息','整改建议','下发时间','通知书ID']
def parse(observation,row,opening,job):
    nav.scope(job);g.need(observation.get('source')=='local-dom-bridge' and observation.get('not_business_capture') is True,'stop-loss-observation-source-invalid');before=document(opening['before']);g.need(opening.get('state')=='confirmed','stop-loss-original-open-not-confirmed');p=g.records_page(before['tree'],start=job['start'],end_exclusive=job['end_exclusive']);source=g.one([r for r in p['rows'] if r['notice_id']==row['notice_id']],'stop-loss-original-before-row-not-unique');g.need(detail.same_source_row(source,row),'stop-loss-original-before-source-row-changed');expected={**g.detail_action(before['tree'],row['notice_id'],start=job['start'],end_exclusive=job['end_exclusive']),'tabId':observation['tab_id']};g.need(opening.get('command')==expected,'stop-loss-original-open-command-mismatch')
    detail.reply_matches(expected,opening.get('result',{}),before);result=opening.get('result',{});clicked=result.get('clicked',{});g.need(result.get('kind')=='navigation' and result.get('version')==nav.VERSION and clicked.get('selector')==expected['locator']['value'] and clicked.get('tag')=='a' and clicked.get('name')=='查看详情','stop-loss-original-open-reply-unverified')
    tab=nav.context([{'tabs':[observation['tab']]}],observation['tab_id'],job['groupid']);previous=nav.context([{'tabs':[before['tab']]}],observation['tab_id'],job['groupid']);g.need(tab.get('windowId')==previous.get('windowId'),'stop-loss-window-changed');u=urlsplit(tab['url']);q=parse_qs(u.query,keep_blank_values=True);g.need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path==PATH and not u.fragment and set(q) in ({'EnterFrom','TaskID','groupid'},{'EnterFrom','TaskID','groupid','life_account_biz_ids','life_biz_view_id'}) and (len(q)==3 or (q['life_account_biz_ids']==[''] and q['life_biz_view_id']==['22'])) and q['EnterFrom']==['home_violation_center'] and q['groupid']==[str(job['groupid'])] and len(q['TaskID'])==1 and re.fullmatch(r'ST[a-f0-9]{24}',q['TaskID'][0]),'stop-loss-public-route-unreviewed');tree=observation['tree'];g.need(tree.get('url')=='https://life.douyin.com'+PATH,'stop-loss-tree-route-mismatch');ns=g.nodes(tree);nav.identity(tree,job['identity']);root=g.one([n for n in ns if n.get('attributes',{}).get('id')=='root'],'stop-loss-page-root-not-unique');ns=list(g.walk(root))
    title=g.one([n for n in ns if n.get('tag')=='h1' and n.get('attributes',{}).get('class')=='title-AOxZNO'],'stop-loss-title-unreviewed');g.need(g.text(title)=='止损通知书','stop-loss-title-changed')
    container=g.one([n for n in ns if n.get('attributes',{}).get('class')=='container-VoTc0M horizontal-H4lO0z'],'stop-loss-fields-container-unreviewed');ch=container.get('children',[]);g.need(len(ch)==12 and [g.text(ch[i]) for i in range(0,12,2)]==LABELS and all(ch[i].get('attributes',{}).get('class')=='label-Uorjsh' and ch[i+1].get('attributes',{}).get('class')=='value-Hil7yf' for i in range(0,12,2)),'stop-loss-field-layout-unreviewed');fields=dict(zip(LABELS,ch[1::2]));values={k:g.text(v) for k,v in fields.items()}
    g.need(values['通知书ID']==row['notice_id'] and values['问题描述']==row['reason'] and values['处置方式']==row['disposal'],'stop-loss-source-notice-reason-disposal-mismatch');g.need(re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}',values['下发时间']) and values['下发时间'].split(' ')[0]==row['violation_date'],'stop-loss-source-notification-date-mismatch');store=re.fullmatch(re.escape(row['store_name'])+r'（ID：(\d{1,32})）',values['门店信息']);g.need(store,'stop-loss-source-store-mismatch')
    def leaf(c):return g.one([n for n in ns if n.get('attributes',{}).get('class')==c and not n.get('children')],'stop-loss-object-field-unreviewed:'+c)
    product,price,productid=leaf('title-QQ07Im'),leaf('price-y0Sfkt'),leaf('id_text-muNBHv');g.need(re.fullmatch(r'\d{1,32}',g.text(productid)) and row['object']==g.text(product)+' 商品 '+g.text(price)+' '+g.text(productid),'stop-loss-source-product-mismatch')
    improvement=g.one([n for n in ns if n.get('attributes',{}).get('class')=='card-XR0Ntz impre-Kyj22P'],'stop-loss-improvement-section-unreviewed');heading=g.one(g.classnodes(improvement,'title-h1ih39'),'stop-loss-improvement-heading-unreviewed');g.need(g.text(heading)=='我该如何避免','stop-loss-improvement-heading-changed');blocks=g.classnodes(improvement,'block-Fng6I3');g.need(len(blocks)==2 and [g.text(g.one(g.classnodes(b,'title-UUDoZz'),'stop-loss-advice-block-title-unreviewed')) for b in blocks]==['改善建议1','改善建议2'],'stop-loss-advice-blocks-unreviewed')
    first=g.one(g.classnodes(blocks[0],'sub-title-UGFgEk'),'stop-loss-advice-first-title-unreviewed');second=g.one(g.classnodes(blocks[1],'sub-title-UGFgEk'),'stop-loss-advice-second-title-unreviewed');body=g.one(g.classnodes(blocks[1],'content-RvpJDV'),'stop-loss-advice-second-body-unreviewed');g.need(g.text(first)=='开通体验补偿赔券' and g.text(second)=='建议缺货门店及时备货，做好用户接待' and g.text(body)==values['整改建议'],'stop-loss-observed-advice-text-changed')
    advice=[{'text':g.text(first),'selector':first['selector'],'source_block':'改善建议1','feature_action_executed':False},{'text':g.text(second)+'\n'+g.text(body),'selector':body['selector'],'heading_selector':second['selector'],'source_block':'改善建议2'}]
    button=g.one([n for n in ns if n.get('tag')=='button' and n.get('role')=='button' and 'btn-WHUasg' in g.cls(n) and g.text(n)=='查看其他处置'],'stop-loss-return-button-unreviewed');g.need(button.get('disabled') is not True,'stop-loss-return-button-disabled')
    facts={'schema':'governance-stop-loss-detail-v1','notice_id':row['notice_id'],'source_notice_row':row,'notification_time':values['下发时间'],'notification_time_label':'下发时间','notification_time_selector':fields['下发时间']['selector'],'reason':row['reason'],'object_type':'商品','object_name':g.text(product),'object_id':g.text(productid),'store_name':row['store_name'],'store_id':store.group(1),'disposals':[values['处置方式']],'effective_statuses':[],'detail_effectiveness_status_observed':False,'table_effectiveness_status':row['effective_status'],'public_recommendation':'\n'.join(p['text'] for p in advice),'public_recommendation_paragraphs':advice,'public_recommendation_selectors':[p['selector'] for p in advice],'public_recommendation_section':'我该如何避免','internal_rules_excluded_from_recommendation':True,'observed_at':observation['observed_at'],'source_binding':{'opening_before':opening['before'],'opening_command':opening['command'],'notification_id_selector':fields['通知书ID']['selector'],'store_selector':fields['门店信息']['selector'],'product_id_selector':productid['selector'],'task_id':q['TaskID'][0],'route':PATH},'submitted':False}
    if len(q)==5:
        g.need(row['reason']=='门店商品缺货' and row['effective_status']=='已结束' and row['rectification_status']=='-' and not body.get('children'),'stop-loss-business-context-status-or-advice-unreviewed')
        # New context is the same public template; the marketing feature is not
        # rectification advice. Legacy three-key facts stay byte-for-byte intact.
        public=[{'text':g.text(body),'selector':body['selector'],'heading_selector':second['selector'],'source_block':'改善建议2'}]
        facts.update(public_recommendation=g.text(body),public_recommendation_paragraphs=public,public_recommendation_selectors=[body['selector']],marketing_features_excluded_from_recommendation=True,detail_period_observed=False)
        facts['source_binding'].update(observed_business_context={'life_account_biz_ids':'','life_biz_view_id':'22'},observed_url=tab['url'])
    return facts,{'op':'click','tabId':observation['tab_id'],'kind':'navigation','locator':{'by':'selector','value':button['selector']}}

# A separate explicit stop-loss maintenance entry keeps ordinary drawer/records
# parsing strict. No operation below advances the original cursor.
import argparse,copy,fcntl,json
from pathlib import Path
import governance_detail as detail
class Runner(detail.Runner):
    def observe(self):
        ping=self.request({'op':'ping','tabId':self.tab})
        self.stop_loss_policy_ready=ping.get('governance_stop_loss_policy')=='public-notice-return-v1'
        return super().observe()
    def original(self):
        stage=self.s['stop_loss_stage'];old=document(stage['original_state']);detail.verify_completed(old,self.manifest,self.v,require_complete=False)
        g.need(old['phase']=='read-detail' and old['last_observation']==stage['original_observation'] and old['cursor']==self.s['cursor'] and old['details']==self.s['details'] and self.s['current']['normal_before']==old['current']['normal_before'],'stop-loss-original-checkpoint-changed')
        call=old['calls'][-1];g.need(call['before']==old['current']['normal_before'] and self.s['calls'][:len(old['calls'])]==old['calls'],'stop-loss-original-calls-changed')
        return old,self.v['query']['rows'][old['cursor']],call
    def stage(self,state_sha,observation_sha):
        if 'stop_loss_stage' not in self.s:
            g.need(nav.digest(self.file)==state_sha and self.s['phase']=='read-detail' and self.s['last_observation']['sha256']==observation_sha,'stop-loss-stage-original-checkpoint-mismatch')
            detail.verify_completed(self.s,self.manifest,self.v,require_complete=False);row=self.v['query']['rows'][self.s['cursor']];call=self.s['calls'][-1]
            g.need(call['before']==self.s['current']['normal_before'],'stop-loss-original-open-before-mismatch');parse(document(self.s['last_observation']),row,call,self.job)
            archive=self.file.parent/('stop-loss-original-'+state_sha+'.json');data=self.file.read_bytes()
            if archive.exists():g.need(archive.read_bytes()==data,'stop-loss-archive-conflict')
            else:
                with archive.open('xb') as f:f.write(data);f.flush();__import__('os').fsync(f.fileno())
            self.s['stop_loss_stage']={'schema':'stop-loss-readonly-stage-v1','original_state':detail.ref(archive),'original_observation':self.s['last_observation'],'expected_state_sha256':state_sha,'expected_observation_sha256':observation_sha,'started_at':nav.stamp()};self.s.update(phase='stop-loss-staging',hold=True,waiting_for='stop-loss-readonly-stage');self.save()
        stage=self.s['stop_loss_stage'];g.need(stage['expected_state_sha256']==state_sha and stage['expected_observation_sha256']==observation_sha,'stop-loss-stage-original-arguments-required')
        if self.s['phase']=='stop-loss-return-ready':return self.s
        g.need(self.s['phase']=='stop-loss-staging','stop-loss-stage-not-resumable');old,row,call=self.original();original_facts,original_return=parse(document(stage['original_observation']),row,call,self.job)
        self.observe();obs=self.s['last_observation'];facts,command=parse(document(obs),row,call,self.job);g.need(detail.same_facts(facts,original_facts) and command==original_return,'stop-loss-changed-during-readonly-stage')
        self.s['current'].update(detail_observation=obs,facts=facts,return_command=command);self.s.update(phase='stop-loss-return-ready',hold=True,waiting_for='supervisor-reviewed-single-stop-loss-return');self.s.pop('last_error',None);self.save();return self.s
    def return_once(self):
        g.need(self.s['phase']=='stop-loss-return-ready','stop-loss-return-already-issued-or-not-ready');old,row,call=self.original();self.observe();obs=self.s['last_observation'];facts,command=parse(document(obs),row,call,self.job)
        g.need(detail.same_facts(facts,self.s['current']['facts']) and command==self.s['current']['return_command'],'stop-loss-return-source-changed');g.need(self.stop_loss_policy_ready,'stop-loss-return-policy-not-loaded');self.s['current']['before_return']=obs
        self.action(command,'stop-loss-returned',obs);return self.inspect_return()
    def inspect_return(self):
        g.need(self.s['phase'] in ('stop-loss-returned','stop-loss-returned-unknown','stop-loss-return-route-hold'),'stop-loss-return-not-issued');old,row,opening=self.original();before=document(self.s['current']['before_return']);facts,command=parse(before,row,opening,self.job);g.need(detail.same_facts(facts,self.s['current']['facts']) and command==self.s['current']['return_command'],'stop-loss-saved-return-binding-changed');calls=self.s['calls'][len(old['calls']):];call=g.one(calls,'stop-loss-return-call-not-unique');g.need(call['command']==command and call['before']==self.s['current']['before_return'] and call['state'] in ('unknown','confirmed'),'stop-loss-return-call-changed');
        if call['state']=='confirmed':detail.reply_matches(command,call['result'],before)
        self.observe();obs=self.s['last_observation'];raw=document(obs)
        self.s['current']['return_observation']=obs;self.s['current']['return_route']={'origin':urlsplit(raw['tab']['url']).scheme+'://'+urlsplit(raw['tab']['url']).netloc,'path':urlsplit(raw['tab']['url']).path};self.s.update(phase='stop-loss-return-route-hold',hold=True,waiting_for='supervisor-review-observed-return-route');self.save();return self.s

    def finish_roundtrip(self,state_sha):
        g.need(nav.digest(self.file)==state_sha and self.s['phase']=='stop-loss-return-route-hold','stop-loss-finish-original-checkpoint-required');old,row,opening=self.original();before=document(self.s['current']['return_observation']);page=detail.normal_page(before['tree'],self.job,self.v['query']);original_page=detail.normal_page(document(self.s['current']['normal_before'])['tree'],self.job,self.v['query']);g.need(page['page']==original_page['page'] and row in page['rows'],'stop-loss-finish-original-notice-not-returned')
        # This exact observed route is already the original range; no recovery input.
        self.observe();obs=self.s['last_observation'];fresh=detail.normal_page(document(obs)['tree'],self.job,self.v['query']);g.need(fresh['page']==page['page'] and row in fresh['rows'],'stop-loss-finish-fresh-original-notice-mismatch')
        entry=copy.deepcopy(self.s['current']);entry.update(state='complete',completion_kind='stop-loss-roundtrip-v1',stage_evidence=copy.deepcopy(self.s['stop_loss_stage']),normal_after=obs);verify_entry(entry,self.s,self.manifest,self.v,row)
        self.s['details'].append(entry);self.s.update(cursor=self.s['cursor']+1,current=None,phase='normal');self.s.pop('stop_loss_stage');self.s.pop('hold',None);self.s.pop('waiting_for',None);self.s.pop('last_error',None)
        if self.s['cursor']==len(self.v['query']['rows']):self.s['phase']='complete'
        detail.verify_completed(self.s,self.manifest,self.v,require_complete=self.s['phase']=='complete');self.save();return self.s

def verify_entry(entry,state,manifest,inputs,row):
    """Verify a completed observed stop-loss roundtrip without accepting drawer aliases."""
    g.need(entry.get('completion_kind')=='stop-loss-roundtrip-v1' and entry.get('state')=='complete','stop-loss-completed-kind-invalid')
    stage=entry['stage_evidence'];old=document(stage['original_state']);g.need(stage.get('schema')=='stop-loss-readonly-stage-v1' and stage['original_state']['sha256']==stage['expected_state_sha256'] and stage['original_observation']['sha256']==stage['expected_observation_sha256'] and old['phase']=='read-detail' and old['last_observation']==stage['original_observation'],'stop-loss-completed-original-state-invalid')
    detail.verify_completed(old,manifest,inputs,require_complete=False);index=old['cursor'];g.need(inputs['query']['rows'][index]==row and old['details']==state['details'][:index] and old['current']['normal_before']==entry['normal_before'] and state['calls'][:len(old['calls'])]==old['calls'],'stop-loss-completed-prefix-changed')
    opening=old['calls'][-1];g.need(opening['before']==entry['normal_before'],'stop-loss-completed-open-before-changed');original,original_return=parse(document(stage['original_observation']),row,opening,inputs['job']);facts,command=parse(document(entry['detail_observation']),row,opening,inputs['job']);recent,recent_command=parse(document(entry['before_return']),row,opening,inputs['job'])
    g.need(facts==entry['facts'] and detail.same_facts(original,facts) and detail.same_facts(recent,facts) and command==recent_command==original_return==entry['return_command'],'stop-loss-completed-detail-changed')
    closing=state['calls'][len(old['calls'])];g.need(closing['state']=='confirmed' and closing['command']==command and closing['before']==entry['before_return'],'stop-loss-completed-return-not-confirmed');detail.reply_matches(command,closing['result'],document(entry['before_return']))
    g.need(len([c for c in state['calls'] if c.get('command')==command and c.get('before')==entry['before_return']])==1,'stop-loss-completed-return-not-unique')
    observations=[document(entry[k]) for k in ('normal_before','detail_observation','before_return','return_observation','normal_after')];tab=observations[0]['tab'];times=[]
    for raw in observations:
        g.need(raw.get('source')=='local-dom-bridge' and raw.get('not_business_capture') is True and raw.get('tab_id')==manifest['tab_id'],'stop-loss-roundtrip-observation-source-changed');current=nav.context([{'tabs':[raw['tab']]}],manifest['tab_id'],inputs['job']['groupid']);g.need(current.get('windowId')==tab.get('windowId') and raw['tree'].get('url')=='https://life.douyin.com'+urlsplit(current['url']).path,'stop-loss-roundtrip-scope-changed');nav.identity(raw['tree'],inputs['job']['identity']);at=__import__('datetime').datetime.fromisoformat(raw['observed_at']);g.need(at.utcoffset() is not None,'stop-loss-roundtrip-time-required');times.append(at)
    g.need(times==sorted(times),'stop-loss-roundtrip-time-reversed')
    before=detail.normal_page(observations[0]['tree'],inputs['job'],inputs['query'])
    for raw in observations[-2:]:
        page=detail.normal_page(raw['tree'],inputs['job'],inputs['query']);g.need(page['page']==before['page'] and row in page['rows'],'stop-loss-roundtrip-original-page-notice-not-restored')
    g.need(entry.get('return_route')=={'origin':'https://life.douyin.com','path':g.RECORDS},'stop-loss-completed-return-route-changed');return facts

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('verb',choices=['stage','return-once','inspect-return','finish-roundtrip']);parser.add_argument('--manifest',required=True);parser.add_argument('--expected-state-sha256');parser.add_argument('--expected-last-observation-sha256');args=parser.parse_args()
    try:
        m=json.loads(Path(args.manifest).read_text());v=detail.inputs(m);folder=Path(m['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/nav.tag(v['job'])
        g.need((folder/'state.json').is_file(),'stop-loss-original-state-required')
        with (folder/'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);runner=Runner(m)
            if args.verb=='stage':g.need(args.expected_state_sha256 and args.expected_last_observation_sha256,'stop-loss-original-hashes-required');runner.stage(args.expected_state_sha256,args.expected_last_observation_sha256)
            elif args.verb=='return-once':runner.return_once()
            elif args.verb=='finish-roundtrip':g.need(args.expected_state_sha256,'stop-loss-finish-checkpoint-hash-required');runner.finish_roundtrip(args.expected_state_sha256)
            else:runner.inspect_return()
            print(json.dumps({'ok':True,'phase':runner.s['phase'],'cursor':runner.s['cursor'],'completed_details':len(runner.s['details']),'state':str(runner.file),'state_sha256':nav.digest(runner.file),'waiting_for':runner.s.get('waiting_for'),'detail_progress_changed':args.verb=='finish-roundtrip','business_progress_changed':False},ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e),'business_progress_changed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
