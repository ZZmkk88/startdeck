# startdeck P2 修复记录

修前基线：`21 passed, 1 warning in 8.68s`。每条之后都重跑全量 pytest。未改 `tests/`、`LICENSE`、`UPSTREAM.md`、`requirements*.txt`。

## P2-1 图标失败回退首字

- 文件：`static/index.html:369-376`
- 改法：加载前不再给首字加 `hidden`。`error` 时删掉图片并 `classList.remove("hidden")`；`load` 成功才 `classList.add("hidden")`。两个监听都在设置 `img.src` 之前注册。
- 验证命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B -m pytest E:\muse-bridge\in\TASK-039-startdeck-p2\tests -q --rootdir E:\muse-bridge\in\TASK-039-startdeck-p2 -p no:cacheprovider
```

```
21 passed, 1 warning in 8.47s
```

页面行为没有自动化测试，也没有浏览器。依据是改后的 `static/index.html:369-376`：失败路径不再把首字留在 `hidden` 里。

## P2-2 README 测试数量

- 文件：`README.md:67`（P2-3 在上方插了一段说明，行号从 65 移到 67）
- 改法：`共 20 项` 改为 `共 21 项`，并写上 `test_change_password_revokes_other_sessions`。与 `tests/test_app.py` 里 21 个 `def test_` 以及修前 `21 passed` 对齐。
- 验证命令：同上全量 pytest。

```
21 passed, 1 warning in 8.46s
```

## P2-3 README 覆盖说法

- 文件：`README.md:7-9`
- 改法：标题去掉「均已测试覆盖」。补一句：后端接口已有自动化测试；删除前确认框、打开页面自动探测、绿点/红点文案、图标加载失败回退首字是页面行为，当前没有自动化测试。未改 `tests/`。
- 验证命令：同上全量 pytest。

```
21 passed, 1 warning in 8.46s
```

## P2-4 README 补 Windows 自测命令

- 文件：`README.md:71-79`
- 改法：保留 `.venv/bin/python tests/live_selftest.py`，并补 PowerShell：`.venv\Scripts\python tests\live_selftest.py`。未改 `tests/live_selftest.py`。
- 验证命令：同上全量 pytest。

```
21 passed, 1 warning in 7.99s
```

## P2-5 validate_url 拒绝 CR/LF

- 文件：`app.py:444-450`
- 改法：`strip` 之后，若仍含码点 `<= 0x20` 或 `== 0x7F`，返回 400「网址含有控制字符」。只在首尾的空白会被原有 `strip` 去掉，不会原样存进库。
- 验证命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-039-startdeck-p2\check_p2_5.py
```

```
REJECT 400 网址含有控制字符 'https://example.com/a\r\nX-Injected: 1'
ACCEPT 'https://example.com/a\n' -> 'https://example.com/a'
REJECT 400 网址含有控制字符 'https://example.com/a b'
REJECT 400 网址含有控制字符 'https://example.com/\x7f'
ACCEPT 'https://example.com/ok' -> 'https://example.com/ok'
ACCEPT 'http://127.0.0.1:9/x' -> 'http://127.0.0.1:9/x'
```

全量 pytest：

```
21 passed, 1 warning in 8.55s
```

## P2-6 哈希比较改 hmac.compare_digest

- 文件：`app.py:9` 增加 `import hmac`；`app.py:56-63` 固定盐/摘要与 `password_matches`；登录 `app.py:270-274`；改密 `app.py:303`。
- 改法：先算一次 pbkdf2。用户不存在时用 16 字节固定盐和 64 位十六进制占位摘要，避免短路不算哈希。比较用 `hmac.compare_digest`，不再用 `!=`。
- 验证：全量 pytest 覆盖错密码、正确登录、改密与作废其他会话。

```
21 passed, 1 warning in 8.50s
```

## P2-7 常见安全响应头

- 文件：`app.py:210-216`
- 改法：HTTP 中间件对每个响应加 `X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy: no-referrer`。未加 CSP，页面有内联脚本。
- 验证命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-039-startdeck-p2\check_p2_7.py
```

```
PATH / STATUS 200
  x-content-type-options nosniff
  x-frame-options DENY
  referrer-policy no-referrer
PATH /api/me STATUS 401
  x-content-type-options nosniff
  x-frame-options DENY
  referrer-policy no-referrer
```

全量 pytest：

```
21 passed, 1 warning in 8.46s
```

## P2-8 外链补 noreferrer

- 文件：`static/index.html:360`
- 改法：`rel="noopener"` 改为 `rel="noopener noreferrer"`。
- 验证命令：同上全量 pytest。没有浏览器，未点击外链。

```
21 passed, 1 warning in 8.51s
```

## P2-9 改密后立刻收起横幅

- 文件：`static/index.html:265`
- 改法：改密接口成功后给 `#pwBanner` 加上 `hidden`。失败路径不收起。成功文案 `#pwMsg` 写在横幅里面，横幅收起后当次看不到这句话；清单要求的就是收起整条横幅。
- 验证命令：同上全量 pytest。没有浏览器，未做点击。依据是 `static/index.html:263-265`。

```
21 passed, 1 warning in 8.50s
```

## P2-10 LIKE 查询转义 % 和 _

- 文件：`app.py:474-477` `like_contains`；`app.py:492-497` 查询改用 `ESCAPE '\'`。
- 改法：先把 `\`、`%`、`_` 转义，再包进 `%...%`。`%` 和 `_` 按字面匹配。名称、说明、网址三个字段同一模式。
- 验证命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-039-startdeck-p2\check_p2_10.py
```

```
PATTERN '%100\\%\\_a\\\\b%'
CREATE 200 alpha
CREATE 200 100% done
CREATE 200 under_score
CREATE 200 a_pha
SEARCH '%' ['100% done']
SEARCH '_' ['100% done', 'under_score', 'a_pha']
SEARCH 'a_pha' ['a_pha']
SEARCH '100%' ['100% done']
SEARCH 'alpha' ['alpha']
SEARCH 'mail' []
SEARCH '\\' []
```

修前同样的 `%` 和 `_` 会命中 `alpha`。修后 `%` 只命中名称里真有百分号的 `100% done`；`a_pha` 不再命中 `alpha`。`_` 仍命中说明为 `a_b` 的 `100% done`，这是字面下划线，不是通配。

该条改完后的全量 pytest：

```
21 passed, 1 warning in 8.57s
```

## 收尾全量测试

十条都改完后重跑。命令：

```
E:\muse-bridge\work\TASK-039-startdeck-p2\.venv\Scripts\python.exe -B -m pytest E:\muse-bridge\in\TASK-039-startdeck-p2\tests -q --rootdir E:\muse-bridge\in\TASK-039-startdeck-p2 -p no:cacheprovider
```

```
21 passed, 1 warning in 8.96s
```

警告仍是 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 未改测试，未加 skip/xfail，未改断言。`git diff --stat`：`README.md | 12`、`app.py | 43`、`static/index.html | 12`，共 3 files changed, 57 insertions(+), 10 deletions(-)。

## git status --porcelain

命令：`git status --porcelain`

```
 M README.md
 M app.py
 M static/index.html
```
