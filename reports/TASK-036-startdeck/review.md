# startdeck 验收报告

结论：本机能按 README 装起并跑通。pytest **21 passed**，`tests/live_selftest.py` 全过，`python app.py` 默认监听 `127.0.0.1:8000`，首页 200。没有 P0。抽查没有可利用的鉴权绕过、越权或请求头注入，没有要改代码的 P1。README 有 4 处与代码或本机运行方式不符。LICENSE / README / UPSTREAM 在仓库内自洽；上游 commit 与版权原文未联网核实。本次未改仓库源码。

## 本地跑通记录

环境：Windows，Python 3.11.9，仓库 `E:\muse-bridge\in\TASK-036-startdeck`，HEAD `a1ecd377a058f1ac87a00a97ebafac6cd7023a89`（仅这一个提交）。虚拟环境按 README 建在仓库 `.venv`（已被 `.gitignore` 忽略）。测试用的 TEMP 与手动起服务的数据库放在 `E:\muse-bridge\work\TASK-036-startdeck`，避免写入系统 TEMP，也避免在仓库里留下删不掉的 `data\startdeck.db`（本任务禁止 del/rm）。默认数据库路径只对照了代码，没有落盘执行。

安装（退出码 0）：

```text
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

装上的正是锁定版本：`fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1`。

pytest（退出码 0，包装脚本把 TEMP 指到工作目录）：

```text
21 passed, 1 warning in 10.69s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。审查结束、未改源码后又跑了一次：`21 passed, 1 warning in 10.00s`，退出码 0。

`tests/live_selftest.py`（退出码 0）自己在 `127.0.0.1:8131` 起服务并关掉。节选：

```text
PASS 首页能打开且是 startdeck 页面
PASS 登录成功 | {"username":"admin","must_change_password":true}（token 已截断）
PASS 单条探测-通 | {'up': True, 'status_code': 200, 'response_ms': 17, 'error': None}
PASS 单条探测-断 | {'up': False, 'status_code': None, 'error': '[WinError 10061] 由于目标计算机积极拒绝，无法连接。'}
LIVE SELFTEST: ALL PASS
```

自测里的「探测全部」会请求 `https://example.com/`。该外网站点没有单独断言，整段通过，未标环境限制，未重试。

按 README 起默认服务（未设置 HOST/PORT，数据库改到工作目录）：

```text
INFO:     Started server process [26048]
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

```text
netstat -ano | findstr :8000
TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       26048
```

直连结果（不经代理）：

```text
/ status=200 ctype=text/html; charset=utf-8
/api/me status=401 body={"detail":"未登录"}
/docs status=404
/redoc status=404
/openapi.json status=404
/health status=404
```

`POST /api/login` 使用 admin / admin123：`status 200 username admin must_change_password True`，随后带该 token 的 `/api/me` 为 200。检查后已停掉进程。停后 `127.0.0.1:8000` 没有 LISTENING，只剩 TIME_WAIT。

仓库没有 `/health`。README 没写健康检查路径，404 不记为缺陷。首页 200 且 `Content-Type` 为 `text/html`。

额外抽查（TestClient，临时库，未改仓库）里这些是通过的：非 http/https 网址 400；SQL 注入式用户名 401；过期 token 401；第二个用户看不到、改不了、删不了第一个用户的链接（404）；带用户信息的网址仍可保存，但 `icon_url` 去掉了用户信息（`https://alice:s3cret@example.com/x` → `https://example.com/favicon.ico`）。带 `\r\n` 的网址能存进库，但 `probe` 没有发出请求，错误是 `URL can't contain control characters`，本机监听端收到的是空连接。

## README 与实际不符处

1. README.md:65 写「共 20 项自动化测试」。`tests/test_app.py` 有 21 个 `test_` 函数，两次 pytest 都是 `21 passed`。多出来的是 tests/test_app.py:127 `test_change_password_revokes_other_sessions`。同句括号里的「登录/改密」没有点出「改密作废其他会话」。

2. README.md:12 写「页面加载不到图标时自动回退为名称首字占位」。static/index.html:368 在图片 `error` 时只 `img.remove()`，static/index.html:371 在设置 `src` 之后立刻给首字加上 `hidden`。static/index.html:19 的 `.hidden` 是 `display:none !important`。失败回调没有去掉 `hidden`。图标请求失败后，首字仍然隐藏，方块是空的。成功加载的路径不受影响。

3. README.md:7 标题写功能「均已测试覆盖」。自动化测试没有覆盖这三处界面行为：删除前确认（static/index.html:331）、登录后自动探测（static/index.html:247 与 static/index.html:491）、图标失败回退（static/index.html:368）。其中回退与 README 的描述不一致，见上一条。

4. README.md:70 真实流程自测只写了 `.venv/bin/python tests/live_selftest.py`。这是 Linux/macOS 路径。本机没有 `.venv\bin\python`。Windows 上实际跑通的命令是 `.venv\Scripts\python.exe tests\live_selftest.py`。上面的 pytest 小节（README.md:59-62）写了 Windows 路径，自测命令没有对称的一行。

以下对照过、与代码一致，不记为不符：单用户与 24 小时 token（app.py:27，过期比较已抽查）、首次登录只提示改密（app.py:128、static/index.html:245）、分组删除级联（app.py:405-406）且界面有确认（static/index.html:331）、网址仅 http/https（app.py:426）、默认监听 `127.0.0.1:8000`（app.py:577-578，netstat 已核对）、环境变量 `PORT` / `HOST` / `STARTDECK_DB_PATH` / `SD_INITIAL_USERNAME` / `SD_INITIAL_PASSWORD`（app.py:26-29、app.py:577-578）、2xx/3xx 算通且不跟随重定向（app.py:143-168，重定向用例已通过）、自测端口 8131（tests/live_selftest.py:15、tests/live_selftest.py:37）。

## 许可证与署名核查

仓库内三份声明互相一致，本次不改 LICENSE 与 UPSTREAM。

- LICENSE:1-3 是 MIT，版权行为 `Copyright (c) 2026 startdeck contributors`。正文是常见 MIT 许可，没有附加限制。
- README.md:82 写本项目 MIT、独立实现，上游也是 MIT，归因见 UPSTREAM.md。与 LICENSE 的许可类型一致，没有把上游作者写成自己的版权人。
- UPSTREAM.md:5-8 写上游为 Dashy（`https://github.com/Lissy93/dashy`），commit `a0005e8d6ea3dad611bc7c4daa1cd837dd338c79`，MIT，版权行 `Copyright (c) 2019-2026 Alicia Sykes <https://aliciasykes.com>`。NOTES.md:5-7 与这三行相同。
- 源码是单个 FastAPI + SQLite 文件加一个静态页，树里没有 Vue/Node 上游源码，也没有把上游 LICENSE 原文嵌进本项目 LICENSE。独立重写不把上游版权行放进自己的 LICENSE，同时在 UPSTREAM.md 署名，和 README.md:82 的说法一致。
- 未访问 GitHub。上游 commit 是否为 2026-10-16 的默认分支 HEAD、版权行是否与上游 LICENSE 逐字相同，均未核实，不把它写成错误，也不改 UPSTREAM.md。

DECISIONS.md:7-8 引用的 `10548aa083a2`、`05e19958`，以及 DECISIONS.md:20 的 `24d3616c`、DECISIONS.md:34 的 `4c234f91`，在本仓库执行 `git cat-file -t` 都是 `fatal: Not a valid object name`。本仓库只有提交 `a1ecd37`。这些提交号对不上，但文中描述的行为（默认绑定 127.0.0.1、favicon 去掉用户信息、关闭 `/docs`、改密作废其他会话）都在当前 `app.py` 里。这是快照里缺少被引用的 git 对象，不是 LICENSE 与 UPSTREAM 互相打架。没有证据证明那几行是编造的上游事实，所以不改 DECISIONS 里的提交号。

## 分级修复清单

### P0

无。安装、21 项 pytest、live_selftest、默认端口首页均已跑通。没有阻断启动或测试收集的错误。

### P1

无。不改代码。依据：

- 未登录访问 `/api/sections` 为 401；`/docs`、`/redoc`、`/openapi.json` 为 404（app.py:190-196，实请求已核对）。
- 链接与分组按 `user_id` 隔离。抽查中第二个用户对第一条用户的链接读/改/删都是 404。
- `file://`、`javascript:`、`data:` 等方案在 app.py:426 被拒绝。
- 带 `\r\n` 的网址虽然能通过 app.py:421 的校验，但 urllib 拒绝发送，监听端没有收到注入头。没有打成请求头注入。
- 默认只监听 127.0.0.1（app.py:577，netstat 已核对）。首次改密只提示、不强制，是 DECISIONS.md:38-40 已记录的产品决定；测试也依赖「未改密仍可调用接口」。不把它改成强制改密。

### P2

1. README.md:65 测试数量写成 20。修法：改成 21，并写上改密会作废其他会话。DECISIONS.md:9 的「pytest 20 项」一并改成 21。
2. static/index.html:368-371 图标失败不回退首字，与 README.md:12 相反。修法：不要在加载前给首字加 `hidden`；仅在 `load` 时隐藏或移除首字，`error` 时去掉图片并留下首字。
3. README.md:70 自测命令只有 `.venv/bin/python`。修法：补上 Windows 的 `.venv\Scripts\python tests\live_selftest.py`。
4. README.md:7「均已测试覆盖」过满。修法：改成接口行为有自动化测试，界面确认、自动探测和图标回退目前没有自动化测试。
5. app.py:421-427 `validate_url` 接受控制字符和端口 99999。修法：拒绝含 ASCII 控制字符的网址，并拒绝端口不在 1–65535 的网址。当前 urllib 会挡住控制字符请求，所以未升为 P1。
6. app.py:147 `build_opener` 保留了默认 `ProxyHandler`。本机 `getproxies()` 把 http/https 指到 `127.0.0.1:7890`；`http://example.com:99999/` 在 21ms 内得到 HTTP 502。修法：在 README 写明探测会沿用 `HTTP(S)_PROXY`；若希望探测不经过代理，再向 opener 传入空的 `ProxyHandler`。这是本机操作者自己的代理，未升为 P1。
7. app.py:250 与 app.py:280 用 `!=` 比较密码哈希。修法：改成 `hmac.compare_digest`。pbkdf2 的耗时占主导，未升为 P1。
8. app.py:93 与 app.py:253 会话 token 明文入库。修法：表里只存 token 哈希，校验时对请求头中的 token 做同样哈希。读到数据库的人已经能读到全部链接数据，未升为 P1。
9. 依赖警告：starlette 建议改用 `httpx2`，当前 httpx==0.28.1 仍能跑完测试。修法：保持 requirements 里的版本号不动。没有依赖冲突，本次不允许改已锁定的版本。
