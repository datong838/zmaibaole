# 本地车间主任授权宿主

调度逻辑继续使用 `workshop_director`，不依赖 Codex、模型 API 或云定时。

当前固定应用：`/Users/feibing/work/projects/zmaibaole/dist/WorkshopDirectorHost.app`。

```sh
/usr/bin/open /Users/feibing/work/projects/zmaibaole/dist/WorkshopDirectorHost.app --args --permissions
```

窗口提供辅助功能、屏幕录制、下载目录授权及真实子 Python 检查。授权窗口与 `--probe-child` 不执行工作流；只有 `--serve` 可启动原调度器。检查保存到 `work/2026-10-23/workshop-host-permission-probes/`，可重复执行。当前安装检查绑定已核验的 2026-10-22 评价导出样本；缺少该样本应重新配置检查，不能当作已授权。

LaunchAgent 已于 2026-10-23 迁移到此应用的 `--serve` 模式，原工作单、队列和计时保留。launchd 启动的宿主及其 Python 子进程已实际通过三项权限检查，迁移收据位于 `work/2026-10-23/standalone-host-migration-v1/`。应用更新签名后，系统可能要求重新授权。构建器只离线构建，不打开应用或安装服务；参数见 `python3 packages/workshop-director/macos/package_host.py --help`。
