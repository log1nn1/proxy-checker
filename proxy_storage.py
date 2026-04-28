"""
代理存储模块 - 本地数据库管理
"""
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from models.proxy import Proxy, ProxyStats
import config

logger = logging.getLogger(__name__)


class ProxyStorage:
    """代理存储管理器"""
    
    def __init__(self, db_path: str = config.PROXY_DB_PATH):
        self.db_path = db_path
        self.stats_path = config.STATS_DB_PATH
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        for path in [self.db_path, self.stats_path]:
            try:
                with open(path, 'r') as f:
                    json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                with open(path, 'w') as f:
                    json.dump([], f)
                logger.info(f"创建了新的数据库文件: {path}")
    
    def load_proxies(self) -> List[Proxy]:
        """加载所有代理"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                proxies = [Proxy.from_dict(item) for item in data]
                logger.debug(f"加载了 {len(proxies)} 个代理")
                return proxies
        except Exception as e:
            logger.error(f"加载代理失败: {e}")
            return []
    
    def save_proxies(self, proxies: List[Proxy]):
        """保存所有代理"""
        try:
            data = [proxy.to_dict() for proxy in proxies]
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存了 {len(proxies)} 个代理")
        except Exception as e:
            logger.error(f"保存代理失败: {e}")
    
    def add_proxy(self, proxy: Proxy) -> bool:
        """添加单个代理"""
        proxies = self.load_proxies()
        
        for existing in proxies:
            if existing == proxy:
                return False
        
        proxies.append(proxy)
        self.save_proxies(proxies)
        return True
    
    def add_proxies(self, new_proxies: List[Proxy]) -> int:
        """添加多个代理，返回新增数量"""
        proxies = self.load_proxies()
        existing_set = {(p.ip, p.port, p.protocol) for p in proxies}
        
        added_count = 0
        for proxy in new_proxies:
            key = (proxy.ip, proxy.port, proxy.protocol)
            if key not in existing_set:
                proxies.append(proxy)
                existing_set.add(key)
                added_count += 1
        
        if added_count > 0:
            self.save_proxies(proxies)
            logger.info(f"新增了 {added_count} 个代理")
        
        return added_count
    
    def get_proxy(self, ip: str, port: int, protocol: str = "http") -> Optional[Proxy]:
        """获取特定代理"""
        proxies = self.load_proxies()
        for proxy in proxies:
            if proxy.ip == ip and proxy.port == port and proxy.protocol == protocol:
                return proxy
        return None
    
    def update_proxy(self, proxy: Proxy) -> bool:
        """更新代理信息"""
        proxies = self.load_proxies()
        
        for i, existing in enumerate(proxies):
            if existing == proxy:
                proxies[i] = proxy
                self.save_proxies(proxies)
                return True
        
        return False
    
    def delete_proxy(self, ip: str, port: int, protocol: str = "http") -> bool:
        """删除代理"""
        proxies = self.load_proxies()
        original_count = len(proxies)
        
        proxies = [p for p in proxies 
                   if not (p.ip == ip and p.port == port and p.protocol == protocol)]
        
        if len(proxies) < original_count:
            self.save_proxies(proxies)
            logger.info(f"删除了代理: {ip}:{port}")
            return True
        
        return False
    
    def get_proxies_by_quality(self, min_score: int = 3) -> List[Proxy]:
        """获取指定质量等级以上的代理"""
        proxies = self.load_proxies()
        return [p for p in proxies if p.quality_score >= min_score]
    
    def get_proxies_by_country(self, country: str) -> List[Proxy]:
        """按国家获取代理"""
        proxies = self.load_proxies()
        return [p for p in proxies if p.country and p.country.lower() == country.lower()]
    
    def get_proxies_by_protocol(self, protocol: str) -> List[Proxy]:
        """按协议获取代理"""
        proxies = self.load_proxies()
        return [p for p in proxies if p.protocol == protocol]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        proxies = self.load_proxies()
        
        if not proxies:
            return {
                "total": 0,
                "by_protocol": {},
                "by_quality": {},
                "by_country": {},
                "success_rate": 0,
                "avg_response_time": 0
            }
        
        by_protocol = {}
        for proxy in proxies:
            protocol = proxy.protocol
            if protocol not in by_protocol:
                by_protocol[protocol] = 0
            by_protocol[protocol] += 1
        
        by_quality = {score: 0 for score in range(1, 6)}
        for proxy in proxies:
            by_quality[proxy.quality_score] += 1
        
        by_country = {}
        for proxy in proxies:
            if proxy.country:
                if proxy.country not in by_country:
                    by_country[proxy.country] = 0
                by_country[proxy.country] += 1
        
        total_success = sum(p.stats.success_count for p in proxies)
        total_fail = sum(p.stats.fail_count for p in proxies)
        total_checks = total_success + total_fail
        
        success_rate = (total_success / total_checks * 100) if total_checks > 0 else 0
        
        total_response_time = sum(p.stats.total_response_time for p in proxies)
        avg_response_time = (total_response_time / total_success) if total_success > 0 else 0
        
        return {
            "total": len(proxies),
            "by_protocol": by_protocol,
            "by_quality": by_quality,
            "by_country": by_country,
            "total_checks": total_checks,
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(avg_response_time * 1000, 2),
        }


_storage = None

def get_storage():
    """获取全局存储实例"""
    global _storage
    if _storage is None:
        _storage = ProxyStorage()
    return _storage


def load_proxies() -> List[Proxy]:
    return get_storage().load_proxies()

def save_proxies(proxies: List[Proxy]):
    get_storage().save_proxies(proxies)

def add_proxy(proxy: Proxy) -> bool:
    return get_storage().add_proxy(proxy)

def add_proxies(proxies: List[Proxy]) -> int:
    return get_storage().add_proxies(proxies)

def delete_proxy(ip: str, port: int, protocol: str = "http") -> bool:
    return get_storage().delete_proxy(ip, port, protocol)

def get_proxy(ip: str, port: int, protocol: str = "http") -> Optional[Proxy]:
    return get_storage().get_proxy(ip, port, protocol)

def get_stats() -> Dict:
    return get_storage().get_stats()


def cleanup_proxies():
    """清理过期和低质代理"""
    logger.info("开始清理代理...")
    
    storage = get_storage()
    proxies = storage.load_proxies()
    
    if not proxies:
        logger.info("没有代理需要清理")
        return
    
    max_age_days = config.CLEANUP_CONFIG["max_age_days"]
    min_quality_score = config.CLEANUP_CONFIG["min_quality_score"]
    keep_recent_count = config.CLEANUP_CONFIG["keep_recent_count"]
    
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    kept_proxies = []
    removed_count = 0
    
    for proxy in proxies:
        if proxy.added_at:
            try:
                added_time = datetime.fromisoformat(proxy.added_at)
                if added_time < cutoff_date:
                    removed_count += 1
                    logger.debug(f"删除过期代理: {proxy.display_url}")
                    continue
            except Exception:
                pass
        
        if proxy.quality_score < min_quality_score:
            if len(kept_proxies) < keep_recent_count:
                kept_proxies.append(proxy)
            else:
                removed_count += 1
                logger.debug(f"删除低质代理: {proxy.display_url} (质量评分: {proxy.quality_score})")
            continue
        
        kept_proxies.append(proxy)
    
    storage.save_proxies(kept_proxies)
    logger.info(f"清理完成，删除了 {removed_count} 个代理，保留 {len(kept_proxies)} 个")
