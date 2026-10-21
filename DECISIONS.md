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

## 2026-10-21 · grok/TASK-029-startdeck（纯报告 review 模式）

来源：Grok Build 在本地真跑后推到 `grok/TASK-029-startdeck` 分支
（head `d26d02f8ee032968f056a7078c6273c335958361`，基座 == 当时 main head
`a1ecd377`）。结论：本地跑通，pytest 21 项、live_selftest 全过，
127.0.0.1:8000 首页 200；P0 无、P1 无；P2 10 条按任务规矩未改代码。
该分支经核验无任何代码改动（只有 5 个报告文件），不合并，我方在 main 上
逐项实现。

逐条决定（10 条全采纳，无不采纳项）：

- **P2-1 采纳**：图标加载失败时删掉图片并把首字占位显示回来
  （之前 `hidden` 一直盖着，方块是空的），加载成功首字才退场。前端改动，
  无自动化测试（见 README 功能清单说明）。
- **P2-2 采纳**：README 测试数 20 → 写实数（本轮后 25）。
- **P2-3 采纳**：「均已测试覆盖」改成准确表述：后端行为有自动化测试覆盖，
  确认框、自动探测、状态点文案、图标回退属于前端行为、暂无自动化测试。
- **P2-4 采纳**：README 真实流程自测补 Windows（PowerShell）命令。
- **P2-5 采纳**：`validate_url` 拒绝含控制字符（`\x00`-`\x20`、`\x7f`）
  的网址，网址里的空格请写成 `%20`。带回归测试。
- **P2-6 采纳**：登录与改密的密码哈希比对改用 `secrets.compare_digest`
  （口径第 8 条）；用户名不存在时也照常算一次哈希再拒绝。全盘审计：
  敏感字面比对只有这两处，令牌走数据库参数化查询、SQL 里的 `token != ?`
  不是 Python 字面比对，均不改。带回归测试（未知用户 401）。
- **P2-7 采纳**：加安全响应头，照抄 pushhub 的纯 ASGI 中间件做法
  （`X-Frame-Options: DENY`、`X-Content-Type-Options: nosniff`、
  `Referrer-Policy: no-referrer`，另加 `Content-Security-Policy:
  frame-ancestors 'none'`）；startdeck 无 SSE，直接加不影响。
  带回归测试。
- **P2-8 采纳**：外链 `rel="noopener"` → `"noopener noreferrer"`。
- **P2-9 采纳**：改密成功后提示横幅立即收起（之前要等下次打开页面）。
- **P2-10 采纳**：搜索的 LIKE 把用户输入里的 `\`、`%`、`_` 转义并加
  `ESCAPE '\'`，只做字面匹配（与 bookmark-manager 的 ede1a738 同一做法）。
  带回归测试。

note：review 原文明确"首次登录只提示不强制改密是既定口径，不列为缺陷"，
与口径第 1 条一致，本文件 38-39 行已有记录，不重复记。

## 2026-10-21 · grok/TASK-036-startdeck（纯报告 review 模式）

来源：Grok Build 在本地真跑后推到 `grok/TASK-036-startdeck` 分支
（head `81835f80`）。结论：本地跑通，pytest 21 项（当时 main）、
live_selftest 全过；P0 无、P1 无；P2 9 条未改代码。
该分支基座是 TASK-029 之前的 main，报告里 P2-1/2/3/4/7 已被 TASK-029
在 main 落地（`be0be991`），无需再做；剩下 3 项我方在 main 实现：

- **P2-5 端口子项采纳**：`validate_url` 增加端口检查——越界（如 99999）、
  非数字、端口 0 一律 400 拒绝（`parsed.port` 对前两者抛 ValueError，
  一并捕获）。带回归测试。
- **P2-6 采纳（文档）**：状态探测走服务端 urllib，默认带 `ProxyHandler`，
  会遵循本机 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量；之前 README 没写，
  已在功能清单的状态探测条目里补一句说明。不改行为。
- **P2-8 采纳：会话 token 哈希入库**。评估：quicklink 对同类项选了"留待后续"，
  但 startdeck 这里决定修，理由——① db 文件可能进备份/同步盘，明文 token
  是 24 小时有效的活凭证，哈希化是实实在在的纵深防御；② 改动收敛，
  只动登录/鉴权/登出/改密 4 处 token 落库与查询点，对外行为不变，
  存量测试无需改写；③ token 是 256 位随机数，SHA-256 无需加盐。
  实现：`token_hash()` 存 SHA-256，登录存哈希、鉴权/登出/改密清会话时先哈希
  再查库。带回归测试（断言库里只有哈希、没有明文）。
  注意：升级后旧库里的明文会话全部失效，用户重新登录一次即可。

## 2026-10-21 · grok/TASK-039-startdeck-p2（关闭，不合并）

来源：`grok/TASK-039-startdeck-p2` 分支（head `869f2f82`，review+fix 名义）。
结论：**不合并，只记档**。理由：

- 基座旧：merge-base 是 `a1ecd37`，落后当前 main（`be0be991`）1 个提交，
  是 TASK-029 落地前的旧基座导致的重复劳动。
- 10 项"修复"与 main 的 TASK-029 实现实质重复，且 main 版更优：
  安全头 main 用纯 ASGI 中间件（4 个头、只补缺失的不覆盖），分支用普通
  `@app.middleware("http")`（3 个头、覆盖式写入）；哈希比对 main 用
  `secrets.compare_digest`（口径第 8 条），分支用 `hmac.compare_digest`
  （行为等价、无实质增量）。
- 合进来没有增益，只有回退风险。分支不删除（留档），main 不动。
