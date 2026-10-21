# startdeck 验收审查

结论：环境能装上，pytest **21 passed**（8.72s），`live_selftest` **ALL PASS**，服务默认听在 **127.0.0.1:8000**，首页 **200**。没有 P0。没有需要改代码的 P1。README 有 4 处与代码不符；图标失败不回退首字是明确的功能缺陷，列入 P2。许可证与署名在仓库内自洽；上游 commit 与版权原文未联网复核。

证据命令与原文在 `run.md`。下面文件行号均指仓库 `E:\muse-bridge\in\TASK-029-startdeck`。

## 本地跑通记录

Python `3.11.9`（`python --version`）。虚拟环境在 `E:\muse-bridge\work\TASK-029-startdeck\.venv`，未写进待审仓库。依赖用 `requirements-dev.txt` 安装（其中 `-r requirements.txt`），exit 0，装上 `fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1`。

pytest：

```
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -B -m pytest E:\muse-bridge\in\TASK-029-startdeck\tests -q --rootdir E:\muse-bridge\in\TASK-029-startdeck
```

```
21 passed, 1 warning in 8.72s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。按任务不改已有依赖版本。

`tests/live_selftest.py`（端口 8131，临时目录改到工作目录）末行 `LIVE SELFTEST: ALL PASS`。登录 `admin/admin123` 返回 `must_change_password: true`。单条探测通为 `status_code 200`；断连错误原文 `[WinError 10061] 由于目标计算机积极拒绝，无法连接。`。脚本里的「文档站」会请求 `https://example.com/`，断言不依赖它通，本次整段通过。

服务：`python app.py`，子进程未设置 `HOST`，`PORT=8000`，数据库在工作目录。

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       6788
HTTP 200 GET /
HTTP 401 GET /api/me          {"detail":"未登录"}
HTTP 200 POST /api/login      must_change_password=true
```

首页 `Content-Type: text/html; charset=utf-8`，正文以 `<!DOCTYPE html>` 开头，标题是 `startdeck · 个人起始页`。响应里没有 `X-Frame-Options`、`Content-Security-Policy`、`X-Content-Type-Options`、`Referrer-Policy`。

README 未写健康检查 URL。实测 `GET /health` 与 `GET /api/health` 都是 `404 {"detail":"Not Found"}`。`/docs`、`/redoc`、`/openapi.json` 同样 404。查完后 `terminate`，进程退出（`SERVER_STOPPED 1`）。

另两件本地核对（不访问外网）：

- 302 不跟随：探测返回 `up True, status_code 302`，跳转目标进程命中数 `0`。
- 第二个初始用户与第一个互不可见：跨用户读/改/删均为 404，己方数据仍是 200（`audit_isolation.py`）。

没有浏览器工具，页面点击流程没有在浏览器里走。首页 HTML、登录接口和自测脚本已覆盖。

## README 与实际不符处

1. `README.md:65` 写「共 20 项自动化测试」。`pytest` 结果是 `21 passed`。`tests/test_app.py` 有 21 个 `def test_`，多出来的是 `tests/test_app.py:127` `test_change_password_revokes_other_sessions`。同段列举的覆盖主题（登录/改密、分组、链接、校验、搜索、探测、favicon）与这些用例对得上，错的是数字。

2. `README.md:12` 写「页面加载不到图标时自动回退为名称首字占位」。`static/index.html:368` 在图片 `error` 时只 `img.remove()`；`static/index.html:370` 在设置 `src` 之后立刻给首字加上 `hidden`；`static/index.html:371` 只在 `load` 时移除首字。`static/index.html:19` 的 `.hidden` 是 `display:none !important`。图片失败后首字仍然隐藏，方块是空的。旁边注释写「取不到图标就留首字占位」，和这三行的实际顺序相反。

3. `README.md:7` 写功能「均已测试覆盖」。后端行为有 pytest / live_selftest。下面几项只有前端实现，两个测试文件都没有断言：
   - 删除前确认：`static/index.html:331`（分组）、`static/index.html:377`（链接）
   - 打开页面自动探测：`static/index.html:247`、`static/index.html:491`
   - 绿点/红点文案：`static/index.html:281-286`
   - 图标失败回退：`static/index.html:365-372`（并且行为与 README 不符，见上条）

4. `README.md:69-70` 真实流程自测只给了 bash：`.venv/bin/python tests/live_selftest.py`。同文件 `README.md:29-36` 与 `README.md:59-63` 给了 Windows 的 venv 路径，自测这一段没有对应的 `.venv\Scripts\python tests\live_selftest.py`。脚本本身在 Windows 上能跑通（见跑通记录）。

以下 README 陈述与代码一致，不计入不符：默认 `127.0.0.1:8000`（`app.py:577-578`，启动日志与 netstat）；默认账号 `admin/admin123`（`app.py:28-29`，登录 200）；`PORT` / `HOST` / `STARTDECK_DB_PATH` / `SD_INITIAL_USERNAME` / `SD_INITIAL_PASSWORD`（`app.py:26-29`、`app.py:577-578`）；Token 24 小时（`app.py:27`）；网址仅 http/https（`app.py:426`）；2xx/3xx 算通且不跟随重定向（`app.py:143-145`、`app.py:168`，单测与本地 302 实验）；分组删除级联与确认框存在（`app.py:405-406`、`static/index.html:331`）。

## 许可证与署名核查

仓库内自洽，本次未改 `LICENSE` 与 `UPSTREAM.md`。

- `LICENSE:1-3`：MIT，版权行 `Copyright (c) 2026 startdeck contributors`。正文是标准 MIT 许可条款。
- `README.md:80-82`：声明 MIT，并指向 `LICENSE` 与 `UPSTREAM.md`，称本项目独立实现、上游同为 MIT。
- `UPSTREAM.md:5-8`：上游 Dashy，`source_url` `https://github.com/Lissy93/dashy`，`source_commit` `a0005e8d6ea3dad611bc7c4daa1cd837dd338c79`，许可证 MIT，版权行 `Copyright (c) 2019-2026 Alicia Sykes <https://aliciasykes.com>`。
- `UPSTREAM.md:16-19` 与 `NOTES.md:5-10` 都写代码是 Python + FastAPI + SQLite 独立重写，未复制上游源码。两份记录的 commit、许可证、版权行一致。
- 通读 `app.py` 与 `static/index.html`：没有 Dashy / Vue 源码片段，也没有 Alicia Sykes 的版权头。在「未复制源码、只借鉴产品思路」这个前提下，本仓库 `LICENSE` 使用自己的版权主体，上游版权放在 `UPSTREAM.md`，和 MIT 对衍生作品保留原版权声明的要求不冲突。
- `source_commit` 以及「版权行逐字复制自上游 LICENSE」（`UPSTREAM.md:12-16`）按任务禁止访问外网，**未复核**。没有证据说这两句是错的，所以不改 `UPSTREAM.md`。
- 本工作副本 `git log --all` 只有 `a1ecd37`。`DECISIONS.md:7-34` 里的 `10548aa083a2`、`24d3616c`、`4c234f91` 等提交在这个副本的历史里看不到，无法用本地 git 复核那些合并叙述。不据此改 `DECISIONS.md`。

`.gitignore:1-9` 忽略了 `data/`、`*.db`、`.env`、`.venv/`。默认数据库路径 `app.py:26` 的 `data/startdeck.db` 不会被 git 跟踪。

## 分级修复清单

上一轮已合入、本次复核仍成立、不开新项：默认绑定 `127.0.0.1`（`app.py:577`）；favicon 去掉用户信息（`app.py:62-65`，样例输出见 `run.md`）；关闭 `/docs` `/redoc` `/openapi.json`（`app.py:190-196`，实测 404）；改密删除其他会话（`app.py:292-295`，`tests/test_app.py:127`）。首次登录只提示不强制改密是 `DECISIONS.md:38-39` 的既定口径，测试也依赖未改密即可调用 API，不列为缺陷。

### P0

无。安装、21 项 pytest、live_selftest、`127.0.0.1:8000` 首页 200 均已跑通。

### P1

无。鉴权覆盖除登录与首页外的 API；跨用户访问 404；探测不跟随重定向；非 http/https 在 `app.py:426` 被拒绝；含 CR/LF 的网址虽能通过校验，但本机 `http.client` 发请求前会拒绝（见 P2-4 的实测错误），当前打不出请求头注入。

### P2

1. `static/index.html:368-371` 图标失败后首字仍被 `hidden` 藏住。修法：不要在加载前隐藏首字；`error` 时去掉 `hidden` 并删掉图片，`load` 成功再隐藏首字。
2. `README.md:65` 测试数量写成 20。修法：改成 21，并写上 `test_change_password_revokes_other_sessions`。
3. `README.md:7`「均已测试覆盖」超出了现有测试。修法：改成后端用例已覆盖，确认框、自动探测、状态点文案、图标回退属于前端行为、当前没有自动化测试。本任务不许改测试，所以不能靠加断言圆上这句话。
4. `README.md:69-70` 自测命令只有 bash 路径。修法：补一行 Windows：`.venv\Scripts\python tests\live_selftest.py`。
5. `app.py:421-428` `validate_url` 接受含 `\r` `\n` 的网址（实测 `validate_crlf` 原样返回）。修法：拒绝 `\x00-\x20` 与 `\x7f`。本机探测已被解释器挡住：`URL can't contain control characters ... (found at least '\r')`，所以不升 P1。
6. `app.py:250` 密码哈希用 `!=` 比较；用户不存在时短路、不算哈希。`app.py:280` 改密同样用 `!=`。修法：统一先算哈希，再用 `hmac.compare_digest`。口令哈希 20 万次 pbkdf2（`app.py:50-52`）占掉绝大部分时间，又是本机单用户，不升 P1。
7. `app.py:190` 创建 FastAPI 时没有安全响应头。实测首页 `sec_headers (none)`。修法：加 `X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy: no-referrer`。令牌在 `localStorage`（`static/index.html:203`），不走 Cookie。
8. `static/index.html:359` 外链只有 `rel="noopener"`。修法：写成 `noopener noreferrer`。
9. `static/index.html:262-264` 改密成功后不隐藏 `#pwBanner`。修法：成功时加上 `hidden`。下次打开页面会走 `static/index.html:489`，那时横幅会按 `must_change_password` 收起。
10. `app.py:459-462` 搜索把用户输入直接包进 `LIKE %...%`，`%` 与 `_` 仍是通配符。修法：转义这两字符并加 `ESCAPE`。查询已带 `user_id`，只能搜到自己的链接。
