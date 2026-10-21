# startdeck 修复报告

结论：`review.md` 分级清单里 **P0 无、P1 无**。本任务只修这两级，最多 5 项。因此没有改仓库源码。P2 共 10 条，全部未动。

没有「修不动」的 P0/P1。下面按清单编号说明。

## P0

无条目。pytest、live_selftest、`127.0.0.1:8000` 首页 200 在审查阶段已经跑通，见 `run.md` 第 2–4 节。不需要为「跑不起来」改代码。

## P1

无条目。鉴权、跨用户隔离、重定向不跟随、文档页关闭、favicon 去掉用户信息，审查时都有命令输出或 `文件:行号`。不新增修复。

## P2（按任务不修）

1. 问题编号 P2-1。文件 `static/index.html:368-371`。未改。原因：图标失败不回退首字，是展示缺陷，不属于跑不起来、安全、数据或权限。
2. 问题编号 P2-2。文件 `README.md:65`。未改。原因：测试数量 20 与实际 21 不符，是文档错误。
3. 问题编号 P2-3。文件 `README.md:7`。未改。原因：「均已测试覆盖」说满了；要圆上只能改 README 或加测试，加测试被禁止，改文档不属于 P0/P1。
4. 问题编号 P2-4。文件 `README.md:69-70`。未改。原因：自测命令缺 Windows 写法，文档遗漏。
5. 问题编号 P2-5。文件 `app.py:421-428`。未改。原因：`validate_url` 接受 CR/LF，但本机探测已被解释器拒绝。`audit_isolation.py` 输出：`URL can't contain control characters. '/\\r\\nX-Injected: yes' (found at least '\\r')`。当前打不出请求头注入，不升 P1。
6. 问题编号 P2-6。文件 `app.py:250`、`app.py:280`。未改。原因：哈希比较不是恒定时间。pbkdf2 20 万次占主要耗时，且是本机单用户，不升 P1。
7. 问题编号 P2-7。文件 `app.py:190`。未改。原因：缺安全响应头。令牌不在 Cookie 里。首页实测 `sec_headers (none)`。
8. 问题编号 P2-8。文件 `static/index.html:359`。未改。原因：外链只有 `noopener`，没有 `noreferrer`。
9. 问题编号 P2-9。文件 `static/index.html:262-264`。未改。原因：改密成功后横幅不立刻收起。刷新后 `static/index.html:489` 会按标志收起。
10. 问题编号 P2-10。文件 `app.py:459-462`。未改。原因：`LIKE` 未转义 `%` `_`。查询带 `user_id`，只能看到自己的链接。

`LICENSE`、`UPSTREAM.md`、测试文件、`requirements*.txt` 的版本号都没有改。

## 全量测试（审查结束后重跑）

未改代码，仍按要求重跑 pytest。live_selftest 在改代码之前已全部通过（`run.md` 第 3 节），这次没有再去请求 `https://example.com/`。

命令：

```
E:\muse-bridge\work\TASK-029-startdeck\.venv\Scripts\python.exe -B -m pytest E:\muse-bridge\in\TASK-029-startdeck\tests -q --rootdir E:\muse-bridge\in\TASK-029-startdeck -p no:cacheprovider
```

输出：

```
.....................                                                    [100%]
============================== warnings summary ===============================
..\..\work\TASK-029-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-029-startdeck\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 1 warning in 8.47s
```

exit 0。没有失败用例。警告是 Starlette 建议换 httpx2，不改依赖版本。

## git status --porcelain

命令：

```
git -C E:\muse-bridge\in\TASK-029-startdeck status --porcelain
```

输出：（空，exit 0）

空输出是预期：P0/P1 没有条目，仓库源码一字未改，工作区仍与 HEAD `a1ecd37` 一致。没有执行 `git checkout`、`git restore`、`git stash`、`git clean`。报告写在 `E:\muse-bridge\out\TASK-029-startdeck\`，不在这个仓库里。
