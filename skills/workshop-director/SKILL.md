---
name: workshop-director
description: 调度每日评价统计、差评投诉草稿复查、违规通知三个独立岗位，串行分配浏览器和企业微信，检测停滞并向监理发出修复及重派工单。
---

日常调度使用独立代码包 `packages/workshop-director/bin/workshop-director --root 项目/runtime/standalone-workshop-director`，以本地 SQLite 计划和 macOS LaunchAgent 运行，不依赖 Codex 定时或开发工具常驻。`plan list/add/pause/resume/cancel` 管理计划，`tasks/issues/service health` 检查运行；每日上海时间 08:30。首次安装用 `init --paused`，三个岗位独立真机验收后才启用计划。原协调器 `scripts/coordinator.py` 保留为业务工单和深验接口，固定总目录 `runtime/workshop-director` 不变；本地包使用明确的 `local-subprocess-v1` 协议，不伪造旧工具履历，不推进岗位业务日期。

`morning` 按上海日期先续旧日；旧日全部完成才归档到 `days/日期/state.json` 并初始化当天。每次新派工先重验最初固定的三份验收路径、SHA与原始证据，再只读三个岗位五份固定业务台账，保存原字节哈希快照及原任务/工单ID；不替岗位写日期。跨午夜仍保留旧日截止日期，同日重复或并发 morning 不重复派工。

旧版 `init` 仅初始化；显式 `plan` 先持久化派工意图再返回一次岗位工单，依次评价统计→投诉草稿/复查→违规汇总。每岗自行读取独立进度，补做至当天（不含）；复用原工单和发送key，禁止另起key重发结果不明的操作。收件人固定「测试群请忽略」，投诉仅草稿；禁止生产发送及真实投诉提交。

本地新派工先保存意图，再启动普通岗位子进程，`ack` 深验实际调用者 PID、启动身份和原工单回执。旧 `collaboration.followup_task` 派工仅保留原单恢复兼容；不能把未知旧派工改成新本地派工重发。取得 plan 后崩溃/未 ack，先复查原进程和回执；`inspect/status` 不隐式重派。岗位日志由 `semantic_progress.py` 和 `fresh_completed_evidence.py` 深验，仅当前原工单中新闭环及客户端确认计为实质进展；旧结果、心跳、只读观测、更新时间和模型自报均不能续期。发现异常由监理修复代码，再以绑定原 task/attempt/order 的修复证据续跑；原执行岗、浏览器和发送均须静止。结果未知不重启、不换 key、不夺取资源；监理不代执行业务。

`finish` 必须登记同岗位的真实验收/完成报告路径及SHA256；报告须明确 `live=true`、`complete=true`、`test_target=测试群请忽略`、`production_sent=false`、`complaint_submitted=false`，且具有实际业务证据引用，模拟报告不合格。每次finish报告另须有当前dispatch_id/day/role/completed_at，时间位于本次派工意图之后，不得用初始验收报告或其他日/其他派工代替；跨午夜仍沿原调度日截止日期。监理还须检查原始收据，不能只信布尔值。三个岗位完成后当日调度结束，次日读取各自业务台账补做，不由调度器修改完成日期。

所有浏览器约束沿用岗位代码：无CDP/调试端口、无凭据读取，只用DOM/UI树定位。监理只审查、修复和重新派工，不代执行业务。

已ack原派工进入attention后，若执行岗只读复查已证实完成，监理用 `reconcile-finish --dispatch-id 原ID --report 完成报告 --supervisor-report 复核报告` 消费原派工，不retry、不新派工。复核报告kind为`supervisor-original-dispatch-completion-reconciliation-v1`，须匹配dispatch_id/day/role、completion_report路径/SHA，source_completion_verified与四项静止/原工单字段均true；original_work_order含journal路径/SHA和从该原日志抽出的identity，journal也须列入完成报告evidence。未ack或dispatch-ack-unknown先复核原ack。正常finish仍只接受running；heartbeat不能解除attention。

日统派工返回`daily_execution`固定order与launcher命令，执行岗必须沿该父入口start/advance/notify，不能直接flow或内层timed_run。完成后以`daily_orchestration.py`纯复验适配当前dispatch报告，再由主任finish；功能完成与30秒性能通过分开。heartbeat仍用实际operator/sender日志，不用父计时state。

违规与投诉新派工返回 `role_execution` 的原 order，分别由 `role_execution_launcher.py`、`complaint_execution_launcher.py` 连续执行。对应 orchestration 深验当前派工报告后主任再 finish；新父入口的实机验收不能用历史内层报告代替。

故障计时用 `scripts/rehearsal_issue_timing.py` 的 `open → repair-start → resume → verified/failed`，每轮独立监理台账并绑定原派工/停点证据；历史起点不明须 `open --historical`。只在阶段实际发生时登记，整轮原 E2E 时钟不断开、不扣故障时长；完整流程结束后再开下一轮复测。
