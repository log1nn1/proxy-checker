"""
定时任务调度器
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
import asyncio
from functools import wraps

import config

logger = logging.getLogger(__name__)


class ProxyScheduler:
    """代理任务调度器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
    
    def _make_async_wrapper(self, async_func):
        """为异步函数创建包装器"""
        @wraps(async_func)
        def wrapper():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(async_func())
                else:
                    loop.run_until_complete(async_func())
            except Exception as e:
                logger.error(f"任务执行失败: {e}", exc_info=True)
        return wrapper
    
    def _import_function(self, func_path: str):
        """动态导入函数"""
        try:
            module_name, func_name = func_path.split(":")
            module = __import__(module_name)
            return getattr(module, func_name)
        except Exception as e:
            logger.error(f"导入函数失败 {func_path}: {e}")
            return None
    
    def _schedule_job(self, job_config: dict) -> bool:
        """根据配置添加定时任务"""
        job_id = job_config.get("id")
        func_path = job_config.get("func")
        trigger_type = job_config.get("trigger")
        description = job_config.get("description", "")
        
        logger.info(f"注册任务: {job_id} - {description}")
        
        func = self._import_function(func_path)
        if func is None:
            logger.error(f"无法导入函数: {func_path}")
            return False
        
        try:
            if asyncio.iscoroutinefunction(func):
                func = self._make_async_wrapper(func)
            
            if trigger_type == "cron":
                trigger = CronTrigger(
                    hour=job_config.get("hour"),
                    minute=job_config.get("minute", 0)
                )
            elif trigger_type == "interval":
                trigger = IntervalTrigger(
                    minutes=job_config.get("minutes", 30)
                )
            else:
                logger.error(f"未知的触发器类型: {trigger_type}")
                return False
            
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name=description,
                replace_existing=True
            )
            
            self.jobs[job_id] = job
            logger.info(f"任务已添加: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"添加任务失败 {job_id}: {e}")
            return False
    
    def schedule_all(self):
        """添加所有配置的任务"""
        logger.info(f"开始注册 {len(config.SCHEDULE_JOBS)} 个定时任务...")
        
        success_count = 0
        for job_config in config.SCHEDULE_JOBS:
            if self._schedule_job(job_config):
                success_count += 1
        
        logger.info(f"成功注册 {success_count}/{len(config.SCHEDULE_JOBS)} 个任务")
    
    def start(self):
        """启动调度器"""
        if self.scheduler.running:
            logger.warning("调度器已在运行中")
            return
        
        self.schedule_all()
        self.scheduler.start()
        logger.info("调度器已启动")
        
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id})")
    
    def stop(self):
        """停止调度器"""
        if not self.scheduler.running:
            logger.warning("调度器未在运行中")
            return
        
        self.scheduler.shutdown(wait=True)
        logger.info("调度器已停止")
    
    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        if job_id not in self.jobs:
            logger.error(f"任务不存在: {job_id}")
            return False
        
        self.scheduler.pause_job(job_id)
        logger.info(f"任务已暂停: {job_id}")
        return True
    
    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        if job_id not in self.jobs:
            logger.error(f"任务不存在: {job_id}")
            return False
        
        self.scheduler.resume_job(job_id)
        logger.info(f"任务已恢复: {job_id}")
        return True
    
    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        if job_id not in self.jobs:
            logger.error(f"任务不存在: {job_id}")
            return False
        
        self.scheduler.remove_job(job_id)
        del self.jobs[job_id]
        logger.info(f"任务已移除: {job_id}")
        return True
    
    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()
    
    def get_job_info(self, job_id: str) -> dict:
        """获取任务信息"""
        job = self.scheduler.get_job(job_id)
        if job is None:
            return {}
        
        return {
            "id": job.id,
            "name": job.name,
            "trigger": str(job.trigger),
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "misfire_grace_time": job.misfire_grace_time
        }


_scheduler = None

def get_scheduler():
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ProxyScheduler()
    return _scheduler
