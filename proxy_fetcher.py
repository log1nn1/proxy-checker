"""
代理获取模块 - 从多个源获取代理列表
"""
import logging
import asyncio
import aiohttp
import json
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse
from datetime import datetime
from models.proxy import Proxy
import config

logger = logging.getLogger(__name__)


class ProxyFetcher:
    """代理获取器"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(
            total=config.TOTAL_TIMEOUT,
            connect=config.CONNECT_TIMEOUT,
            sock_read=config.READ_TIMEOUT
        )
    
    async def fetch_from_url(self, url: str) -> List[str]:
        """从URL获取代理列表"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=config.DEFAULT_HEADERS) as resp:
                    if resp.status != 200:
                        logger.warning(f"获取代理失败 {url}: HTTP {resp.status}")
                        return []
                    
                    content = await resp.text()
                    proxies = self._parse_proxy_content(content, url)
                    logger.info(f"从 {url} 获取了 {len(proxies)} 个代理")
                    return proxies
        
        except asyncio.TimeoutError:
            logger.error(f"获取代理超时: {url}")
            return []
        except Exception as e:
            logger.error(f"获取代理异常 {url}: {e}")
            return []
    
    def _parse_proxy_content(self, content: str, source_url: str) -> List[str]:
        """解析代理内容"""
        proxies = []
        source_name = self._get_source_name(source_url)
        
        try:
            if content.strip().startswith("[") or content.strip().startswith("{"):
                return self._parse_json(content, source_name)
        except Exception as e:
            logger.debug(f"JSON解析失败，尝试文本格式: {e}")
        
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "://" in line:
                try:
                    parsed = urlparse(line)
                    if parsed.hostname and parsed.port:
                        proxies.append(f"{parsed.hostname}:{parsed.port}")
                except Exception:
                    pass
            elif ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        ip, port = parts[0].strip(), parts[1].strip()
                        if self._is_valid_ip(ip) and port.isdigit():
                            proxies.append(f"{ip}:{port}")
                    except Exception:
                        pass
        
        return proxies
    
    def _parse_json(self, content: str, source_name: str) -> List[str]:
        """解析JSON格式的代理"""
        proxies = []
        data = json.loads(content)
        
        if isinstance(data, list):
            for item in data:
                proxy = self._extract_proxy_from_json_item(item)
                if proxy:
                    proxies.append(proxy)
        elif isinstance(data, dict):
            for item in data.get("data", []):
                proxy = self._extract_proxy_from_json_item(item)
                if proxy:
                    proxies.append(proxy)
        
        return proxies
    
    def _extract_proxy_from_json_item(self, item: Dict) -> Optional[str]:
        """从JSON项提取代理"""
        if isinstance(item, dict):
            ip = item.get("ip") or item.get("IP")
            port = item.get("port") or item.get("PORT")
            if ip and port:
                return f"{ip}:{port}"
        elif isinstance(item, str):
            if ":" in item:
                return item
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """简单的IP验证"""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except ValueError:
            return False
    
    def _get_source_name(self, url: str) -> str:
        """从URL获取源名称"""
        for name, source_url in config.PROXY_SOURCES.items():
            if url == source_url:
                return name
        return "unknown"
    
    async def fetch_all(self) -> List[Proxy]:
        """从所有源获取代理"""
        logger.info(f"开始从 {len(config.PROXY_SOURCES)} 个源获取代理...")
        
        tasks = []
        for name, url in config.PROXY_SOURCES.items():
            tasks.append(self._fetch_and_convert(name, url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_proxies = []
        for result in results:
            if isinstance(result, list):
                all_proxies.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"获取代理失败: {result}")
        
        seen = set()
        unique_proxies = []
        for proxy in all_proxies:
            key = (proxy.ip, proxy.port, proxy.protocol)
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        logger.info(f"获取到 {len(unique_proxies)} 个唯一代理")
        return unique_proxies
    
    async def _fetch_and_convert(self, name: str, url: str) -> List[Proxy]:
        """获取并转换为Proxy对象"""
        proxy_strings = await self.fetch_from_url(url)
        proxies = []
        
        for proxy_str in proxy_strings:
            try:
                ip, port = proxy_str.split(":")
                proxy = Proxy(
                    ip=ip,
                    port=int(port),
                    protocol="http",
                    source=name,
                    added_at=datetime.now().isoformat()
                )
                proxies.append(proxy)
            except Exception as e:
                logger.debug(f"转换代理失败 {proxy_str}: {e}")
        
        return proxies


fetcher = None

def get_fetcher():
    """获取单例fetcher"""
    global fetcher
    if fetcher is None:
        fetcher = ProxyFetcher()
    return fetcher


async def fetch_proxies():
    """异步获取代理（定时任务接口）"""
    from proxy_storage import add_proxies
    
    fetcher = get_fetcher()
    proxies = await fetcher.fetch_all()
    
    if proxies:
        added = add_proxies(proxies)
        logger.info(f"添加了 {added} 个新代理到数据库")
    
    return proxies
