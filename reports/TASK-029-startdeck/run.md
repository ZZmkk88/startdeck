# TASK-029-startdeck 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-029-startdeck`。先审查再修 P0/P1。

## 环境

- 系统 Python：`python --version` → `Python 3.11.9`（满足 README「3.10+」）。`py --version` 失败：`Unable to create process using 'E:\python.exe --version'`，未使用 py 启动器。
- 虚拟环境放在工作目录，避免把依赖树写进待审仓库：`E:\muse-bridge\work\TASK-029-startdeck\.venv`
- `git status --porcelain` 开工时无输出（工作区干净）。HEAD：`a1ecd37 docs(startdeck): DECISIONS.md records TASK-016 review merge decisions`

## 1. 装依赖

命令：

```
python -m venv E:\muse-bridge\work\TASK-029-startdeck\.venv
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-029-startdeck\requirements-dev.txt
```

结果：exit 0。装上 fastapi==0.156.4、uvicorn==0.54.0、httpx==0.28.1、pytest==9.1.1 及其依赖（starlette 1.9.0、pydantic 2.14.1 等）。末行：`Successfully installed ... fastapi-0.156.4 ... pytest-9.1.1 ... uvicorn-0.54.0`

## 2. 全量 pytest

命令（`-B` 不写 pyc，避免往仓库里丢 `__pycache__`）：

```
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -B -m pytest E:\muse-bridge\in\TASK-029-startdeck\tests -q --rootdir E:\muse-bridge\in\TASK-029-startdeck
```

输出：

```
.....................                                                    [100%]
============================== warnings summary ===============================
..\..\work\TASK-029-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-029-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 1 warning in 8.72s
```

exit 0。21 passed。README 写的是 20 项。警告不导致失败：Starlette 提示 TestClient 仍用 httpx，建议 httpx2。未改依赖版本。

## 3. 真实流程自测 live_selftest

临时目录改到工作目录（脚本自己会 `tempfile.mkdtemp`，跟随 TEMP）。命令：

```
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-029-startdeck\run_live.py
```

`run_live.py` 把 TEMP/TMP 设为 `E:\muse-bridge\work\TASK-029-startdeck` 后执行仓库里的 `tests/live_selftest.py`（脚本固定端口 8131）。exit 0。末行：`LIVE SELFTEST: ALL PASS`。

输出摘要（登录响应里的 token 属于已关掉的临时库，这里略去）：

```
PASS 首页能打开且是 startdeck 页面
PASS 登录成功 | {"token":"<省略>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建分组「工作」
PASS 建分组「服务」
PASS 加链接：本机面板 / 断掉的服务 / 文档站
PASS 链接自动带 favicon 地址 | http://127.0.0.1:8131/favicon.ico
PASS 分组结构正确：工作 1 条、服务 2 条
PASS 搜索「文档」命中 1 条
PASS 单条探测-通 | up True, status_code 200, response_ms 7
PASS 单条探测-断 | up False, error '[WinError 10061] 由于目标计算机积极拒绝，无法连接。'
PASS 全部探测：本机通、断口断
PASS 链接移动到「服务」分组
PASS 移动后：工作 0 条、服务 3 条
PASS 编辑链接名称生效
PASS 删除链接成功
PASS 删后查不到
PASS 删除分组成功
PASS 分组删除级联删链接
LIVE SELFTEST: ALL PASS
```

`check-all` 会请求 `https://example.com/`（脚本里的「文档站」）。该条断言不要求它通。本次整段通过，未标环境限制。

## 4. 按 README 起服务（默认 HOST 不设置，PORT=8000）

数据库放到 `E:\muse-bridge\work\TASK-029-startdeck\server-check.db`，避免在仓库里生成 `data/startdeck.db`。子进程环境去掉 `HOST`，用来看代码默认值。父进程里 `HOST`、`PORT` 均为空（`PARENT_HOST None` / `PARENT_PORT None`）。

命令：

```
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-029-startdeck\audit_and_server.py
```

服务日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

netstat 监听行：

```
TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       6788
```

同一次 netstat 里还有若干到 `127.0.0.1:8000` 的 TIME_WAIT，以及一条远端 IPv6 地址文本里带 `8000`、进程号 21832 的连接，不是这个 uvicorn（进程 6788）。

HTTP 结果：

```
HTTP 200 GET /            ctype=text/html; charset=utf-8
  body 以 <!DOCTYPE html> 开头，title 为 startdeck · 个人起始页
  sec_headers (none)
HTTP 404 GET /health      {"detail":"Not Found"}
HTTP 404 GET /api/health  {"detail":"Not Found"}
HTTP 404 GET /docs        {"detail":"Not Found"}
HTTP 404 GET /redoc       {"detail":"Not Found"}
HTTP 404 GET /openapi.json {"detail":"Not Found"}
HTTP 401 GET /api/me      {"detail":"未登录"}
HTTP 401 GET /api/sections {"detail":"未登录"}
HTTP 200 POST /api/login  username=admin, must_change_password=true（token 略）
```

随后 `proc.terminate()`，输出 `SERVER_STOPPED 1`（进程已退出）。README 没有写健康检查路径；`/health` 与 `/api/health` 是 404。

同一次脚本还打印了路由表：除 `POST /api/login` 与 `GET /` 外，其余 API 的参数里都有 `user`（`current_user`）。favicon 样例：`https://alice:s3cret@example.com/admin` → `https://example.com/favicon.ico`；密码里含 `@`、IPv6 带用户信息也同样去掉了用户信息。本地 302 探测：`status_code 302`、`up True`、跳转目标命中数 `target_hits 0`。

## 5. 双用户隔离与 CRLF 网址

命令：

```
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-029-startdeck\audit_isolation.py
```

```
A sees sections ['A的分组']
B sees sections ['B的分组']
A get B link 404
B get A link 404
A delete B section 404
B delete A link 404
A rename B section 404
B still has link 200
A still has link 200
validate_crlf 仍接受含 CR/LF 的网址
probe_crlf error: URL can't contain control characters. '/\\r\\nX-Injected: yes' (found at least '\\r')
```

隔离成立。含控制字符的网址能通过 `validate_url` 并被存住，但本机 Python 3.11 的 `http.client` 在真正发请求前拒绝，探测结果为 down。

## 6. 审查结论之后重跑全量 pytest

未改仓库源码（无 P0/P1）。收尾重跑：

```
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -B -m pytest E:\muse-bridge\in\TASK-029-startdeck\tests -q --rootdir E:\muse-bridge\in\TASK-029-startdeck -p no:cacheprovider
```

```
.....................                                                    [100%]
============================== warnings summary ===============================
..\..\work\TASK-029-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-029-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 1 warning in 8.47s
```

exit 0。

## 7. git status --porcelain

```
git -C E:\muse-bridge\in\TASK-029-startdeck status --porcelain
```

无输出，exit 0。仓库相对 HEAD `a1ecd37` 没有改动。审查结论是 P0/P1 为空，所以没有改源码；空状态是这个结果，不是改完又被还原。
