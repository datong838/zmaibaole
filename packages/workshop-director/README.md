# 车间主任

独立本地 Python 程序，使用 SQLite 保存计划、任务和进程回执，通过普通子进程调用三个岗位。运行不需要 Codex；系统服务使用 macOS LaunchAgent。

```sh
./packages/workshop-director/bin/workshop-director --root "$PWD/runtime/standalone-workshop-director" plan list
./packages/workshop-director/bin/workshop-director --root "$PWD/runtime/standalone-workshop-director" plan add --id 临时补跑 --workflow violation-notifier --at 2026-10-24T09:15:00+08:00
```

`plan pause/resume/cancel --id ID` 管理计划；`tasks` 查看执行，`issues` 查看异常。默认每日上海时间 08:30，三岗串行执行并补排漏日。暂停不终止在途岗位；结果未知不重复启动。

首次使用 `init --project 项目绝对目录 --acceptance 验收索引 --start-date YYYY-MM-DD --paused`，然后 `service generate --out 文件`、`service install --plist 文件 --install`、`service health`。首次安装保持计划暂停，完成真机验收后再启用。

独立服务已安装并验证常驻，morning 计划保持暂停；当前正式版本的三岗完整实机接线仍在验收。AI 判断及图片审核保留原工单的文件交接接口，未经实际审核不会自动通过。发送目标固定测试群，投诉仅草稿。
