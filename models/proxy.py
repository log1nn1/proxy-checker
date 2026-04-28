"""
代理数据模型
"""
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class ProxyStats:
    """代理检查统计数据"""
    success_count: int = 0
    fail_count: int = 0
    total_response_time: float = 0.0
    last_check_time: Optional[str] = None
    last_check_status: Optional[bool] = None
    
    @property
    def success_rate(self) -> float:
        """计算成功率 (%)"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100
    
    @property
    def avg_response_time(self) -> float:
        """计算平均响应时间 (ms)"""
        if self.success_count == 0:
            return 0.0
        return (self.total_response_time / self.success_count) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class Proxy:
    """代理模型"""
    ip: str
    port: int
    protocol: str = "http"
    country: Optional[str] = None
    anonymity: Optional[str] = None
    source: Optional[str] = None
    added_at: Optional[str] = None
    stats: ProxyStats = field(default_factory=ProxyStats)
    quality_score: int = 1
    tags: list = field(default_factory=list)
    
    @property
    def url(self) -> str:
        """返回代理URL"""
        return f"{self.protocol}://{self.ip}:{self.port}"
    
    @property
    def display_url(self) -> str:
        """返回显示用的代理URL"""
        return f"{self.ip}:{self.port}"
    
    def __hash__(self):
        return hash((self.ip, self.port, self.protocol))
    
    def __eq__(self, other):
        if not isinstance(other, Proxy):
            return False
        return (self.ip == other.ip and 
                self.port == other.port and 
                self.protocol == other.protocol)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if isinstance(self.stats, ProxyStats):
            data["stats"] = self.stats.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proxy":
        """从字典创建实例"""
        if "stats" in data and isinstance(data["stats"], dict):
            data["stats"] = ProxyStats(**data["stats"])
        elif "stats" not in data:
            data["stats"] = ProxyStats()
        
        return cls(**data)
    
    def __repr__(self) -> str:
        return f"Proxy({self.display_url}, {self.protocol}, quality={self.quality_score}, success_rate={self.stats.success_rate:.1f}%)"
