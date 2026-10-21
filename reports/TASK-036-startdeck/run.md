# TASK-036-startdeck 执行记录

开工时间：2026-10-21

（以下按步骤追加真实命令与输出，未执行的命令不记为已验证。）

## 0. 环境

工作目录：`E:\muse-bridge\in\TASK-036-startdeck`

```text
python --version
Python 3.11.9
```

```text
git rev-parse HEAD
a1ecd377a058f1ac87a00a97ebafac6cd7023a89

git log --oneline -20
a1ecd37 docs(startdeck): DECISIONS.md records TASK-016 review merge decisions

git branch -v
* main a1ecd37 docs(startdeck): DECISIONS.md records TASK-016 review merge decisions
```

DECISIONS.md 引用的对象在本仓库不存在（`git cat-file -t` 均 fatal: Not a valid object name）：

- `10548aa083a2`
- `24d3616c`
- `4c234f91`
- `05e19958`

## 1. 安装依赖

按 README「Windows（PowerShell）」在仓库内建虚拟环境并安装运行依赖与测试依赖。

```text
python -m venv .venv
```

退出码 0，无标准输出。

```text
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

退出码 0。关键行：

```text
Collecting fastapi==0.156.4 (from -r requirements.txt (line 1))
Collecting uvicorn==0.54.0 (from -r requirements.txt (line 2))
Collecting httpx==0.28.1 (from -r requirements-dev.txt (line 2))
Collecting pytest==9.1.1 (from -r requirements-dev.txt (line 3))
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 certifi-2026.10.19 click-8.5.0 colorama-0.4.6 fastapi-0.156.4 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.1 packaging-26.3 pluggy-1.7.0 pydantic-2.14.1 pydantic-core-2.50.1 pygments-2.21.0 pytest-9.1.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

pip 提示可升级（24.0 -> 26.2.2），未执行升级。

## 2. 全量 pytest

临时目录改到任务工作目录（避免测试写系统 TEMP）。包装脚本：`E:\muse-bridge\work\TASK-036-startdeck\run-pytest.cmd`。

```text
cmd /c E:\muse-bridge\work\TASK-036-startdeck\run-pytest.cmd
```

脚本内容要点：`TEMP`/`TMP`=`E:\muse-bridge\work\TASK-036-startdeck\tmp`，`PYTHONIOENCODING=utf-8`，然后 `.\.venv\Scripts\python.exe -m pytest tests/ -q`。

退出码 0。输出：

```text
.....................                                                    [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-036-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 1 warning in 10.69s
PYTEST_EXIT=0
```

README 写「共 20 项」，本次实际收集并通过 21 项。

## 3. 真实流程自测 live_selftest

包装脚本：`E:\muse-bridge\work\TASK-036-startdeck\run-live.cmd`（同样把 TEMP/TMP 指到工作目录）。

```text
cmd /c E:\muse-bridge\work\TASK-036-startdeck\run-live.cmd
```

退出码 0。脚本自己在 8131 端口起 uvicorn，跑完 `proc.terminate()`。输出节选（登录行里的 token 已截断，临时库已随进程退出失效）：

```text
PASS 首页能打开且是 startdeck 页面
PASS 登录成功 | {"token":"<截断>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建分组「工作」
PASS 建分组「服务」
PASS 加链接：本机面板
PASS 加链接：断掉的服务
PASS 加链接：文档站
PASS 链接自动带 favicon 地址 | http://127.0.0.1:8131/favicon.ico
PASS 分组结构正确：工作 1 条、服务 2 条
PASS 搜索「文档」命中 1 条
PASS 单条探测-通 | {'link_id': 1, 'up': True, 'status_code': 200, 'response_ms': 17, 'error': None, 'checked_at': '2026-10-21T11:31:34+00:00'}
PASS 单条探测-断 | {'link_id': 2, 'up': False, 'status_code': None, 'response_ms': None, 'error': '[WinError 10061] 由于目标计算机积极拒绝，无法连接。', 'checked_at': '2026-10-21T11:31:36+00:00'}
PASS 全部探测：本机通、断口断
PASS 链接移动到「服务」分组
PASS 移动后：工作 0 条、服务 3 条
PASS 编辑链接名称生效
PASS 删除链接成功
PASS 删后查不到
PASS 删除分组成功
PASS 分组删除级联删链接
LIVE SELFTEST: ALL PASS
LIVE_EXIT=0
```

说明：自测会创建 `https://example.com/` 并在「探测全部」里请求它。该步没有单独断言外网结果，整段退出码 0，未出现需要标成「环境限制」的失败。未重试。

## 4. 按 README 启动默认服务

数据库改到工作目录，避免在仓库里生成 `data/startdeck.db`（本任务禁止 del/rm，生成后无法删除）。未设置 `HOST`/`PORT`，以核对默认绑定。

```text
cmd /c E:\muse-bridge\work\TASK-036-startdeck\start-server.cmd
```

启动日志：

```text
INFO:     Started server process [26048]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

监听（只保留本服务那一行）：

```text
netstat -ano | findstr :8000
TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       26048
```

进程号 26048 与 uvicorn 日志一致。绑定地址是 `127.0.0.1`，不是 `0.0.0.0`。

首页与相关路由（`check-server.py`，直连、不走代理）：

```text
/ status=200 ctype=text/html; charset=utf-8 body=b'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, ini'
/api/me status=401 body=b'{"detail":"\xe6\x9c\xaa\xe7\x99\xbb\xe5\xbd\x95"}'
/docs status=404 body=b'{"detail":"Not Found"}'
/redoc status=404 body=b'{"detail":"Not Found"}'
/openapi.json status=404 body=b'{"detail":"Not Found"}'
/health status=404 body=b'{"detail":"Not Found"}'
```

`/api/me` 的 body 是 UTF-8「未登录」。仓库没有 `/health` 路由，README 也没写健康检查路径，404 不记为缺陷。首页 200 且 Content-Type 为 `text/html`。

默认账号（`check-login.py`，不打印 token）：

```text
status 200 username admin must_change_password True token_len 43
me_status 200 username admin must_change_password True
```

停止方式：结束上述后台进程（未使用 taskkill）。停止后 `netstat` 对 `127.0.0.1:8000` 只剩 `TIME_WAIT`，没有 `LISTENING`。

## 5. 本地抽查（不改仓库）

脚本在 `E:\muse-bridge\work\TASK-036-startdeck\`，数据库在同目录 `tmp\`。结论见 review.md。关键原始行：

- `file://`、`javascript:`、`data:`、`gopher:`、`ftp://` 创建链接均为 400「只支持 http/https 网址」
- `https://alice:s3cret@example.com/x` 保存成功，`icon_url` 为 `https://example.com/favicon.ico`，图标地址里没有 `s3cret`
- 把会话 `expires_at` 改到过去后，`/api/me` 为 401「登录已过期，请重新登录」
- 直接插入第二个用户后，该用户 `GET /api/sections` 为 `[]`；读取/修改/删除第一个用户的链接均为 404
- `GET /docs`、`/redoc`、`/openapi.json` 均为 404
- `validate_url` 接受了带 `\r\n`、`\n`、`\x00`、`\t` 的 http URL
- 对 `http://127.0.0.1:<port>/path\r\nX-Injected: pwned` 调用 `probe`：本机监听端没有收到连接，返回 `URL can't contain control characters`
- `urllib.request.getproxies()`：`http`/`https`/`all` 均为 `http://127.0.0.1:7890`。环境变量名存在：`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`、`NO_PROXY`
- `http://example.com:99999/` 创建成功，探测结果 `status_code=502`，`response_ms=21`，`up=false`，`error=HTTP 502`（21ms 内的 HTTP 502 来自本机代理，不是本机直接报端口非法）

## 6. 审查结束后重跑全量 pytest

未改仓库源码。再次执行同一包装脚本。

```text
cmd /c E:\muse-bridge\work\TASK-036-startdeck\run-pytest.cmd
```

退出码 0。

```text
.....................                                                    [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-036-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 1 warning in 10.00s
PYTEST_EXIT=0
```

## 7. 收尾 git status

```text
git status --porcelain
```

退出码 0，无输出。未改仓库源码，空状态是预期。


