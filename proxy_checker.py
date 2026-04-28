"""
代理质量检查模块
"""
import asyncio
import logging
import time
from typing import List, Optional, Dict
from datetime import datetime
import aiohttp

from models.proxy import Proxy, ProxyStats
from proxy_storage import load_proxies, save_proxies, get_proxy, update_proxy
import config

logger = logging.getLogger(__name__)


class ProxyChecker:
    """代理质量检查器"""
    
    def __init__(self, check_urls: List[str] = None):
        self.check_urls = check_urls or config.CHECK_URLS
        self.timeout = aiohttp.ClientTimeout(
            total=config.TOTAL_TIMEOUT,
            connect=config.CONNECT_TIMEOUT,
            sock_read=config.READ_TIMEOUT
        )
    
    async def check_proxy(self, proxy: Proxy) -> bool:
        """检查单个代理"""
        success_count = 0
        fail_count = 0
        total_response_time = 0.0
        
        for url in self.check_urls:
            result = await self._test_url(proxy, url)
            if result[0]:
                success_count += 1
                total_response_time += result[1]
            else:
                fail_count += 1
        
        proxy.stats.success_count += success_count
        proxy.stats.fail_count += fail_count
        proxy.stats.total_response_time += total_response_time
        proxy.stats.last_check_time = datetime.now().isoformat()
        proxy.stats.last_check_status = success_count > 0
        
        proxy.quality_score = self._calculate_quality_score(proxy.stats)
        
        return success_count > 0
    
    async def _test_url(self, proxy: Proxy, url: str) -> tuple:
        """测试URL，返回 (成功状态, 响应时间)"""
        try:
            start_time = time.time()
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(
                timeout=self.timeout,
                connector=connector
            ) as session:
                async with session.get(
                    url,
                    proxy=proxy.url,
                    headers=config.DEFAULT_HEADERS,
                    allow_redirects=False
                ) as resp:
                    response_time = time.time() - start_time
                    
                    if resp.status < 400:
                        logger.debug(f"✓ {proxy.display_url} -> {url}: {resp.status}")
                        return (True, response_time)
                    else:
                        logger.debug(f"✗ {proxy.display_url} -> {url}: HTTP {resp.status}")
                        return (False, response_time)
        
        except asyncio.TimeoutError:
            logger.debug(f"✗ {proxy.display_url} -> {url}: 超时")
            return (False, config.TOTAL_TIMEOUT)
        except Exception as e:
            logger.debug(f"✗ {proxy.display_url} -> {url}: {type(e).__name__}")
            return (False, config.TOTAL_TIMEOUT)
    
    def _calculate_quality_score(self, stats: ProxyStats) -> int:
        """根据统计数据计算质量评分"""
        success_rate = stats.success_rate
        
        if stats.success_count + stats.fail_count == 0:
            return 1
        
        avg_response_time = stats.avg_response_time / 1000
        
        if success_rate >= 95 and avg_response_time < 1.0:
            return 5
        elif success_rate >= 80 and avg_response_time < 2.0:
            return 4
        elif success_rate >= 60 and avg_response_time < 5.0:
            return 3
        elif success_rate >= 30:
            return 2
        
        return 1
    
    async def check_all_proxies(self, max_concurrent: int = None) -> Dict[str, int]:
        """检查所有代理"""
        max_concurrent = max_concurrent or config.MAX_CONCURRENT_CHECKS
        
        proxies = load_proxies()
        logger.info(f"开始检查 {len(proxies)} 个代理...")
        
        if not proxies:
            logger.warning("没有可检查的代理")
            return {"total": 0, "checked": 0, "success": 0}
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_with_limit(proxy: Proxy) -> tuple:
            async with semaphore:
                result = await self.check_proxy(proxy)
                return (proxy, result)
        
        tasks = [check_with_limit(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        updated_proxies = []
        success_count = 0
        
        for result in results:
            if isinstance(result, tuple):
                proxy, success = result
                updated_proxies.append(proxy)
                if success:
                    success_count += 1
            elif isinstance(result, Exception):
                logger.error(f"检查失败: {result}")
        
        save_proxies(updated_proxies)
        
        stats = {
            "total": len(proxies),
            "checked": len(updated_proxies),
            "success": success_count,
            "failed": len(updated_proxies) - success_count
        }
        
        logger.info(f"检查完成: {stats}")
        return stats


_checker = None

def get_checker():
    """获取全局检查器实例"""
    global _checker
    if _checker is None:
        _checker = ProxyChecker()
    return _checker


async def check_all_proxies() -> Dict[str, int]:
    """检查所有代理（定时任务接口）"""
    checker = get_checker()
    return await checker.check_all_proxies()

async def check_proxy(proxy: Proxy) -> bool:
    """检查单个代理"""
    checker = get_checker()
    return await checker.check_proxy(proxy)
