# startdeck P2 第二轮审查

结论：本副本修前 `pytest` **21 passed**（8.68s），没有新的 P0，没有新的 P1。上一轮 `E:\muse-bridge\out\TASK-029-startdeck\review.md` 的 P2-1..P2-10 在本仓库仍然成立。这 10 条已按下面清单改完，改法与验证在 `fix-report.md`。收尾全量 pytest 仍是 `21 passed, 1 warning in 8.96s`。

下面行号均指修前的 `E:\muse-bridge\in\TASK-039-startdeck-p2`。命令原文在 `run.md`。

## 基线

Python `3.11.9`。虚拟环境 `E:\muse-bridge\work\TASK-039-startdeck-p2\.venv`，依赖按 `requirements-dev.txt` 安装，`fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1`。

```
21 passed, 1 warning in 8.68s
```

警告是 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 未改依赖版本。`tests/test_app.py` 有 21 个 `def test_`。`tests/live_selftest.py` 没有 `def test_`，不在这次收集里。修前 `git status --porcelain` 无输出。

上一轮已合入的项仍在，不开新项：默认 `127.0.0.1`（`app.py:577`）；favicon 去掉 userinfo（`app.py:55-65`）；关闭 `/docs` `/redoc` `/openapi.json`（`app.py:193-195`）；改密删除其他会话（`app.py:292-295`，对应用例 `tests/test_app.py:127`）。

## 十条现状

1. 图标失败不回退首字。`static/index.html:368` 在 `error` 时只 `img.remove()`。`static/index.html:371` 在设置 `src` 之后立刻 `letter.classList.add("hidden")`。`static/index.html:372` 只在 `load` 时删首字。`static/index.html:19` 的 `.hidden` 是 `display:none !important`。图片失败后首字仍被藏住。
2. 测试数量写成 20。`README.md:65`「共 20 项自动化测试」。实测 21 passed，多出的是 `tests/test_app.py:127` `test_change_password_revokes_other_sessions`。
3. 覆盖说法过满。`README.md:7`「均已测试覆盖」。确认框在 `static/index.html:331`、`static/index.html:377`；打开页面自动探测在 `static/index.html:247`；绿点/红点文案在 `static/index.html:281-286`；图标回退在 `static/index.html:365-372`。`tests/` 里没有这些断言。
4. 自测命令只有 bash。`README.md:69-71` 是 `.venv/bin/python tests/live_selftest.py`。同文件 `README.md:59-62` 已给 Windows 的 pytest 路径，自测段没有 `.venv\Scripts\python tests\live_selftest.py`。
5. `validate_url` 接受 CR/LF。`app.py:421-428` 只查 scheme 和 hostname。修前脚本原样返回 `VALIDATE_CRLF_ACCEPTED 'https://example.com/a\r\nX-Injected: 1'`。不升 P1：上一轮已记下本机 `http.client` 发请求前会拒绝控制字符，本轮不重复打外网探测。
6. 密码哈希用 `!=`。登录 `app.py:250`，改密 `app.py:280`。用户不存在时 `user is None or ...` 会短路，不算哈希。`app.py` 未 `import hmac`。不升 P1：`app.py:50-52` 的 pbkdf2 为 20 万次，占掉绝大部分时间，且是本机单用户。
7. 没有常见安全响应头。`app.py:190-196` 创建 FastAPI 时未加中间件。修前 `GET /` 为 200，`x-content-type-options`、`x-frame-options`、`content-security-policy`、`referrer-policy` 都是 `None`。令牌在 `localStorage`（`static/index.html:203`），不走 Cookie。
8. 外链只有 `noopener`。`static/index.html:359`：`rel="noopener"`。
9. 改密成功不收起横幅。`static/index.html:263-264` 只改文案并隐藏 `#pwForm`，不给 `#pwBanner` 加 `hidden`。登录时 `static/index.html:245` 和再次进入时 `static/index.html:489` 会按 `must_change_password` 切换，当次成功路径没有。
10. 搜索把 `%` 和 `_` 当通配符。`app.py:460-461` 直接 `like = f"%{q.strip()}%"`，没有 `ESCAPE`。修前：`q=%` 与 `q=_` 都返回 `['alpha', '100% done']`；`q=a_pha` 返回 `['alpha']`。查询带 `user_id`（`app.py:454`），只能搜到自己的链接。

`LICENSE` 与 `UPSTREAM.md` 本轮不改。未联网复核上游 commit。

## 分级修复清单

### P0

无。修前 21 项 pytest 已通过，TestClient `GET /` 为 200，登录 200。

### P1

无。鉴权、跨用户与改密废会话仍由现有测试覆盖。上面第 5、6、7、10 条保持 P2，理由见各条。

### P2

1. `static/index.html:368-372`。修法：加载前不隐藏首字；`error` 时删图片并去掉 `hidden`；`load` 成功再给首字加 `hidden`。监听在设置 `src` 之前注册。
2. `README.md:65`。修法：改成 21，并写上 `test_change_password_revokes_other_sessions`。
3. `README.md:7`。修法：删掉「均已测试覆盖」；写明后端用例已覆盖，确认框、自动探测、状态点文案、图标回退是页面行为、当前没有自动化测试。不加测试。
4. `README.md:69-71`。修法：保留 bash 命令，补 Windows：`.venv\Scripts\python tests\live_selftest.py`。
5. `app.py:421-428`。修法：`strip` 之后拒绝仍含 `\x00`–`\x20` 或 `\x7f` 的网址。
6. `app.py:250`、`app.py:280`。修法：先算一次 pbkdf2（用户不存在时用固定盐），再用 `hmac.compare_digest`。
7. `app.py:190`。修法：HTTP 中间件加 `X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy: no-referrer`。不加 CSP，避免拦掉页面内联脚本。
8. `static/index.html:359`。修法：`rel="noopener noreferrer"`。
9. `static/index.html:263-264`。修法：改密成功时给 `#pwBanner` 加上 `hidden`。
10. `app.py:459-462`。修法：把 `\`、`%`、`_` 转义后放入 `LIKE`，并 `ESCAPE '\'`。
