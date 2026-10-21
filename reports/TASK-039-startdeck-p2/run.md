# TASK-039-startdeck-p2 执行日志

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-039-startdeck-p2`。本轮只处理上一轮 review 的 P2-1..P2-10。

## 环境

命令：`python --version`

```
Python 3.11.9
```

上一轮虚拟环境仍在：`E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe`（Test-Path = True）。本轮在 `E:\muse-bridge\work\TASK-039-startdeck-p2\.venv` 另建环境，避免和上一轮混用。

命令：`python -m venv E:\muse-bridge\work\TASK-039-startdeck-p2\.venv`  
退出码 0。

命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-039-startdeck-p2\requirements-dev.txt
```

退出码 0。装上的直接依赖：`fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1`（均来自本地缓存 wheel，未改 requirements 版本）。pip 提示可升级自身，未执行升级。

## 修前基线测试

命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B -m pytest E:\muse-bridge\in\TASK-039-startdeck-p2\tests -q --rootdir E:\muse-bridge\in\TASK-039-startdeck-p2 -p no:cacheprovider
```

```
21 passed, 1 warning in 8.68s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。按任务不改已有依赖版本。`tests/live_selftest.py` 没有 `def test_`，不在这次 pytest 收集里。

## 修前行为探测

命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-039-startdeck-p2\pre_fix_check.py
```

数据库：`E:\muse-bridge\work\TASK-039-startdeck-p2\pre-fix.db`。退出码 0。摘要：

```
VALIDATE_CRLF_ACCEPTED 'https://example.com/a\r\nX-Injected: 1'
HOME_STATUS 200
SEC_HEADERS {'x-content-type-options': None, 'x-frame-options': None, 'content-security-policy': None, 'referrer-policy': None}
LOGIN 200
SEARCH '%' ['alpha', '100% done']
SEARCH '_' ['alpha', '100% done']
SEARCH 'a_pha' ['alpha']
SEARCH '100%' ['100% done']
```

修前 `git status --porcelain` 无输出。

## 逐条修改后的全量 pytest

解释器始终是 `E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe`。每条命令都是：

```
python.exe -B -m pytest E:\muse-bridge\in\TASK-039-startdeck-p2\tests -q --rootdir E:\muse-bridge\in\TASK-039-startdeck-p2 -p no:cacheprovider
```

退出码都是 0。结果行：

- P2-1 之后：`21 passed, 1 warning in 8.47s`
- P2-2 之后：`21 passed, 1 warning in 8.46s`
- P2-3 之后：`21 passed, 1 warning in 8.46s`
- P2-4 之后：`21 passed, 1 warning in 7.99s`
- P2-5 之后：`21 passed, 1 warning in 8.55s`
- P2-6 之后：`21 passed, 1 warning in 8.50s`
- P2-7 之后：`21 passed, 1 warning in 8.46s`
- P2-8 之后：`21 passed, 1 warning in 8.51s`
- P2-9 之后：`21 passed, 1 warning in 8.50s`
- P2-10 之后：`21 passed, 1 warning in 8.57s`
- 收尾重跑：`21 passed, 1 warning in 8.96s`

每次警告都是同一句 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## 行为探测（工作目录脚本，未改 tests/）

P2-5：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-039-startdeck-p2\check_p2_5.py
```

退出码 0。嵌入的 CR/LF、中间空格、`\x7f` 为 400；普通 http/https 通过。仅尾部换行会被原有 `strip` 去掉后再通过。

P2-7：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-039-startdeck-p2\check_p2_7.py
```

退出码 0。`GET /` 200 与 `GET /api/me` 401 都带 `nosniff`、`DENY`、`no-referrer`。

P2-10：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-039-startdeck-p2\check_p2_10.py
```

退出码 0。`q=%` 只返回 `100% done`；`q=a_pha` 只返回 `a_pha`，不再命中 `alpha`。

本轮没有跑 `tests/live_selftest.py`。该脚本会请求 `https://example.com/`，任务禁止抓取外部页面。Windows 命令只写进 README，没有当成本轮已执行的自测。

## 收尾 diff 与状态

`git diff --stat`：

```
 README.md         | 12 ++++++++++--
 app.py            | 43 +++++++++++++++++++++++++++++++++++++++----
 static/index.html | 12 ++++++++----
 3 files changed, 57 insertions(+), 10 deletions(-)
```

`git status --porcelain` 见 fix-report.md 末尾。未 commit，未 push。
