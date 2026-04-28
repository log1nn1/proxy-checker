# Proxy Checker

一个轻量级的代理检查工具，支持本地 SOCKS5 代理服务。

## 功能特性

- 🌐 本地 SOCKS5 代理服务（监听 127.0.0.1:1080）
- ✅ 代理连通性检查
- 🔄 支持多种代理类型

## 快速开始

### 1. 启动本地代理服务

```bash
python local_proxy_server.py
```

输出示例：
```
✓ SOCKS5 代理已启动: 127.0.0.1:1080
✓ 浏览器代理设置: 127.0.0.1:1080 (SOCKS5)
✓ 等待连接...
```

### 2. 配置浏览器

#### Chrome/Chromium
1. 打开浏览器设置 → 系统 → 打开代理设置
2. 配置 SOCKS 代理：
   - 地址：`127.0.0.1`
   - 端口：`1080`

#### Firefox
1. 设置 → 网络设置 → 网络代理 → 手动代理配置
2. SOCKS 主机：`127.0.0.1`
3. 端口：`1080`
4. 勾选 "SOCKS v5"

#### macOS/Linux
```bash
# 临时代理设置（仅当前终端）
export all_proxy=socks5://127.0.0.1:1080
```

### 3. 测试代理连接

浏览器访问任何网站，终端会显示连接日志：
```
[连接] 来自 127.0.0.1:xxxxx
  → 目标: example.com:443
  ✓ 连接已关闭
```

## 使用自定义端口

```bash
python local_proxy_server.py 8080  # 使用 8080 端口
```

## 项目结构

```
proxy-checker/
├── local_proxy_server.py    # 本地 SOCKS5 代理服务
├── requirements.txt         # 项目依赖
└── README.md               # 本文档
```

## 支持的功能

- ✅ SOCKS5 协议
- ✅ IPv4/IPv6 支持
- ✅ 域名解析
- ✅ 实时连接日志
- ✅ 双向数据转发

## 注意事项

- 默认仅监听本地接口 (`127.0.0.1`)，安全可靠
- 不支持 SOCKS4、HTTP 代理（可扩展）
- 需要 Python 3.6+
- 无需外部依赖，仅使用 Python 标准库

## 许可证

MIT
