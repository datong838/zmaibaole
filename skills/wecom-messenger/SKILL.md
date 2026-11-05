---
name: wecom-messenger
description: 通过macOS辅助功能UI树向企业微信群聊或个人发送文字和文件，固定代码流程校验收件人、草稿、文件哈希及发送回执；当前仅放行测试群请忽略和方景堂。
metadata:
  version: 1.0.0
---

# 企业微信发送岗

从本skill目录运行，Python 3.9+，仅标准库。需要已登录企业微信Mac版及运行宿主的辅助功能权限；不需要Chrome扩展、调试端口或屏幕录制。

```sh
python3 scripts/messenger.py doctor
python3 scripts/messenger.py prepare --key 唯一业务编号 --kind group --target '测试群请忽略' --text '仅测试，请忽略'
python3 scripts/messenger.py run --job /prepare返回的job_path
```

发个人使用 `--kind person --target '方景堂'`。发文件把 `--text` 换成 `--file /文件绝对路径.xlsx`；长文字可用 `--text-file /文字文件.txt`。每项内容分别prepare，重跑必须复用相同key；不为同一次发送生成新key绕过停点。

代码负责选择目标、核验群/个人类型、保护草稿、写发送意图、防重复及回执。执行者只调用prepare/run/status，不临时点其他按钮。`unknown`仅核查，不重发；发送前的locate/verify失败修复后可用 `resume --job ...`，发送意图后的失败不能resume。

`config/policy.json`当前只授权两个测试目标，production_enabled=false；不因日常统计完成而扩大名单或改为生产。新增目标/生产发送必须已有用户授权。此skill与统计岗位独立，未自动发送真实评价产物。

只按UI树角色、文字和语义关系定位，键盘事件定向到已验证的企业微信进程。禁止坐标/OCR定位、读取客户端数据库/登录凭据、改登录态、群发广播、自动加人/建群。非空草稿、目标歧义、进程更换或文件变化立即停止。

文件限20MiB，只发送原始选定文件。`ui_confirmed=true`表示客户端聊天记录出现且输入框清空，不证明对方已读或服务器送达。权限与验收见[说明](references/说明.md)。

PNG/JPEG会粘贴为图片草稿。代码确认原文件哈希、空输入框、目标/PID、本程序写入剪贴板的file-url类型/URL/变更计数，粘贴一次后绑定唯一附件与会话基线。同一连续执行进程复核绑定后先记录Return意图，再按一次回车；空输入框、旧消息不变和唯一新增图片消息共同作为客户端确认。缺少绑定、进程重启或结果不明时只核查，不重粘贴/重发。公开AX富文本不提供真实图片字节，因此使用可审计的自身粘贴链，不声称做过草稿图像内容比对；用户手动发送须记user_sent。

特定 `image-paste-seed-or-transcript-changed` 停点可由监理核准后调用 `python3 scripts/image_draft_recovery.py --job /原工单绝对路径 --original-sha256 原SHA`：保留原工单和发送基线，只复制唯一图片草稿并与源图逐像素比对，成功才按一次回车；不重粘贴，复制或发送结果不明不可重试。常规发送仍使用自身粘贴链。
