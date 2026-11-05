#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render per-round and per-incident records from supervision receipts; no UI."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/测试记录'
ZONE = ZoneInfo('Asia/Shanghai')
SOURCE = ROOT / 'runtime/supervision/continuous-rehearsal.json'
NOTES = {
    'violation-anchor-epoch-pixel-quality-unresolved-history': ('锚点截图的全局epoch历史未能自动认证', '原程序已生成真实锚点PNG，几何前后相同，但公共证明仅全局epoch从1531变为1533；变化原因与捕图区间历史仍未证实，原质量程序在OCR前拒绝。不能用当前只读状态回溯证明过去，也不把该图当数据行证据。', '已发布独立五列表头像素核验合同，保留原unresolved证明和日期片段披露，历史与数据行认证均为false。整带识别与固定边距实验失败均保留；字符范围仅定位，独立局部识别在原0.5门槛下精确通过。已封存缓存将经完整native/source/crop/owner程序复核，0新OCR后才普通accept；当前不把像素通过当列表数据行或四交付完成。', '区分像素字段可核验与DOM变化历史不可证明；有图的已知质量等待不能走未知截图重拍路径，不能改原证明凑全等。冷启动测试必须从真实producer入口开始，不以测试预热掩盖依赖闭包问题。'),
    'reboot-capture-canonical-navigation-root': ('重启后捕图校验仍读取旧导航目录', '已验证重启profile指向当前tab666/window665，但共享捕图guard仍硬读原source目录的旧279/278导航profile并执行全等比较，正常拒绝。旧URL门当时已过且没有新focus输入或PNG；后续0005正式续跑已生成原生锚点截图。', '仅reboot-derived类型复用既有RP.nav_root完整验证，普通路径保持原目录；profile、scope、binding和operations完成校验原样，capture与retake两个消费者共享修复。01:18:44.273843Z原生截图完成证明该门已跨过；后续epoch质量等待另列问题17。', '正常导航与捕图/复拍的导航根目录选择必须使用同一已验证profile合同；覆盖真实重启profile、普通profile、未知操作、缺新目录拒fallback及完整旧完成证明兼容。'),
    'source-bound-capture-focus-url-lifecycle': ('环境恢复后的URL参数触发旧焦点证据绑定拒绝', '原环境已完整核验同source的公司、DOM日期和记录事实并自动续旧违规；焦点日志只因URL新增平台时间与入口参数而拒绝，其余source/profile/chain/PID/tab/window完全相同。URL默认周范围不能当作DOM实际筛选日期。', '保旧焦点journal、reads、events和原业务key；只在完整环境证明和严格共同scope/route/query意义下建立独立焦点证据代次，fresh观察后仍过原native/viewport守卫。已按受审两源发布，正式恢复仍须原任务收据；不重环境或未知输入。', '恢复导航可能改变URL表示；焦点证据生命周期须明确原源、完整环境证明和新观察的关系，覆盖query风险、跨公司/窗口、unknown/nativepending及库存闭包，不能简单忽略全部URL参数。'),
    'handoff-daemon-business-python-dependency-boundary': ('自动旧任务交接使用了缺依赖的调度解释器', '前两流已完成，程序已恢复旧违规owner并落0003源码修复；环境恢复却直接在系统调度Python中import业务ports，缺PIL，尚未创建环境输入意图。该问题属于环境解释器边界，不是违规新业务操作失败。', '应由已配置且具业务依赖的固定config.python子进程执行原environment step/verify，原grant/event与逐RPC日志不变；未知不得换key重发，不pip或手改租约。常驻模块缓存必须通过既有受控生命周期更新后才算部署有效。', '环境预检须实际覆盖调度解释器到业务解释器的调用边界，不能只在venv运行TEMP测试；同grant进程收据、原0003与已完成报告兼容均应验证。'),
    'complaint-completed-report-compact-failed-membership': ('业务完成后的报告误读分散失败调用列表', '已审历史失败子调用分布在0、1、6、7、9、10，报告代码把compact列表按当前index取值，误将第6次历史失败当正常rc0。业务已完成，不是新业务失败。', '正常报告改为完整call与唯一授权launch/result引用匹配；未授权或重复例外仍拒。已complete父流程在浏览器和父调用前直接纯报告收尾，原attempt16现已完成report/coordfinish/harvest。原parent/engine/completion与双outer完全保持，无parentrun/accept/浏览器scope命令，不重业务finish/发送。', '完成报告测试必须包含非连续历史失败列表和真实已完成工单；业务完成、调度harvest与整轮完成分别记录，不能因报告错再重跑业务。'),
    'bridge-readonly-lone-surrogate-encoding': ('只读桥返回数据的Unicode编码失败', '上海切换与评价导航已确认，读取筛选scope时JSON响应包含不能直接UTF-8编码的孤立surrogate，未进入筛选输入。原失败payload未保存，不能断言具体emoji来源。', 'JSON传输和本地证据统一转义保留字符数据；原桥同票据只重载一次，新PID/启动身份、loopback健康和扩展就绪已核。原7输入、树和双outer保留；原phase11真实tree/scope已成功，07:12:35.335340由go记录恢复，程序进入recordsProfileRequired。整流仍继续。', 'JSON传输须安全表示完整Unicode及孤立surrogate；测试成对emoji、孤立高低surrogate、嵌套响应和原始语义，错误路径也保只读边界。'),
    'complaint-confirm-snapshot-anchor-name': (
        '公司确认快照与只读恢复锚点命名不一致',
        '正常producer已让confirmSwitch树使用recovered-UUID不可变文件，而consumer仍只允许固定NNNN-confirmSwitch.json，scope另用base前缀，导致真实完整证据被拒；不是确认失败或未知输入。',
        '只允许同目录同revision的旧base或recovered32hex树，以scope.tree与真实lasttree内容绑定唯一scope；保beforeafter、身份、scope和来源校验。已正式只读恢复，4confirmed输入没有重复；后续原程序正常导航至评价筛选，新Unicode只读问题另列12。原readonly恢复使用独立精确语义合同，不冒充transport错误。',
        'producer改不可变命名时同时检查所有正常consumer；不要从tree.stem猜scope命名，须以内容/原引用唯一绑定，覆盖旧新命名及多scope/坏路径/unknown负例。'),
    'complaint-historical-exact-recheck-code-pin': ('历史exact复查的旧源码图被当前执行门拒绝', 'prepare在判定新旧day/version前，对旧active manifest直接执行live current11校验；runner已审升级后历史原e96与当前a1f不同。并非当前页面或新输入失败。', '已将旧完成/applied历史数据核验和新current11执行分开，两旧源码只读归档不执行。首次补丁后又暴露恢复证明把会追加reads的导航journal当固定文件；旧de78完整bytes未封存，未假造原hash，以原成功准入CLI及固定旧F源码侧证原前置，另冻结fe86完整snapshot并严格只准只读增长。原currentday manifest和激活不回退，06:42:24.505094实际第一案已完成并apply；整流仍继续。', '源码变化核查所有历史active消费者，不能只验v3而漏exact。可变journal必须封存准入快照并测试后续正常增长、完成重验；不能把前置准入等同永久live文件hash，缺旧raw需明确审计侧证，禁止重构冒充。live pin/未知输入不放宽，不重导出/已确认激活。'),
    'complaint-capture-download-panel-title-mismatch': (
        '投诉截图前下载浮层挡住目标窗口',
        '原采集和导出已完成。截图前实际CG首窗是同一Chrome进程的近期下载记录浮层，PID正确但标题不符；原截图守卫在native意图和PNG之前拒绝。较早仅证实拦截弹窗提示气泡消失，不是近期下载面板关闭，不能代替当前窗口事实。',
        '同PID错误标题不算ready；原exact标签激活确认后不重发。保旧unknown状态和同key，已知pre-native失败使用新观察旁支。原程序已只读确认窗口恢复并产出真实区域截图；本次没有调用AXRaise，不能宣称窗口提升动作已经真机验证。后续图片QA另见问题08。',
        '检查当次CG/AX标题、窗口、原下载关闭时间与截图边界库存；保原源和已确认采集，不重导出、不把PID相同当窗口就绪、未知动作不重发。'),
    'complaint-region-qa-rating-locator': (
        '评价图片QA首轮评分定位分组不一致',
        '首卡OCR分组为“• 非常差”，第二卡为“00• 非常差”；首轮精确匹配整段文字失败，尚未进入二次局部识别。这不是二次事实置信度低。两卡现已分别通过正式程序核验并注册，后续结果抽屉问题另见09。',
        '首卡有限评分符号修复和同图二次识别已通过正式Q.create/verify。第二卡暴露同根因变体，改用OCR已提供的唯一精确评分query range作为定位hint，并核对评分列几何；二次ROI评分/正文/门店/顾客/操作的事实核验门槛保持。正式同图核验和首卡旧证明兼容验证已通过。原图、旧失败缓存与首卡已通过证据均保留，不重拍。',
        '首轮只负责定位，不能把OCR整段分组当评分事实。覆盖心形误识/装饰与评分同run、精确query range缺失或不唯一、二次事实不符；更新Q还须验证旧已注册attestation有效，避免修第二卡破坏首卡。'),
    'complaint-result-drawer-empty-loading': (
        '查看已有投诉结果时过早解析空抽屉',
        '查看投诉结果已确认打开，原正常卡片门店和顾客匹配；随后抽屉仅出现投诉评价标题及空body，门店/顾客/正文节点均为0。严格parser过早执行而报result-review-mismatch:store，并非实际观察到另一家门店。',
        '仅在已确认opened、原scope及身份相同、唯一精确空骨架时有限只读等待；ready立即解析，非空不符仍拒，等待耗尽保存超时证据。不重复open。三正式消费者共同合同已发布，原98a8在06:07:19程序真实完成；原confirmed open没有重复。实际续读已ready，有限退避由针对测试覆盖，不冒称真机额外触发。',
        '区别空加载和真实字段冲突；所有正式读取结果入口共用同一等待合同。保原confirmed open、原树、key和计时，未知输入不重放；已完成历史记录只验证，不执行旧代码。'),
    'daily-explicit-weekend-init-nonbatch': (
        '周末初始化返回非批次对象',
        '10月24日是周六。flow 返回 today_not_workday，父程序仍按 batch 核验，报 daily-timing-batch-binding-invalid；此时未创建采集批次、未操作页面。',
        '正式工单已核准公司游标至截止日的范围，初始化按此范围执行；普通无工单入口保留工作日策略。精确恢复零效果失败，保留原失败 child、工单和计时。',
        '下一轮先测试显式周末补做、普通工作日和普通周末日历入口；不得靠模型临时加参数。'),
    'daily-confirm-company-loading-zero-button': (
        '公司选择后加载中没有确认按钮',
        '选择公司已 confirmed；紧接着 modal 仍显示 loading，确认按钮实际为0。旧错误 semantic-locator-not-unique 未区分0和多个，程序立即退出。',
        '仅对已验证的选择后加载状态进行有限只读退避；就绪立即执行。允许严格目标公司已直接完成的分支。原5次确认动作、失败树和操作 key 保留。',
        '复现时查看按钮实际数量、loading证据、最后 confirmed 操作；不能重做 chooseCompany。测试加载至确认、直接完成、等待耗尽及真正歧义。'),
    'daily-return-known-merchant-query-scope-rejected': (
        '返回公司复核时拒绝合法商户参数',
        '两公司采集完成后返回烟台。确认已 confirmed，旧上海 management URL 带 groupid、life_biz_view_id=22、空 life_account_biz_ids，只读 helper 错将其拒为 group-risk；adapter 正确拒绝把语义错误当传输重试。',
        '精确接受已观测 management 三参数格式及原始/目标 groupid；重复、未知参数、外域和错误窗口仍拒。独立只读恢复原语义 hold，不重确认或重采集。',
        '按原 sample 核对完整 URL 和参数列表；不得泛化所有 query。正向 pending 有限退避，ready 不等待；语义风险不当作网络故障重试。'),
    'daily-wecom-initial-main-window-unavailable': (
        '企业微信主窗和初始会话分区识别',
        '首 sender 在 locate 阶段失败，0输入。真实同Host诊断证明进程、权限和唯一主窗口存在，旧结构强制要求已选会话及输入区。修复后 attempt29 又被全窗 TextArea/help 检查拦截；该次树未保存，具体触发节点未知。',
        '按必要导航拓扑识别主窗，locate 可先搜索/选择目标，verify/stage/send 仍需完整目标和输入区。仅排除已识别导航表下不可编辑预览；非表或可编辑输入仍拒。失败时保存已读树的脱敏结构摘要。',
        '环境预检除权限还要验证可用主窗。复现从同Host进程/窗口结构和原 sender intent 查起；先区分未选会话、会话预览与实际 composer。未知发送结果不能换 key 重发。'),
    'daily-shanghai-prepaste-frontmost-unverified': (
        '上海文件粘贴前未证实应用在前台',
        '烟台3条测试群客户端消息已确认；上海首份Excel已核对目标群，composer相等，但应用前台未被证实，程序在粘贴之前停止。没有粘贴、发送意图或发送。',
        '沿既有粘贴前合同只读重验原PID、目标群与空草稿后，原key正常续跑；上海首条于00:44:53客户端确认，六部分于00:45:34全部确认。未改焦点源码或弱化守卫，烟台前三条未重发。',
        '区分输入区匹配、系统应用前台、激活请求被接受三类证据。前三条已确认消息不重发，上海沿原sender/key恢复，不能弱化焦点守卫。'),
    'completed-operator-not-woken-by-send-message': (
        '已完成岗位没有被普通消息唤醒',
        '执行岗报告上海故障后自然完成。主任用 send_message 继续交代，但该调用不会启动已完成岗位；之后检查实际状态，才用 followup_task 唤醒。该等待属于调度续办延迟，不是新增业务故障。',
        '新工作一律使用 followup_task，运行中的岗位也可安全投递；send_message 只用于已确认工作中的进展沟通。状态读取可能与岗位结束竞争，必须取得新任务确认或真实程序句柄才算启动。仍由唯一执行岗持有资源，不重复启动业务。',
        '不能把已发消息当成任务正在执行。必须取得实际运行状态或程序句柄；本次未记录原始等待起点，耗时保持未知。'),
}
CODE_FILES = {
    'registration-pure-scope-repeated-historical-proof-validation': ['skills/violation-notifier/scripts/violation_reboot_continuation.py', 'skills/violation-notifier/scripts/registration_validation.py'],
    'violation-row-pixel-quality-global-epoch-only-race': ['skills/violation-notifier/scripts/program_epoch_rows_quality.py', 'skills/violation-notifier/scripts/rows_character_range_quality.py', 'skills/violation-notifier/scripts/violation_execution_ports.py', 'skills/violation-notifier/scripts/region_frame_capture.py'],
    'complaint-result-drawer-empty-loading': ['skills/negative-review-complaints/scripts/existing_result_runner.py', 'skills/negative-review-complaints/scripts/unbound_case_runner.py', 'skills/negative-review-complaints/scripts/case_alias_v3.py'],
    'complaint-region-qa-rating-locator': ['skills/negative-review-complaints/scripts/program_review_quality.py', 'skills/negative-review-complaints/scripts/review_capture_focus.py'],
    'complaint-capture-download-panel-title-mismatch': ['skills/negative-review-complaints/scripts/review_capture_focus.py', 'skills/chrome-dom-export/scripts/native_window_capture.py'],
    'daily-explicit-weekend-init-nonbatch': ['skills/daily-comment-stats/scripts/daily_timed_run.py', 'skills/workshop-director/scripts/daily_execution_launcher.py', 'skills/workshop-director/scripts/daily_completed_archive.py'],
    'daily-confirm-company-loading-zero-button': ['skills/douyin-laike-operator/scripts/bridge-workflow.py'],
    'daily-return-known-merchant-query-scope-rejected': ['skills/douyin-laike-operator/scripts/switch_read_recovery.py'],
    'daily-wecom-initial-main-window-unavailable': ['skills/wecom-messenger/scripts/main_window.py', 'skills/wecom-messenger/scripts/ui.py', 'skills/wecom-messenger/scripts/messenger.py', 'packages/workshop-director/workshop_director/adapters.py'],
    'daily-shanghai-prepaste-frontmost-unverified': ['skills/wecom-messenger/scripts/native.py', 'skills/wecom-messenger/scripts/messenger.py', 'packages/workshop-director/workshop_director/adapters.py'],
}


def stamp(value):
    if not value:
        return '未记录'
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(ZONE).strftime('%Y-%m-%d %H:%M:%S %z')


def link(value):
    if not value:
        return '无'
    if isinstance(value, dict) and value.get('path'):
        p = Path(value['path'])
        if not p.is_absolute():
            p = ROOT / p
        label = p.name
        sha = value.get('sha256')
        return f'[{label}](<{p}>)' + (f' SHA256 `{sha}`' if sha else '')
    return str(value)


def refs(value):
    if isinstance(value, dict):
        if value.get('path'):
            yield value
        else:
            for child in value.values():
                yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n')


def main():
    state = json.loads(SOURCE.read_text())
    now = datetime.now(ZONE)
    rounds = state.get('rounds', [])
    index = ['# 三工作流测试记录', '',
             '每次完整串行演练建立一份轮次记录；同轮中的故障续跑另建问题记录。调度器的正常分段 continuation 不冒称新的完整测试轮次。', '',
             '原始收据与 JSON 台账保留，本文档由固定脚本生成；发现、诊断、测试通过、部署和真实恢复分别记录。没有证据的时间不补造，离线通过不等于真机通过。', '',
             '更新命令：`python3 scripts/supervision/render_round_records.py`', '',
             '## 轮次索引', '']
    for number, run in enumerate(rounds, 1):
        directory = OUT / f'round-{number:03d}'
        if run.get('record_sealed') and (directory / 'README.md').exists():
            index.append(f'- [第{number}轮 三工作流实操](round-{number:03d}/README.md)：已封存，不自动改写。')
            continue
        issues = [i for i in state.get('issues', []) if not i.get('same_root_issue_as') and i.get('round_number', 1) == number]
        # New runtime categories must retain full issue records. Only explicit
        # preparation and uncategorized historical carryovers belong below.
        live = [i for i in issues if i.get('category') not in (None, 'environment-preparation')]
        prep = [i for i in issues if i not in live]
        page = ['# 第%d轮 三工作流完整实操' % number, '',
                f'记录更新时间：{stamp(now.isoformat())}。本轮状态：`{run.get("state", "未知")}`。', '',
                '## 范围和执行约束', '',
                f'- 计划：`{run.get("plan_id")}`；原首任务：`{run.get("first_task_id")}`。',
                '- 顺序：每日评价统计 → 差评投诉草稿和已有投诉复查 → 违规汇总通知。',
                '- 批准范围：' + '；'.join(f'{name}：`{value}`' for name, value in run.get('ranges', {}).items()) + '。跨日不修改已经启动的工单。',
                '- 最终只发“测试群请忽略”；不提交真实投诉、不发生产群。程序实操，监理只检查、修复协调和重新派工。',
                '- 禁止CDP、DevTools、调试端口、浏览器重启、凭据读取和像素定位。', '',
                '## 计时', '',
                f'- 环境准备开始：{stamp(state.get("started_at"))}。',
                f'- 环境READY：{stamp(state.get("environment_ready_at"))}；准备墙钟 {state.get("environment_preparation_wall_seconds", "未记录")} 秒，单列。',
                f'- 正式首程序启动：{stamp(run.get("started_at"))}。恢复和续跑保留这个起点，不清零。',
                '- 本轮尚无全三流最终结束证据，不计算虚假完成耗时，也不声称30秒达标。', '',
                f'首程序原件：{link(run.get("first_program_evidence"))}', '',
                '## 当前发送证据', '', run.get('test_delivery_status', '以原始收据为准，尚无全轮完成结论。'), '', link(run.get('latest_test_delivery_evidence')), '',
                '## 本轮问题索引', '',
                '| 记录 | 发现时间 | 当前证据状态 |', '| --- | --- | --- |']
        for n, issue in enumerate(live, 1):
            title, cause, fix, prevention = NOTES.get(issue['id'], (issue.get('title', issue['id']), issue.get('problem', ''), issue.get('solution', '待查明'), '按原始证据定位，不盲目重试。'))
            target = directory / f'issue-{n:02d}-{issue["id"]}.md'
            page.append(f'| [{n:02d} {title}]({target.name}) | {stamp(issue.get("observed_at"))} | `{issue.get("status")}` |')
            detail = [f'# 第{number}轮 问题{n:02d} {title}', '',
                      f'问题标识：`{issue["id"]}`。状态：`{issue.get("status")}`。', '',
                      '## 现象和原因', '', cause, '',
                      '## 修复和下一轮避免方式', '', fix, '', prevention, '',
                      '## 时间与实际恢复', '',
                      '| 事件 | 时间或耗时 |', '| --- | --- |']
            for label, key in [('发现', 'observed_at'), ('诊断', 'diagnosed_at'), ('候选完成', 'fix_ready_at'), ('正式部署', 'deployed_at'), ('真实恢复', 'recovery_complete_at')]:
                detail.append(f'| {label} | {stamp(issue.get(key))} |')
            duration = issue.get('solution_seconds')
            detail += [f'| 发现至已记录恢复墙钟 | {str(round(duration, 3)) + " 秒" if duration is not None else "尚未记录完整恢复，不填估值"} |', '',
                       issue.get('solution_timing_note', issue.get('recovery_timing_note', '以上为开发和实操墙钟，不能视作纯编码耗时或30秒正式性能。')), '',
                       '## 测试和复发判断', '',
                       '离线测试、发布和真机恢复分别看原件。不同错误不得合并为“又是同一个问题”；相同根因复现必须在本页追加实机尝试证据，保留旧失败。', '']
            if issue.get('resolution_checkpoints'):
                detail += ['### 分阶段解决状态', '', '| 阶段 | 状态 | 证据 |', '| --- | --- | --- |']
                for item in issue['resolution_checkpoints']:
                    detail.append('| ' + ' | '.join([str(item.get('stage', '')).replace('|', '\\|'), str(item.get('status', '')).replace('|', '\\|'), link(item.get('evidence'))]) + ' |')
                detail.append('')
            if issue.get('test_records'):
                detail += ['### 逐次验证记录（保留失败）', '', '| 验证/步骤 | 结果 | 秒 | 说明 | 原件 |', '| --- | --- | --- | --- | --- |']
                for item in issue['test_records']:
                    cells = [str(item.get('name', '')), str(item.get('result', '')), str(item.get('seconds')) if item.get('seconds') is not None else '未单记', str(item.get('note', '')), link(item.get('artifact'))]
                    detail.append('| ' + ' | '.join(c.replace('|', '\\|').replace('\n', ' ') for c in cells) + ' |')
                detail.append('')
            if issue.get('observation_interval'):
                interval = issue['observation_interval']
                detail += [f'发现时间仅能界定在 {stamp(interval.get("start"))} 至 {stamp(interval.get("end"))}，不是精确故障时戳。', '']
            if issue.get('live_followup_failure'):
                follow = issue['live_followup_failure']
                detail += [f'后续 attempt {follow.get("attempt")}：`{follow.get("error")}`；具体触发节点：{follow.get("specific_trigger_node", "待核")}。原件 {link(follow.get("evidence"))}。', '']
            if issue.get('attempt_timeline'):
                detail += ['### 本问题的实机尝试', '', '| attempt | 结果 |', '| --- | --- |']
                detail += [f'| {item["attempt"]} | {item["result"]} |' for item in issue['attempt_timeline']]
                detail.append('')
            if issue.get('recurrences'):
                detail += ['### 同根因复现追加', '']
                for repeat in issue['recurrences']:
                    detail += [f"- 第{repeat.get('occurrence')}次；记录时间：{stamp(repeat.get('recorded_at'))}；岗位：`{repeat.get('target')}`。", f"  {repeat.get('stage')} {repeat.get('actual_recovery')}", f"  原等待起点：{stamp(repeat.get('original_wait_onset_at'))}；等待耗时：{repeat.get('delay_seconds') if repeat.get('delay_seconds') is not None else '未知，不补造'}。"]
                detail.append('')
            if issue.get('diagnosis_corrections'):
                detail += ['### 同轮诊断更正', '']
                for correction in issue['diagnosis_corrections']:
                    detail += [f"- {stamp(correction.get('at'))}：{correction.get('finding')}", f"  避免复发：{correction.get('prevention')}；原件 {link(correction.get('evidence'))}。"]
                detail.append('')
            detail += ['## 原始证据', '']
            seen = set()
            for reference in refs(issue):
                identity = (reference['path'], reference.get('sha256'))
                if identity not in seen:
                    detail.append('- ' + link(reference)); seen.add(identity)
            detail += ['', '## 下次排查的代码入口', '']
            for source in CODE_FILES.get(issue['id'], []):
                detail.append('- ' + link({'path': str(ROOT / source)}))
            write(target, '\n'.join(detail))
        page += ['', '## 环境准备中的问题', '',
                 '这些发生在首程序启动之前，单列准备耗时；不把环境准备失败计作工作流执行速度。', '']
        for issue in prep:
            page += [f'- `{issue["id"]}`：{issue.get("problem", issue.get("diagnosis", "详见台账"))}；状态 `{issue.get("status")}`。']
        page += ['', '## 下一轮开始前核对', '',
                 '1. 读取本轮全部问题页；核对修复是否已部署，并区分已真机恢复与仅离线通过。',
                 '2. 核对旧租约、当日计划、现有标签和可用企业微信主窗；就绪后才从首流计时。',
                 '3. 不复用旧轮成功的发送key来假装新测试；也不更换结果未知的key重发。',
                 '4. 正常路径连续执行；预期加载有限等待；真正未知结果才停止输入并核对。',
                 '5. 只测修改相关部分，再完整跑一轮。记录本轮未改却复现的问题及原件，禁止只写“已解决”。', '',
                 '## 完成判定', '',
                 '三流各自需要页面采集、输出文件、测试群客户端收据和完成游标证据。全部确认后才启用上午排程；当前不以部分文件已发送代替三流验收。', '',
                 f'机器台账：{link({"path": str(SOURCE)})}']
        write(directory / 'README.md', '\n'.join(page))
        index.append(f'- [第{number}轮 三工作流实操](round-{number:03d}/README.md)：`{run.get("state")}`，{len(live)}个执行问题记录。')
    index += ['', '## 使用规则', '',
              '下一轮开始前必读上一轮记录和问题页。每个完整新轮次在台账 rounds 数组追加，记录 ranges；问题写 round_number，不覆盖旧轮；原工单修复续跑留在原轮次。',
              '轮次结束、证据核验并生成终版后设置 record_sealed=true，后续生成不会改写已封存的轮次文档。',
              '更新问题后运行上述生成命令。文档记录用于复习，已经确定的恢复和等待逻辑仍写入程序，不依赖模型每次临场理解。']
    write(OUT / 'README.md', '\n'.join(index))
    print(f'Rendered {len(rounds)} round(s) under {OUT}')


if __name__ == '__main__':
    main()
