# 决策记录（DECISIONS）

记录影响产品行为的取舍决定：谁在什么时候定的、为什么、以及与之相关的后续规则。

## 2026-10-21 · grok/TASK-016-startdeck（review+fix）复核合并

来源：Grok Build 在本地真跑后推到 `grok/TASK-016-startdeck` 分支（head `10548aa083a2`，
基座 == 当时 main head `05e19958`，merge-base 一致）。结论：本地跑通，
pytest 20 项、live_selftest 全过；P0 无；P1 4 条修了 3 条。

红线核对（合并前逐项实查）：分支 `tests/` 下两个测试文件 SHA 与 main 逐字节一致
（`fb5c50b9…` / `7198c495…`），无测试被删、无 skip、无断言被弱化；改动只限
`app.py` 与 `README.md`，与 `reports/TASK-016-startdeck/changed.txt` 一致。
`reports/` 目录按接力协议不合入 main，留在 grok 分支。

逐条决定：

- **P1-1 采纳**：`app.py` 启动监听改成读 `HOST` 环境变量、默认 `127.0.0.1`
  （原来默认 `0.0.0.0`）；`README.md` 两处启动注释与环境变量表同步改成同一默认值。
  与 dailymemo 的同类修复口径一致。提交 `24d3616c`。
- **P1-2 采纳**：`favicon_url_for` 去掉 URL 里的用户信息
  （`https://alice:s3cret@example.com/…` → 只保留主机和端口），IPv6、端口、
  密码含 `@` 的用例 Grok 已验证，我方另行单测复核通过。提交 `24d3616c`。
- **P1-3 采纳**：关闭 `docs_url` / `redoc_url` / `openapi_url`。理由：匿名可访问的
  文档页会从 jsDelivr 加载外部脚本，而登录令牌存在 localStorage 里，存在被读走
  的风险；单用户自用工具不需要在线文档。`/docs` 等三入口现返回 404。
  提交 `24d3616c`。
- **P1-4 我方在 main 直接实现**（Grok 因测试耦合如实记"修不动"，未改代码）：
  改密时删除该用户的其他全部会话、只保留当前会话。实现上把 `change_password`
  的 SQL 与会话删除放在同一连接里；测试上把 `auth` 夹具从模块级改为函数级
  （每个用例独立登录——这是隔离性重构，不删用例、不弱化断言），并新增
  `test_change_password_revokes_other_sessions`（A 改密后 A 有效、B 401，
  再改回原密码）。与 bookmark-manager「改密清全部会话」的口径一致。
  提交 `4c234f91`。

不采纳项：无。

口径重申（与用户已定决策不冲突）：首次登录的改密**只提示、不强制**
（用户 2026-10-20 对 PMC 的 P1-9 选 B，之后定为所有复刻项目的统一口径）；
本次 P1-4 是"改密后作废其他会话"，两者是不同维度，不冲突。
