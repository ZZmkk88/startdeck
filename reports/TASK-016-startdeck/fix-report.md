# startdeck 修复记录

只改 review.md 清单里的 P1。P0 无。P1-4 不改代码，原因写在文末。

## P1-1 默认监听所有网卡

- 问题编号：P1-1
- 文件：`app.py:554-556`（原 `app.py:554` 的 `host="0.0.0.0"`）；`README.md:26`、`README.md:35`、`README.md:45`
- 改法：`HOST` 默认 `127.0.0.1`，只有设置 `HOST` 才监听其他地址。README 两处启动注释和环境变量表改成同一默认值。

验证 1，重新起服务（退出码 0，主动 terminate 后进程退出码为 1，8000 已释放）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe E:\muse-bridge\work\TASK-016-startdeck\run_smoke.py
```

```
CAME_UP True AFTER 1.42s
GET / STATUS 200 TYPE text/html; charset=utf-8 LEN 20691
PORT8000_IN_USE_AFTER False
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:49932 - "GET / HTTP/1.1" 200 OK
```

验证 2，全量 pytest（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
20 passed, 1 warning in 7.66s
```

验证 3，live_selftest（退出码 0，6.51s）：

```
LIVE SELFTEST: ALL PASS
EXIT 0 ELAPSED 6.51s
```

## P1-2 favicon 地址带走口令

- 问题编号：P1-2
- 文件：`app.py:55-65`（原 `app.py:61-62`）
- 改法：从 `netloc` 去掉最后一个 `@` 之前的用户信息，主机和端口保留。

验证 1，直接调用（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe E:\muse-bridge\work\TASK-016-startdeck\verify_favicon.py
```

```
https://alice:s3cret@example.com/admin/page -> https://example.com/favicon.ico
https://sub.example.com:8443/a/b?c=d -> https://sub.example.com:8443/favicon.ico
http://192.168.1.1/admin -> http://192.168.1.1/favicon.ico
https://user:p@ss@example.com:8443/x -> https://example.com:8443/favicon.ico
http://[::1]:8080/a -> http://[::1]:8080/favicon.ico
```

验证 2，全量 pytest（退出码 0）：

```
20 passed, 1 warning in 7.51s
```

`tests/test_app.py:318-322` 的 favicon 断言与 `test_create_link_and_icon`、`test_update_link_fields` 仍通过（包含在这 20 项里）。

## P1-3 匿名文档页加载外部脚本

- 问题编号：P1-3
- 文件：`app.py:188-196`（原 `app.py:185`）
- 改法：`docs_url`、`redoc_url`、`openapi_url` 设为 `None`。

验证 1，TestClient（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe E:\muse-bridge\work\TASK-016-startdeck\verify_docs.py
```

```
GET / 200 text/html; charset=utf-8 '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n<meta name="vi'
GET /docs 404 application/json '{"detail":"Not Found"}'
GET /redoc 404 application/json '{"detail":"Not Found"}'
GET /openapi.json 404 application/json '{"detail":"Not Found"}'
GET /health 404 application/json '{"detail":"Not Found"}'
```

验证 2，全量 pytest（退出码 0）：

```
20 passed, 1 warning in 7.81s
```

## P1-4 改密不撤销其他会话

- 问题编号：P1-4
- 文件：`app.py:261-274` 一带的 `change_password`（行号相对改前的 `app.py:261-274`；本次未改这个函数）
- 改法：未改。
- 原因：改密时应删除同用户的其他 session。`tests/test_app.py:66-68` 把第一次登录的 token 做成 module 级 fixture，`tests/test_app.py:117-122` 再用另一个 token 把密码改回去。若撤销其他会话，后面的用例会拿着旧 token 得到 401。禁止改测试，也不能先改再撤回，所以不落地。
- 改前证据（`repro_checks.py`，退出码 0）：用 token A 改密后，token B 访问 `/api/me` 仍是 `200 {"username":"admin","must_change_password":false}`。

下面是全部改动落地后的最终全量测试。`change_password` 现在从 `app.py:273` 开始，函数体没有改。

## 最终全量测试

命令（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
....................                                                     [100%]
============================== warnings summary ===============================
..\..\work\TASK-016-startdeck\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-016-startdeck\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
20 passed, 1 warning in 9.11s
```

没有失败项。警告仍来自依赖里的 `fastapi\testclient.py:1`，不是本次改动引入的断言失败。

同一状态下又跑了一次真实流程自测（退出码 0）：

```
E:\muse-bridge\work\TASK-016-startdeck\venv\Scripts\python.exe tests/live_selftest.py
```

```
LIVE SELFTEST: ALL PASS
EXIT 0 ELAPSED 8.38s
```

## git status --porcelain

命令：

```
git -C E:\muse-bridge\in\TASK-016-startdeck status --porcelain
```

输出：

```
 M README.md
 M app.py
```
