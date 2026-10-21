# TASK-016-startdeck 执行记录

开工时间：2026-10-21（本地执行方 Grok Build）

第一步：读仓库结构与 README，随后按 README 装环境并跑测试。

## 1. 环境

命令：

```
C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe --version
```

输出：

```
Python 3.11.9
```

说明：PATH 上第一个 `python` 指向 `E:\muse-bridge\env\TASK-016-startdeck\Scripts\python.exe`，该虚拟环境损坏（`Unable to create process using 'E:\python.exe'`）。本次改用上面的系统解释器，在工作目录新建 venv，不把 `.venv` 写进待审仓库。

命令：

```
C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe -m venv E:\muse-bridge\work\TASK-016-startdeck\venv
```

退出码 0。解释器：`E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe`。

## 2. 安装依赖

命令（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-016-startdeck\requirements.txt -r E:\muse-bridge\in\TASK-016-startdeck\requirements-dev.txt
```

结果摘要：`Successfully installed` fastapi-0.156.4 uvicorn-0.54.0 httpx-0.28.1 pytest-9.1.1，以及 starlette-1.9.0 pydantic-2.14.1 httpcore-1.0.9 等传递依赖。无版本冲突。

## 3. 全量测试

工作目录启动器把 `TEMP`/`TMP` 指到 `E:\muse-bridge\work\TASK-016-startdeck`，再在仓库根目录执行 pytest。

命令（退出码 0，耗时 7.75s）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

输出：

```
....................                                                     [100%]
============================== warnings summary ===============================
..\..\work\TASK-016-startdeck\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-016-startdeck\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
20 passed, 1 warning in 7.75s
```

## 4. 真实流程自测

命令（退出码 0，耗时 6.46s）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe tests/live_selftest.py
```

工作目录是仓库根，`TEMP`/`TMP` 指向 `E:\muse-bridge\work\TASK-016-startdeck`。输出片段（登录令牌已截断）：

```
PASS 首页能打开且是 startdeck 页面
PASS 登录成功 | {"token":"P-eGZ6zEh...AZ0GWM","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 单条探测-通 | {'link_id': 1, 'up': True, 'status_code': 200, 'response_ms': 30, 'error': None, ...}
PASS 单条探测-断 | {'link_id': 2, 'up': False, 'status_code': None, 'error': '[WinError 10061] 由于目标计算机积极拒绝，无法连接。', ...}
PASS 分组删除级联删链接
LIVE SELFTEST: ALL PASS
EXIT 0 ELAPSED 6.46s
```

脚本内「文档站」指向 `https://example.com/`。断言只要求本机链接为通、断口为断，不要求 example.com 为通。整段退出码 0，未因外网失败。

## 5. 按 README 起服务

数据库放到 `E:\muse-bridge\work\TASK-016-startdeck\smoke\startdeck.db`，未使用仓库内默认的 `data/startdeck.db`。`PORT=8000`。子进程用 `Process.terminate()` 关掉，没有使用 taskkill。

命令：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe E:\muse-bridge\work\TASK-016-startdeck\run_smoke.py
```

输出片段：

```
PORT8000_IN_USE_BEFORE False
STARTED pid=28044
CAME_UP True AFTER 1.42s
GET / STATUS 200 TYPE text/html; charset=utf-8 LEN 20691 SNIP b'<!DOCTYPE html>\n<html lang="zh-CN">...startdeck ...'
GET /health STATUS 404 TYPE application/json SNIP b'{"detail":"Not Found"}'
GET /api/health STATUS 404 TYPE application/json SNIP b'{"detail":"Not Found"}'
GET /healthz STATUS 404 TYPE application/json SNIP b'{"detail":"Not Found"}'
GET /docs STATUS 200 TYPE text/html; charset=utf-8 LEN 508 SNIP b'...href="https://cdn.j'
GET /openapi.json STATUS 200 TYPE application/json LEN 7573
GET /favicon.ico STATUS 404
STOPPED code=1 PORT8000_IN_USE_AFTER False
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:58334 - "GET / HTTP/1.1" 200 OK
```

退出码 1 是主动 terminate 的结果。结束后 8000 端口已释放。日志里的服务进程号是 5488，与 Popen 记录的 28044 不同；端口已释放，服务已停。

## 6. 补充核查（TestClient，未改仓库）

命令（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe E:\muse-bridge\work\TASK-016-startdeck\repro_checks.py
```

要点：

- 改密后，另一个仍未过期的 token 访问 `/api/me` 返回 200。
- `https://alice:s3cret@example.com/admin/page` 的 `icon_url` 为 `https://alice:s3cret@example.com/favicon.ico`。
- `javascript:` 与 `file://` 返回 400。`http://169.254.169.254/latest/meta-data/` 被接受并入库（只做了校验和写入，没有对该地址发起连接）。
- 搜索 `q=%` 命中当时全部 5 条链接。
- `/docs` 状态 200，正文含 `cdn` / `jsdelivr`。

## 7. 改代码前的 git 状态

```
git -C E:\muse-bridge\in\TASK-016-startdeck status --porcelain
```

无输出，退出码 0。跑测试和起服务没有改动仓库文件。

## 8. P1-1 验证

改默认监听地址后重跑。冒烟日志：`Uvicorn running on http://127.0.0.1:8000`，`GET /` 200。pytest：`20 passed, 1 warning in 7.66s`。live_selftest：`LIVE SELFTEST: ALL PASS`，`EXIT 0 ELAPSED 6.51s`。细节见 fix-report.md 的 P1-1。

## 9. P1-2 / P1-3 与最终全量测试

P1-2 之后 pytest：`20 passed, 1 warning in 7.51s`。favicon 核对：`https://alice:s3cret@example.com/admin/page -> https://example.com/favicon.ico`。

P1-3 之后：`GET /docs 404`，`GET /redoc 404`，`GET /openapi.json 404`，`GET / 200`。pytest：`20 passed, 1 warning in 7.81s`。

全部改动落地后的最终 pytest（退出码 0）：

```
20 passed, 1 warning in 9.11s
```

最终 live_selftest（退出码 0）：

```
LIVE SELFTEST: ALL PASS
EXIT 0 ELAPSED 8.38s
```

`git -C E:\muse-bridge\in\TASK-016-startdeck status --porcelain`：

```
 M README.md
 M app.py
```





