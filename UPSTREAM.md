# 上游溯源（UPSTREAM）

本项目在设计时学习了开源项目 Dashy 的核心思路。按接力规范记录上游信息如下：

- **source_url**: https://github.com/Lissy93/dashy
- **source_commit**: a0005e8d6ea3dad611bc7c4daa1cd837dd338c79
- **license**: MIT
- **attribution**: Copyright (c) 2019-2026 Alicia Sykes <https://aliciasykes.com>

## 说明

- `source_commit` 是 2026-10-21 通过 GitHub 接口实查的上游默认分支 HEAD 提交
  （提交说明 "🔖 Bump version to 4.8.7"，提交时间 2026-10-16）；当日做设计
  调研时通读的上游内容正是这一提交，包括 README 与
  `docs/configuring.md`、`docs/status-indicators.md`、`docs/icons.md`。
- `attribution` 的版权行逐字复制自上游仓库 `LICENSE` 原文，未做任何改动。
- 本项目代码为独立重写（Python + FastAPI + SQLite），未复制上游源码；
  借鉴的是个人导航页的产品思路：分组（sections）组织链接、条目四字段
  （名称/说明/图标/网址）、自动取 favicon、服务端状态探测、即时搜索。
  调研细节见 NOTES.md。
