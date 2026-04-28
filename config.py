"""
配置文件 - 代理检查工具的所有配置参数
"""
import os
from datetime import datetime

# ==================== 项目配置 ====================
PROJECT_NAME = "Proxy Checker"
VERSION = "1.0.0"
DEBUG = False

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# 创建必要目录
for directory in [DATA_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

PROXY_DB_PATH = os.path.join(DATA_DIR, "proxies.json")
STATS_DB_PATH = os.path.join(DATA_DIR, "proxy_stats.json")
LOG_FILE_PATH = os.path.join(LOGS_DIR, "proxy_checks.log")

# ==================== 代理源配置 ====================
PROXY_SOURCES = {
    "github_vakhov": "https://vakhov.github.io/fresh-proxy-list/http.txt",
    "github_fyvri": "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/main/http.txt",
    "proxifly": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/http/data.json",
}

# ==================== 检查配置 ====================
CHECK_URLS = [
    "http://httpbin.org/ip",
    "http://httpbin.org/user-agent",
    "http://httpbin.org/delay/1",
]

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 10
TOTAL_TIMEOUT = 15

MAX_CONCURRENT_CHECKS = 20
MAX_CONCURRENT_FETCHES = 10

# ==================== 质量评级配置 ====================
QUALITY_LEVELS = {
    5: (95, 100, "优"),
    4: (80, 95, "良"),
    3: (60, 80, "中"),
    2: (30, 60, "差"),
    1: (0, 30, "未知"),
}

# ==================== 清理配置 ====================
CLEANUP_CONFIG = {
    "max_age_days": 7,
    "min_quality_score": 2,
    "keep_recent_count": 100,
}

# ==================== 日志配置 ====================
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOG_FILE_PATH,
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"]
    }
}

# ==================== 定时任务配置 ====================
SCHEDULE_JOBS = [
    {
        "id": "fetch_proxies",
        "func": "proxy_fetcher:fetch_proxies",
        "trigger": "cron",
        "hour": 0,
        "minute": 0,
        "description": "每日00:00更新代理��表"
    },
    {
        "id": "check_proxies",
        "func": "proxy_checker:check_all_proxies",
        "trigger": "interval",
        "minutes": 30,
        "description": "每30分钟检查一次代理质量"
    },
    {
        "id": "cleanup_proxies",
        "func": "proxy_storage:cleanup_proxies",
        "trigger": "cron",
        "hour": 3,
        "minute": 0,
        "description": "每日03:00清理过期代理"
    }
]

# ==================== HTTP请求配置 ====================
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==================== 统计配置 ====================
STATS_RETENTION_DAYS = 30
