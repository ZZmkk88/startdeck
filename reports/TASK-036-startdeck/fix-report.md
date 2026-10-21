# startdeck 修复记录

结论：review.md 的 P0 为 0 条，P1 为 0 条。按任务只修 P0 和 P1，本次没有修改仓库源码，也没有改测试、依赖版本、LICENSE、UPSTREAM。

## P0 / P1

无条目。没有「问题编号 / 改动文件 / 改法」可填。未改任何仓库文件，所以没有单条修复后的单独测试；验证就是文末的全量 pytest。

P0 为空的依据：`21 passed`，live_selftest `ALL PASS`，`python app.py` 在 `127.0.0.1:8000` 首页 200。详见 review.md「本地跑通记录」。

P1 为空的依据：未登录 401、文档入口 404、越权 404、非 http(s) 网址 400、控制字符没有打到监听端。这些已在 review.md 写明命令输出与文件行号。不够格升为 P1 的项留在 P2，本次不改。

## 未修的 P2（逐条）

1. 问题编号 P2-1。文件 README.md:65，相关用例 tests/test_app.py:127。改法：把「20 项」改成「21 项」。本次未改。原因：文档计数错误，不是跑不起来，也不是安全、数据或权限缺陷。
2. 问题编号 P2-2。文件 static/index.html:368 与 static/index.html:371（样式 static/index.html:19），对应说明 README.md:12。改法：图标 `error` 时留下名称首字，不要提前加 `hidden`。本次未改。原因：只影响图标加载失败时的占位显示，链接和接口仍可用。
3. 问题编号 P2-3。文件 README.md:70。改法：补 Windows 自测命令 `.venv\Scripts\python tests\live_selftest.py`。本次未改。原因：说明缺了一行；用 Windows 路径已经跑通，见下方全量测试之外的 live_selftest（run.md 第 3 节，`LIVE_EXIT=0`）。
4. 问题编号 P2-4。文件 README.md:7。改法：收窄「均已测试覆盖」的说法。本次未改。原因：文案过满，不阻断运行。
5. 问题编号 P2-5。文件 app.py:421-427。改法：拒绝控制字符和非法端口。本次未改。原因：`probe` 对 `\r\n` 网址没有发出请求（错误原文 `URL can't contain control characters`），没有形成请求头注入。
6. 问题编号 P2-6。文件 app.py:147。改法：文档说明探测会走 `HTTP(S)_PROXY`，或显式关闭代理。本次未改。原因：本机代理是操作者自己的 `127.0.0.1:7890`，关闭它会改变出网语义。
7. 问题编号 P2-7。文件 app.py:250 与 app.py:280。改法：密码哈希比较改用 `hmac.compare_digest`。本次未改。原因：比较耗时被 pbkdf2 盖过，不是可直接利用的缺陷。
8. 问题编号 P2-8。文件 app.py:93 与 app.py:253。改法：会话表只存 token 哈希。本次未改。原因：能读到数据库的人已经能读到全部链接；改动面大于本次收益。
9. 问题编号 P2-9。文件 requirements-dev.txt:3（httpx==0.28.1）与已安装的 starlette。改法：保持版本号。本次未改。原因：测试通过，警告不是依赖冲突；任务禁止在无冲突时改已有依赖版本。

## 最终全量测试

未改源码之后执行。命令：

```text
cmd /c E:\muse-bridge\work\TASK-036-startdeck\run-pytest.cmd
```

包装脚本内的实际命令是 `.\.venv\Scripts\python.exe -m pytest tests/ -q`，TEMP/TMP 指向 `E:\muse-bridge\work\TASK-036-startdeck\tmp`。

退出码 0。输出：

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

没有失败项。那条警告是依赖弃用提示，不是失败，按 P2-9 不改版本。

此前同命令的第一次结果是 `21 passed, 1 warning in 10.69s`，退出码同样为 0。live_selftest 没有在这次结尾重跑；它在审查中已通过（`LIVE SELFTEST: ALL PASS`，`LIVE_EXIT=0`），见 run.md。

## git status

收尾前最后一条命令，输出原样如下（无文件行，退出码 0）：

```text
git status --porcelain
```

空输出是预期结果：P0/P1 为空，没有改仓库源码，因此没有需要留在工作区里的 diff。不是改动丢失。`.venv`、`__pycache__`、`.pytest_cache` 被 `.gitignore` 忽略，不会出现在 porcelain 里。
