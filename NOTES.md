# startdeck 调研笔记

## 上游对象（2026-10-21 通过 GitHub 接口实查）

- 项目：Dashy（github.com/Lissy93/dashy），MIT 许可证。
- 默认分支 HEAD：`a0005e8d6ea3dad611bc7c4daa1cd837dd338c79`（2026-10-16 的提交，版本号 4.8.7）。
- LICENSE 原文版权行：`Copyright (c) 2019-2026 Alicia Sykes <https://aliciasykes.com>`（逐字复制，见 UPSTREAM.md）。
- 上游技术栈：Vue 前端 + Node 服务端，配置集中写在一个 YAML 文件里，体量很大
  （多页、组件、主题、云备份、多用户与 SSO 等）。本项目只借核心产品思路，
  用 Python + FastAPI + SQLite 独立重写，数据存数据库而不是配置文件。

## 从上游读到的核心设计（通读 README、docs/configuring.md、docs/status-indicators.md、docs/icons.md）

- 数据组织就是两层：`sections`（分组）下面挂 `items`（条目），每个条目四个基本
  字段——title（名称）、description（说明）、icon（图标）、url（网址）。
  咱们的数据模型直接对应：sections 表 + links 表（name / description / icon_url / url）。
- 状态探测：由**服务端**代发请求（不是浏览器直连，避免跨域拦截），回响应码与
  响应时间，指示点用颜色区分 通 / 不通 / 未知；页面加载时查一轮是它的默认行为。
  咱们照这个思路自写探测函数，2xx/3xx 算通，并多做了「探测全部」一键并发探测。
- 图标：上游支持 `icon: favicon` 自动取目标站图标，取不到要有兜底。
  咱们用最稳的约定——`<协议>://<主机>/favicon.ico`，前端图片加载失败即回退
  名称首字占位，不依赖任何第三方图标接口（离线、内网都能用）。
- 搜索：按名称、域名（网址）、说明即时过滤，是它的一等功能，咱们做成
  顶部搜索框输入即过滤，后端 `/api/links?q=` 同样支持。

## 本项目 MVP 取舍（任务书范围，做全不扩）

借鉴的核心概念：分组导航、条目四字段、自动 favicon、服务端状态探测、即时搜索。

明确不做（超出单用户 MVP）：多页、动态组件（widgets）、主题/CSS 编辑器、
云备份同步、多用户与权限分级、SSO、快捷键体系、YAML 配置导入导出。

## 实现方案

- 后端：单文件 FastAPI（app.py）+ SQLite，登录方式沿用本团队已验证的做法
  （pbkdf2 密码哈希、自研 Token 会话表、24 小时过期、首次登录
  must_change_password=1）。环境变量：`STARTDECK_DB_PATH`、
  `SD_INITIAL_USERNAME` / `SD_INITIAL_PASSWORD`、`PORT`。
- 数据表：users / sessions；sections（id、user_id、name、sort_order）；
  links（id、user_id、section_id 外键级联删除、name、url、description、
  icon_url、sort_order）。删除分组时其下链接一并删除，界面删除前有确认提示。
- 探测：urllib 标准库发 GET，不跟随重定向（3xx 本身即算通，与团队 sitepulse
  的口径一致），超时 6 秒；单条探测 `POST /api/links/{id}/check`，
  全部探测 `POST /api/check-all`（线程池并发，上限 8）。
- 前端：单页 static/index.html，自行设计布局（深色顶栏 + 左侧分组导航 +
  分组卡片墙），配色与操作排布与上游明显不同；打开页面自动探测一轮，
  也可手动单条/全部探测。

## 资源核对结论

云端实测：2 核 CPU、7.7G 内存、Python 3.12。本方案运行时仅需数十 MB 内存、
单个 SQLite 文件，无 GPU、无重型依赖，云端完全带得动。
