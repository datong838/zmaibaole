# 卖爆了工作流代码

此仓库保存调度器、三项业务工作流、企业微信发送器及现有 Chrome DOM 扩展/本地桥接代码。2026-11-05 的成功交付代码作为当前基线。

## 基线行为

- 当日交付前一日内容，从正式进度补齐尚未交付日期。
- 两家公司独立交付，一家公司就绪立即发送至配置的业务群并核对客户端确认，不等待另一家公司。
- 只生成投诉草稿或复查已有平台结果，不提交新投诉。
- 已确认发送按原业务键复用；UNKNOWN 操作须核对原工单，不盲目重放。
- 运行决策只用当前任务明确指向的输入、输出和未决状态，不扫描历史目录或恢复链。
- 浏览器操作使用现有 DOM 扩展、本地桥接、SDK 及原生 AX 通道。

## 数据与本机配置

`.gitignore` 排除了 work/、runtime/、业务案例记忆、历史证据、客户测试夹具、生成报表/图片、本地依赖和真实配置。Git 只承载代码，不能通过克隆得到客户资料、客户端确认或正式业务游标。

以下配置需在目标电脑单独准备，不进入公开仓库：

- skills/chrome-dom-export/extension/config.js
- skills/daily-comment-stats/config/companies.json
- skills/daily-comment-stats/config/company_wecom_map.csv
- skills/workshop-director/config/company-scopes/
- skills/workshop-director/config/approved-company-scope.json
- skills/workshop-director/config/delivery-targets.json
- skills/wecom-messenger/config/policy.json
- skills/negative-review-complaints/config/appeal-history-identities.json（可选的旧历史入口身份配置）

运行环境和权限设置参阅 packages/workshop-director/README.md 及各 skill 的 SKILL.md。部署时设定 Asia/Shanghai 每日 03:30，由程序执行、监理处理异常，目标 10:00 前交付。Codex 对话定时任务及本机 SQLite 排程属于本地配置，不随源码克隆自动安装。

## 验证范围

详见 BASELINE-20261105.md。基线已在原运行环境完成真实交付；尚未验证全新 Mac 从零安装后的端到端执行。迁移需单独核对依赖、配置、登录、AX/录屏权限、正式游标和未决操作，不能复制旧 PID/标签页后直接重放。
