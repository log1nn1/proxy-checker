#!/usr/bin/env python3
"""
代理检查工具 - 主入口

使用方法:
    python main.py fetch          # 获取代理列表
    python main.py check          # 检查代理质量
    python main.py list           # 列出代理
    python main.py stats          # 统计信息
    python main.py cleanup        # 清理过期代理
    python main.py schedule       # 启动定时调度器
    python main.py run check      # 立即执行任务
"""

import asyncio
import logging
import logging.config
import sys
from typing import Optional
from datetime import datetime
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
import click

import config
from proxy_fetcher import fetch_proxies
from proxy_checker import check_all_proxies, check_proxy
from proxy_storage import (
    load_proxies, get_stats, cleanup_proxies,
    delete_proxy, get_proxy
)
from scheduler import get_scheduler
from models.proxy import Proxy

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.version_option(version=config.VERSION, prog_name=config.PROJECT_NAME)
def cli():
    """🌐 代理检查工具 - Proxy Checker"""
    pass


@cli.command()
@click.option('--concurrent', type=int, default=config.MAX_CONCURRENT_FETCHES,
              help='并发获取数')
def fetch_cmd(concurrent: int):
    """📥 从代理源获取代理列表"""
    console.print(Panel("[bold cyan]正在获取代理列表...[/bold cyan]", title="获取代理"))
    
    try:
        proxies = asyncio.run(fetch_proxies())
        
        if proxies:
            console.print(f"\n[green]✓ 成功获取 {len(proxies)} 个代理[/green]\n")
            
            table = Table(title="代理预览（前10个）")
            table.add_column("IP:端口", style="cyan")
            table.add_column("协议", style="magenta")
            table.add_column("来源", style="green")
            table.add_column("添加时间", style="yellow")
            
            for proxy in proxies[:10]:
                table.add_row(
                    proxy.display_url,
                    proxy.protocol,
                    proxy.source or "未知",
                    proxy.added_at.split('T')[0] if proxy.added_at else "未知"
                )
            
            console.print(table)
        else:
            console.print("\n[yellow]⚠ 未获取到任何代理[/yellow]\n")
    
    except Exception as e:
        console.print(f"\n[red]✗ 获取失败: {e}[/red]\n")
        logger.exception("获取代理异常")


@cli.command()
@click.option('--concurrent', type=int, default=config.MAX_CONCURRENT_CHECKS,
              help='并发检查数')
def check_cmd(concurrent: int):
    """🔍 检查所有代理的质量"""
    proxies = load_proxies()
    
    if not proxies:
        console.print("[yellow]⚠ 没有可检查的代理，请先运行 fetch 命令[/yellow]")
        return
    
    console.print(Panel(
        f"[bold cyan]正在检查 {len(proxies)} 个代理的质量...[/bold cyan]",
        title="检查代理"
    ))
    
    try:
        stats = asyncio.run(check_all_proxies())
        
        console.print(f"\n[green]✓ 检查完成[/green]")
        console.print(f"  总计: {stats['total']} 个")
        console.print(f"  成功: {stats['success']} 个")
        console.print(f"  失败: {stats['failed']} 个")
        console.print()
    
    except Exception as e:
        console.print(f"\n[red]✗ 检查失败: {e}[/red]\n")
        logger.exception("检查代理异常")


@cli.command()
@click.option('--quality', type=int, default=1,
              help='最低质量评分 (1-5)')
@click.option('--protocol', type=str, default=None,
              help='过滤协议 (http/https/socks4/socks5)')
@click.option('--limit', type=int, default=50,
              help='显示数量限制')
def list_cmd(quality: int, protocol: str, limit: int):
    """📋 列出代理"""
    proxies = load_proxies()
    
    if protocol:
        proxies = [p for p in proxies if p.protocol == protocol]
    
    if quality > 1:
        proxies = [p for p in proxies if p.quality_score >= quality]
    
    proxies.sort(
        key=lambda p: (p.quality_score, p.stats.success_rate),
        reverse=True
    )
    
    if not proxies:
        console.print("[yellow]⚠ 没有匹配的代理[/yellow]")
        return
    
    table = Table(title=f"代理列表 (共 {len(proxies)} 个，显示前 {min(limit, len(proxies))} 个)")
    table.add_column("IP:端口", style="cyan")
    table.add_column("协议", style="magenta")
    table.add_column("质量", style="yellow")
    table.add_column("成功率", style="green")
    table.add_column("响应时间", style="blue")
    table.add_column("最后检查", style="dim")
    
    quality_labels = {1: "未知", 2: "差", 3: "中", 4: "良", 5: "优"}
    
    for proxy in proxies[:limit]:
        quality_label = quality_labels.get(proxy.quality_score, "未知")
        last_check = proxy.stats.last_check_time
        if last_check:
            last_check = last_check.split('T')[0]
        else:
            last_check = "从未"
        
        table.add_row(
            proxy.display_url,
            proxy.protocol,
            quality_label,
            f"{proxy.stats.success_rate:.1f}%",
            f"{proxy.stats.avg_response_time:.0f}ms",
            last_check
        )
    
    console.print(table)


@cli.command()
def stats_cmd():
    """📊 显示统计信息"""
    stats = get_stats()
    
    console.print(Panel(
        f"[bold cyan]代理统计信息[/bold cyan]",
        title="统计"
    ))
    
    console.print(f"\n[bold]总体统计[/bold]")
    console.print(f"  总代理数: {stats['total']} 个")
    console.print(f"  总检查次数: {stats.get('total_checks', 0)} 次")
    console.print(f"  总体成功率: {stats.get('success_rate', 0):.2f}%")
    console.print(f"  平均响应时间: {stats.get('avg_response_time', 0):.0f}ms")
    
    if stats['by_protocol']:
        console.print(f"\n[bold]按协议分类[/bold]")
        for protocol, count in stats['by_protocol'].items():
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            console.print(f"  {protocol}: {count} 个 ({percentage:.1f}%)")
    
    if stats['by_quality']:
        console.print(f"\n[bold]按质量分类[/bold]")
        quality_labels = {1: "未知", 2: "差", 3: "中", 4: "良", 5: "优"}
        for score, count in sorted(stats['by_quality'].items(), reverse=True):
            label = quality_labels.get(score, "未知")
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            console.print(f"  {label} (评分{score}): {count} 个 ({percentage:.1f}%)")
    
    if stats['by_country']:
        console.print(f"\n[bold]按国家分类 (TOP 10)[/bold]")
        sorted_countries = sorted(
            stats['by_country'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        for country, count in sorted_countries:
            console.print(f"  {country}: {count} 个")
    
    console.print()


@cli.command()
@click.option('--days', type=int, default=config.CLEANUP_CONFIG['max_age_days'],
              help='代理最大保留天数')
@click.option('--quality', type=int, default=config.CLEANUP_CONFIG['min_quality_score'],
              help='最低质量评分')
def cleanup_cmd(days: int, quality: int):
    """🧹 清理过期和低质代理"""
    console.print(Panel(
        f"[bold cyan]正在清理过期/低质代理...[/bold cyan]",
        title="清理"
    ))
    
    try:
        cleanup_proxies()
        console.print("\n[green]✓ 清理完成[/green]\n")
    
    except Exception as e:
        console.print(f"\n[red]✗ 清理失败: {e}[/red]\n")
        logger.exception("清理代理异常")


@cli.command()
@click.option('--ip', type=str, required=True, help='代理IP')
@click.option('--port', type=int, required=True, help='代理端口')
@click.option('--protocol', type=str, default='http', help='协议')
def delete_cmd(ip: str, port: int, protocol: str):
    """🗑️ 删除代理"""
    proxy_key = f"{ip}:{port} ({protocol})"
    
    if delete_proxy(ip, port, protocol):
        console.print(f"[green]✓ 已删除代理: {proxy_key}[/green]")
    else:
        console.print(f"[yellow]⚠ 代理不存在: {proxy_key}[/yellow]")


@cli.command()
@click.option('--foreground', is_flag=True, default=False,
              help='前台运行')
def schedule_cmd(foreground: bool):
    """⏰ 启动定时任务调度器"""
    scheduler = get_scheduler()
    
    console.print(Panel(
        f"[bold cyan]启动定时任务调度器[/bold cyan]",
        title="调度器"
    ))
    
    scheduler.start()
    
    console.print(f"\n[green]✓ 调度器已启动[/green]\n")
    console.print("[bold]已注册的任务:[/bold]")
    
    for job in scheduler.get_jobs():
        info = scheduler.get_job_info(job.id)
        console.print(f"  • {info['name']}")
        console.print(f"    ID: {info['id']}")
        console.print(f"    触发器: {info['trigger']}")
        if info['next_run_time']:
            console.print(f"    下次运行: {info['next_run_time']}")
        console.print()
    
    if foreground:
        console.print("[yellow]按 Ctrl+C 停止调度器...[/yellow]")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            scheduler.stop()
            console.print("\n[green]✓ 调度器已停止[/green]")


@cli.command()
@click.argument('action', type=click.Choice(['fetch', 'check', 'cleanup']))
def run_cmd(action: str):
    """⚙️ 立即运行指定任务"""
    console.print(Panel(
        f"[bold cyan]正在运行任务: {action}[/bold cyan]",
        title="立即执行"
    ))
    
    try:
        if action == 'fetch':
            asyncio.run(fetch_proxies())
        elif action == 'check':
            asyncio.run(check_all_proxies())
        elif action == 'cleanup':
            cleanup_proxies()
        
        console.print(f"\n[green]✓ 任务执行完成[/green]\n")
    
    except Exception as e:
        console.print(f"\n[red]✗ 任务执行失败: {e}[/red]\n")
        logger.exception("任务执行异常")


@cli.command()
@click.option('--ip', type=str, required=True, help='代理IP')
@click.option('--port', type=int, required=True, help='代理端口')
@click.option('--protocol', type=str, default='http', help='协议')
def info_cmd(ip: str, port: int, protocol: str):
    """ℹ️ 查看代理详细信息"""
    proxy = get_proxy(ip, port, protocol)
    
    if not proxy:
        console.print(f"[yellow]⚠ 代理不存在[/yellow]")
        return
    
    console.print(Panel(
        f"[bold cyan]{proxy.display_url}[/bold cyan]",
        title="代理详情"
    ))
    
    quality_labels = {1: "未知", 2: "差", 3: "中", 4: "良", 5: "优"}
    quality_label = quality_labels.get(proxy.quality_score, "未知")
    
    console.print(f"\n[bold]基本信息[/bold]")
    console.print(f"  IP: {proxy.ip}")
    console.print(f"  端口: {proxy.port}")
    console.print(f"  协议: {proxy.protocol}")
    console.print(f"  国家: {proxy.country or '未知'}")
    console.print(f"  匿名级别: {proxy.anonymity or '未知'}")
    console.print(f"  来源: {proxy.source or '未知'}")
    console.print(f"  添加时间: {proxy.added_at or '未知'}")
    
    console.print(f"\n[bold]质量信息[/bold]")
    console.print(f"  评分: {quality_label} ({proxy.quality_score}/5)")
    console.print(f"  成功率: {proxy.stats.success_rate:.2f}%")
    console.print(f"  平均响应时间: {proxy.stats.avg_response_time:.0f}ms")
    console.print(f"  检查次数: {proxy.stats.success_count + proxy.stats.fail_count}")
    console.print(f"    成功: {proxy.stats.success_count}")
    console.print(f"    失败: {proxy.stats.fail_count}")
    console.print(f"  最后检查: {proxy.stats.last_check_time or '从未'}")
    console.print(f"  最后状态: {'成功' if proxy.stats.last_check_status else '失败'}")
    
    if proxy.tags:
        console.print(f"  标签: {', '.join(proxy.tags)}")
    
    console.print()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ 操作已取消[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]✗ 错误: {e}[/red]")
        logger.exception("未捕获的异常")
        sys.exit(1)
