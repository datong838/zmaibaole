---
name: negative-review-complaints
description: 独立处理抖音来客平台筛选后的中差评投诉草稿、截图核对、已有投诉复查及Excel逐条台账；按公司断点补做，不混入每日统计或违规流程。
metadata:
  version: 0.2.0
---

# 差评投诉处理岗

仅生成草稿及复查已有结果，代码无投诉提交入口。正式连接为已安装的 `local-dom-bridge`；发送固定「测试群请忽略」。已完成两公司2026-10-16（含）至2026-10-21（不含）真机验收，证据见[验收](references/验收.md)。新页面结构仍须真实profile校验，不沿用不匹配选择器。

从项目根目录运行 `python3 skills/negative-review-complaints/scripts/workflow.py --root /固定的公司工作目录 <命令>`。根目录跨日期复用，不能每天另建根目录丢失进度。具体命令和输入契约见[交接](references/交接.md)。

执行顺序由代码返回的 `plan.next_actions` 决定：

1. `init` 初始化公司独立进度，`plan` 取得补做日期及未结案评价。首次从前一个工作日开始，以后从已连续完成处到今天零点（不含），保留未结案复查项。
2. 复用已批准的local-dom-bridge，核验账号、公司、日期及「中差评（1-3心）」已选中。`bridge-navigation.py` 固定日期/中差评导航并等待两次稳定正常列表；`normal_observation.py` 验证指定公司真实profile并交 `authoritative_join.py` 唯一匹配本次Excel，禁止任意按钮执行。页面适配未验收时停止，不猜测选择器。精确星级和绝对日期来自已核本次Excel；平台折叠区排除，单条正文收起不等同折叠区。
3. `capture` 接收完整分页采集结果；只收正常筛选区，折叠区不展开、不读取。稳定评价ID缺失、日期/数量/边界不符即停止。
4. 截图唯一入口为 `capture_review_region.py --manifest PATH --manifest-sha256 SHA --outdir DIR --pid PID --revision REV`：代码串联已审账户浮层退出与原区域截图，未知结果不重放，已完成截图仅读原收据。`register-review-screenshot` 只登记独立验证的DOM定位评价区域图，整窗原图不算最终验收。已确认发送的旧整窗图需用 `revise-review-screenshot --reason user-requested-region-only` 保留历史并建立区域更正版本；未知发送禁止换版本。`send-test` 委托独立wecom-messenger发送，同一评价复用相同发送key；unknown不重发。
5. `plan` 自动加载差评申诉案例摘要；`analysis-order` 自动加载同公司近30天完整已核原文及结果。按五类逐项语义判断，`classification_policy.py` 强制证据与分支一致；四项均不符才选其他。其他类同时用 `recent_other_history.py --root ROOT --id KEY --out FILE` 固定近7天非空真实样本并 `history` 登记，至少参考min(3,样本数)条；零样本须完整查询证据才可声明无历史。历史仅供措辞参考，不能移植商家主张或把驳回/待审当成功范本。`draft_inspection.py prepare/run/verify` 固定原表单选项证据，只打开/取消空表；`analyze` 通过选项与五类校验后存草稿。
6. 已有「查看投诉结果」只做 `result` 复查，不重新投诉。`close` 验收本批截图、核对和草稿/已有结果后推进草稿进度；未结案项持续复查。`block` 记录无法继续的原因。

每次状态变更自动重建 `投诉处理结果汇总.xlsx`，包含汇总、逐条结果、五类判断依据、日期进度、历史处理记录。JSON与证据为权威记录；Excel导出失败保留JSON，先 `export` 修复，不能伪报完成。不要手工编辑Excel回写流程。

禁止开启CDP/调试端口、重启带调试参数的Chrome、读Cookie/网站存储、隐藏接口、React内部状态、坐标/OCR定位。仅使用已审核的本机回环DOM桥与系统公开AX接口。连接丢失、风控、登录或账号变化停止。沿用采集岗的账号/公司/日期定位能力，但不修改其只读导出边界。

依赖同项目的daily-comment-stats（日历）、chrome-dom-export（DOM桥及区域证据）、douyin-laike-operator（身份导航）、wecom-messenger（发送），通过JSON交接，各自进度独立。流程Python使用标准库；区域裁切另需Pillow，Excel使用Codex捆绑Node与artifact-tool。当前验收及下一次实操点见[验收](references/验收.md)。

已有投诉结果的页面执行使用 `scripts/existing_result_runner.py prepare` 固定六份输入refs与订单SHA，再 `run --manifest … --steps 10`。代码持久化单次打开/关闭意图，unknown只读对账；按root内同review索引阻止换来源绕过未完成操作。旧completed operation须连同原normal-before/drawer/normal-after显式完整校验后只读adopt，不能重新打开。正文v2按profile显式启用，不改历史profile。

`result` 存入真实原申诉后自动调用 `case_memory.auto_import` 去重追加并再生[差评申诉案例库](references/投诉案例记忆.md)。库在 `memory/complaint-cases.jsonl`，原文及source/result哈希副本随skill迁移；只读加载不改文件，fixture不读真实库。近30天是默认检索窗口，全部旧案长期保存；入库数只代表已核原文，近30天全量补采尚未完成；以JSONL实际记录为准。

公开历史入口发现用 `scripts/appeal_history_coverage.py --audit FILE --sha256 SHA --document skills/negative-review-complaints/references/投诉案例记忆.md` 核验并独立追加可迁移范围审计；不计为案例。`plan`/`analysis-order` 自动携带其覆盖限制，已归档数不代表全月总量。

月历史补采只使用 `scripts/history_workspace.py` 的独立root：`init → prepare-acquisition → prepare-normal-job → ingest → prepare/run → verify-coverage`。源仍须完整真实normal profile及本次Excel唯一join。代码跳过「投诉」，仅复查已有结果并自动入库，不截图、不发群、不生成新申诉、不推进日常cursor；正式 `workflow.py` 拒绝此类root。跨来源旧操作须 `pin-prior` 完整验证已关闭链，未知操作仍停。

昵称与历史 Excel 冲突时使用独立 `scripts/case_alias_cli.py` 首次受控复核，入口见[昵称变更复核](references/昵称变更复核.md)。`apply_case_alias.py --receipt PATH --receipt-sha256 SHA` 深验收据、更新原任务结果及Excel/案例库，保留原 source/key/customer 与历史，不释放截图权限。后续每日复查入口为 `scripts/case_alias_v3.py`，按原评价和当前派工建立不可变版本；监控仅认可实际关闭且已写入结果的闭环。v3已通过离线测试，真机验收尚未完成，不得复用旧观察冒称今日结果。
