# startdeck 验收

结论：按 README 能在本机装好并跑通。pytest 20 项通过，真实流程自测全部 PASS，`app.py` 监听 8000 时首页返回 200。没有健康检查路由。没有 P0。P1 有 4 项，本次改其中 3 项；改密不撤销其他会话会让现有测试失败，且不能改测试，该项不落地。

## 本地跑通记录

环境：系统解释器 `C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe`，版本 `Python 3.11.9`。PATH 上第一个 `python`（`E:\muse-bridge\env\TASK-016-startdeck\Scripts\python.exe`）已损坏，报 `Unable to create process using 'E:\python.exe'`。虚拟环境建在 `E:\muse-bridge\work\TASK-016-startdeck\venv`，没有写进仓库。

安装（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

`Successfully installed` fastapi-0.156.4、uvicorn-0.54.0、httpx-0.28.1、pytest-9.1.1，以及 starlette-1.9.0、pydantic-2.14.1 等传递依赖。没有版本冲突。

全量测试（退出码 0，7.75s）。`TEMP`/`TMP` 指到工作目录后，在仓库根执行：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
....................                                                     [100%]
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
20 passed, 1 warning in 7.75s
```

警告来自已安装的 `fastapi\testclient.py:1`，测试本身通过。

真实流程自测（退出码 0，6.46s）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe tests/live_selftest.py
```

```
PASS 首页能打开且是 startdeck 页面
PASS 登录成功 | {"token":"P-eGZ6zEh...AZ0GWM","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 单条探测-通 | {'link_id': 1, 'up': True, 'status_code': 200, 'response_ms': 30, 'error': None, ...}
PASS 单条探测-断 | ... 'error': '[WinError 10061] 由于目标计算机积极拒绝，无法连接。' ...
LIVE SELFTEST: ALL PASS
```

脚本里的「文档站」是 `https://example.com/`。断言不要求该站为通。整段没有因外网失败。

按 README 起 `app.py`（`PORT=8000`，数据库在工作目录 `smoke\startdeck.db`）。约 1.42s 后端口可连。首页与健康检查：

```
GET / STATUS 200 TYPE text/html; charset=utf-8 LEN 20691
GET /health STATUS 404 {"detail":"Not Found"}
GET /api/health STATUS 404 {"detail":"Not Found"}
GET /healthz STATUS 404 {"detail":"Not Found"}
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

服务日志确认进程已接请求。结束后 `PORT8000_IN_USE_AFTER False`。`STOPPED code=1` 是 `Process.terminate()` 的退出码，服务已停。

代码里没有 `/health`。README 也没有写健康检查。首页就是可用的入口。

## README 与实际不符处

下列以本次读到的原文行号为准（改代码之前）。

1. `README.md:12` 写「页面加载不到图标时自动回退为名称首字占位」。`static/index.html:371` 在图片尚未加载时就给首字加上 `hidden`，`static/index.html:368` 的 `error` 只执行 `img.remove()`，没有去掉 `hidden`。`static/index.html:19` 的 `.hidden` 是 `display:none !important`。图片失败后首字仍然不可见。

2. `README.md:7` 写功能清单「与代码实现一一对应，均已测试覆盖」。界面删除确认在 `static/index.html:331`，首字占位在 `static/index.html:352` 与 `:368`，绿/红点在 `static/index.html:281-286`，顶部输入即过滤在 `static/index.html:414`。这些都没有自动化测试。`tests/test_app.py` 只有接口测试。`README.md:64` 列举的 20 项与这次 pytest 的 `20 passed` 一致，覆盖的是接口，不是上述界面行为。

3. `README.md:26`、`README.md:35`、`README.md:38` 让用户打开 `http://localhost:8000`，并只说明默认端口 8000。`app.py:554` 是 `host="0.0.0.0"`。冒烟日志原文：`Uvicorn running on http://0.0.0.0:8000`。进程监听所有网卡。环境变量表 `README.md:42-46` 没有监听地址一项。

4. `README.md:66-70` 的真实流程自测只给了 `.venv/bin/python tests/live_selftest.py`。同文 `README.md:58-62` 为 pytest 写了 Windows 命令，自测没有对应的 `.venv\Scripts\python tests/live_selftest.py`。脚本本身在 Windows 上已跑通（见上节，退出码 0）。

5. `README.md:14` 把探测结果写成绿点（通，带毫秒）和红点（不通，带原因）。`static/index.html:403-411` 在「探测全部」请求失败时不清除 `checking`。`static/index.html:284` 会一直显示「探测中…」。同文件 `:410` 的注释写「状态点保持灰色」，`.dot.checking` 在 `static/index.html:75` 用的是强调色，不是灰色。

6. `README.md:7-14` 的功能清单没有匿名文档站。实际 `GET /docs` 与 `GET /openapi.json` 返回 200（冒烟输出）。`/docs` 正文含 `https://cdn.j`。已安装的 FastAPI 0.156.4 默认把 Swagger 脚本指到 `https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js`（`venv\Lib\site-packages\fastapi\openapi\docs.py:79`），CSS 在该文件 `:92`，ReDoc 脚本在 `:236`。入口来自 `app.py:185` 未关闭 `docs_url` / `redoc_url` / `openapi_url`。本次冒烟没有单独请求 `/redoc`。

已核对且与代码一致的部分：默认端口 8000（`README.md:44`，`app.py:554`）、数据库路径 `data/startdeck.db`（`README.md:45`，`app.py:26`）、初始账号 admin / admin123（`README.md:38` 与 `:46`，`app.py:28-29`）、Token 24 小时（`README.md:9`，`app.py:27`）、网址仅 http/https（`README.md:11`，`app.py:404`）、2xx/3xx 算通（`README.md:14`，`app.py:165`）、删除分组级联删除链接（`README.md:10`，`app.py:383-384`）、自测端口 8131（`README.md:66`，`tests/live_selftest.py:15`）。这次没有使用默认数据库路径，避免在仓库里生成 `data/startdeck.db`；`app.py:77` 会创建父目录，这一行没有单独再跑一遍默认路径。

## 许可证与署名核查

本仓库三处说法彼此一致：

- `LICENSE:1-3` 是 MIT 全文，版权行是 `Copyright (c) 2026 startdeck contributors`。
- `README.md:79-81` 写本项目 MIT，并写上游也是 MIT，归因见 `UPSTREAM.md`。
- `UPSTREAM.md:5-8` 与 `NOTES.md:5-7` 的项目（Dashy）、`source_commit`（`a0005e8d6ea3dad611bc7c4daa1cd837dd338c79`）、许可证（MIT）、版权行（`Copyright (c) 2019-2026 Alicia Sykes <https://aliciasykes.com>`）文字相同。

`UPSTREAM.md:17-19` 写代码是独立重写、未复制上游源码。仓库里是 Python / FastAPI / 单页 HTML，没有 Vue 源码或 YAML 配置拷贝。这与「独立实现」的文件构成一致。

以下事实本次不能核实：上游提交是否就是 2026-10-16 的 `4.8.7`，以及版权行是否逐字来自上游 LICENSE。`UPSTREAM.md:12-16` 与 `NOTES.md:3-7` 称 2026-10-21 通过 GitHub 接口实查。任务禁止抓取外部页面，所以这几条标为未核实。没有确凿错误，不改 `LICENSE` 和 `UPSTREAM.md`。

另有一处署名范围：`app.py:136` 与 `NOTES.md:42-43` 写探测口径与团队项目 sitepulse 一致。`UPSTREAM.md` 只署名 Dashy。本仓库里看不到 sitepulse 源码，`probe` 是用标准库写的，不能据此认定复制了另一份代码。不改 `UPSTREAM.md`。

## 分级修复清单

### P0

无。安装、pytest、live_selftest、8000 首页都已跑通。

### P1

1. `app.py:554` 默认 `host="0.0.0.0"`，同时 `README.md:38` 公开默认口令 admin / admin123，改密前接口可用（`README.md:9` 只要求提示；`tests/test_app.py:95-98` 依赖这一点）。同网段可以登录并改完全部链接。修法：默认改为 `127.0.0.1`，增加环境变量 `HOST`；在 `README.md:26`、`README.md:35`、`README.md:42-46` 写明默认只监听本机。

2. `app.py:61-62` 用整个 `netloc` 生成 `icon_url`。实测 `https://alice:s3cret@example.com/admin/page` 得到 `icon_url` `https://alice:s3cret@example.com/favicon.ico`。页面会用这个地址自动请求图标（`static/index.html:369`）。修法：去掉 URL 里的用户信息，只保留主机和端口。

3. `app.py:185` 开启默认文档页，`/docs` 从 jsDelivr 加载脚本，与首页同源；会话令牌在 `static/index.html:203` 的 `localStorage`。外部脚本可以读到令牌。修法：关闭 `docs_url`、`redoc_url`、`openapi_url`。

4. `app.py:261-274` 改密后不删除其他会话。实测：用 token A 改密后，另一个 token B 访问 `/api/me` 仍是 200。修法本应删掉同用户的其他 session。本次不改代码。`tests/test_app.py:66-68` 的 module 级 token 会在 `tests/test_app.py:117-122` 用另一个 token 把密码改回去时被撤销，后面的用例会 401。禁止改测试，也不能把会失败的改动留在工作区后再撤回，所以该项不落地。

### P2

1. `static/index.html:368-372` 图标失败不恢复首字。修法：`error` 时去掉首字的 `hidden`。

2. `static/index.html:403-411` 「探测全部」失败后停在「探测中」。修法：失败时清掉 `checking`。

3. `app.py:69-73` 的 `with get_conn()` 只提交事务，不关闭连接（sqlite3 连接的上下文管理器不 close）。修法：在 `finally` 里 `close()`。

4. `app.py:437-440` 搜索把用户输入直接包进 `LIKE %...%`。实测 `q=%` 命中全部链接。单用户只能看到自己的数据。修法：转义 `%` 和 `_`。

5. `app.py:399-406` 接受带空格的主机名，也接受 `http://169.254.169.254/latest/meta-data/`（本次只校验并入库，没有连接该地址）。`javascript:` 与 `file://` 已是 400。修法：拒绝空白主机名；链路本地地址可单独拒绝。不要封禁 `127.0.0.1`，测试和本机探测依赖它。

6. `app.py:239` 与 `app.py:265` 用 `!=` 比较密码哈希。修法：改为 `hmac.compare_digest`。

7. `requirements-dev.txt:2` 的 `httpx==0.28.1` 触发 Starlette 弃用警告，测试仍通过，安装也没有冲突。修法：等依赖上游提供 httpx2 再改。本次不改版本号。

8. `tests/live_selftest.py:83-85` 把 favicon 断言的第一支拼成没有斜杠的地址，第二支只要以 `/favicon.ico` 结尾就通过。修法：收紧断言。禁止改测试，本次不动。

9. `README.md:69` 缺少 Windows 自测命令。修法：补 `.venv\Scripts\python tests/live_selftest.py`。这不是 P0/P1，本次不改这一行。
