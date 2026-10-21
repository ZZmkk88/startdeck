# startdeck · 个人起始页

一句话定位：一个轻量、可自己部署的个人导航面板——把常用网站和服务按分组摆成一屏，点开即达，还能一眼看出每个站通不通。

本项目的设计学习了开源社区个人导航页工具的通行思路——如分组导航、站点图标、状态探测这类核心概念；代码为独立实现。上游溯源与署名见 [UPSTREAM.md](UPSTREAM.md)。

## 功能清单（与代码实现一一对应，均已测试覆盖）

- **登录**：单用户账号，Token 登录（24 小时有效），首次登录提示改密
- **分组管理**：分组可增、删、改名（如「工作」「影音」「服务器」）；删除分组时其下链接会一并删除，界面删除前有确认提示
- **链接管理**：每个链接有名称、网址、说明；可增、删、改，可在编辑时换到别的分组；网址只接受 http/https
- **图标**：加链接时自动按目标站地址生成 favicon 图标地址，页面加载不到图标时自动回退为名称首字占位
- **首页**：按分组展示链接卡片墙（图标、名称、说明、网址主机名）；顶部搜索框输入即过滤（名称 / 说明 / 网址）
- **状态探测**：打开页面自动探测一轮，也可单条点「探测」或点「探测全部」；卡片显示绿点（通，带响应毫秒）/ 红点（不通，带原因）；2xx/3xx 算通

## 安装与启动

需要 Python 3.10 或更高版本。

**Linux / macOS（bash）:**

```bash
cd startdeck
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py            # 默认只监听本机 127.0.0.1:8000
```

**Windows（PowerShell）:**

```powershell
cd startdeck
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py        # 默认只监听本机 127.0.0.1:8000
```

启动后打开 http://localhost:8000 ，默认账号 **admin / admin123**，首次登录会提示改密码。

可选环境变量：

| 变量 | 说明 | 默认 |
|---|---|---|
| `PORT` | 监听端口（Windows PowerShell 里用 `$env:PORT=8123` 设置） | 8000 |
| `HOST` | 监听地址。只有需要从局域网访问时才设为 `0.0.0.0` | `127.0.0.1` |
| `STARTDECK_DB_PATH` | SQLite 数据库文件位置 | `data/startdeck.db` |
| `SD_INITIAL_USERNAME` / `SD_INITIAL_PASSWORD` | 首次启动创建的初始账号 | admin / admin123 |

## 测试

先装测试依赖（两个系统的命令只是路径写法不同）：

```bash
# Linux / macOS
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -q
```

```powershell
# Windows (PowerShell)
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest tests/ -q
```

共 20 项自动化测试（登录/改密、分组增删改与级联删除、链接增删改与跨分组移动、网址校验、搜索三字段过滤、状态探测通/断/全部及重定向口径、favicon 地址推导）。

真实流程自测（脚本会自己在 8131 端口起一个临时服务、跑完整流程再关掉）：

```bash
.venv/bin/python tests/live_selftest.py
```

## 后续可扩展项

- 分组与链接的拖拽排序
- 自定义图标（上传或填图片地址）
- 定时探测与历史可用率统计
- 从浏览器书签文件批量导入链接

## 许可证

MIT（见 [LICENSE](LICENSE)）。本项目为独立实现；设计时学习的上游同为 MIT 许可证，其版权归因见 [UPSTREAM.md](UPSTREAM.md)。
