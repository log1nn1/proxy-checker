# 🌐 代理检查工具 (Proxy Checker)

一个功能完整、生产级别的代理检查系统，支持从多个源自动获取代理、本地存储、质量检查、定时更新和详细的统计分析。

## ✨ 主要特性

- **🌐 多源代理获取** - 从多个免费代理源自动获取
- **💾 本地数据库** - JSON格式的本地存储管理
- **⚡ 并发检查** - 支持异步并发检查代理质量
- **📊 质量评级** - 五档质量评级系统（优/良/中/差/未知）
- **⏰ 定时任务** - 自动化的计划任务系统
- **📈 详细统计** - 按协议、质量、国家分类的统计分析
- **🧹 自动清理** - 过期和低质代理自动清理
- **📝 完整日志** - 详细的检查记录和错误追踪

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 获取代理
```bash
python main.py fetch
```

### 3. 检查代理质量
```bash
python main.py check
```

### 4. 查看代理列表
```bash
python main.py list
```

### 5. 查看统计信息
```bash
python main.py stats
```

### 6. 启动定时任务
```bash
python main.py schedule --foreground
```

## 📖 详细命令

### 获取代理
```bash
python main.py fetch [--concurrent N]
```

### 检查质量
```bash
python main.py check [--concurrent N]
```

### 列出代理
```bash
python main.py list [--quality N] [--protocol PROTO] [--limit N]
```

### 统计信息
```bash
python main.py stats
```

### 清理代理
```bash
python main.py cleanup [--days N] [--quality N]
```

### 删除代理
```bash
python main.py delete --ip IP --port PORT [--protocol PROTO]
```

### 查看代理详情
```bash
python main.py info --ip IP --port PORT [--protocol PROTO]
```

### 启动调度器
```bash
python main.py schedule [--foreground]
```

### 立即运行任务
```bash
python main.py run [fetch|check|cleanup]
```

## ⚙️ 配置

所有配置在 `config.py` 中，主要项目：

### 代理源
```python
PROXY_SOURCES = {
    "github_vakhov": "https://vakhov.github.io/fresh-proxy-list/http.txt",
    "github_fyvri": "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/main/http.txt",
    "proxifly": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/http/data.json",
}
```

### 定时任务
```python
SCHEDULE_JOBS = [
    # 每日00:00更新代理
    # 每30分钟检查代理质量
    # 每日03:00清理过期代理
]
```

### 质量评级
```python
QUALITY_LEVELS = {
    5: (95, 100, "优"),
    4: (80, 95, "良"),
    3: (60, 80, "中"),
    2: (30, 60, "差"),
    1: (0, 30, "未知"),
}
```

## 📁 项目结构

```
proxy-checker/
├── main.py                 # CLI主入口
├── config.py              # 配置文件
├── requirements.txt       # 依赖清单
├── proxy_fetcher.py       # 代理获取
├── proxy_storage.py       # 本地存储
├── proxy_checker.py       # 质量检查
├── scheduler.py           # 定时任务
├── models/
│   ├── __init__.py
│   └── proxy.py          # 数据模型
├── data/                  # 数据存储
│   ├── proxies.json
│   └── proxy_stats.json
└── logs/                  # 日志
    └── proxy_checks.log
```

## 💡 使用示例

### 获取代理并检查
```bash
# 获取代理
python main.py fetch

# 检查质量
python main.py check

# 显示优质代理
python main.py list --quality 4 --limit 20
```

### 启动自动定时任务
```bash
# 前台运行（便于调试）
python main.py schedule --foreground

# 后台运行
python main.py schedule &
```

### 管理代理
```bash
# 查看代理详情
python main.py info --ip 1.1.1.1 --port 8080

# 删除代理
python main.py delete --ip 1.1.1.1 --port 8080

# 清理过期代理
python main.py cleanup
```

## 📊 日志

日志文件：`logs/proxy_checks.log`

同时输出到控制台和文件，包含：
- 代理获取信息
- 质量检查结果
- 错误和异常
- 定时任务执行

## 🔧 开发

### 添加新的代理源

在 `config.py` 中添加到 `PROXY_SOURCES`

### 自定义检查URL

修改 `config.py` 中的 `CHECK_URLS`

### 添加新的定时任务

在 `config.py` 中的 `SCHEDULE_JOBS` 添加任务配置

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！
