#!/usr/bin/env python3
"""
本地 SOCKS5 代理服务器
监听 127.0.0.1:1080
支持浏览器代理配置
"""

import socket
import sys
import threading
import struct
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class SOCKS5Server:
    def __init__(self, host='127.0.0.1', port=1080):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
    def start(self):
        """启动 SOCKS5 代理服务"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(128)
            self.running = True
            
            logger.info(f"✓ SOCKS5 代理已启动: {self.host}:{self.port}")
            logger.info(f"✓ 浏览器代理设置: {self.host}:{self.port} (SOCKS5)")
            logger.info(f"✓ 等待连接...\n")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    # 使用线程处理每个客户端
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_addr)
                    )
                    thread.daemon = True
                    thread.start()
                except KeyboardInterrupt:
                    logger.info("\n代理服务已停止")
                    self.running = False
                    break
        except OSError as e:
            logger.error(f"✗ 启动失败: {e}")
            sys.exit(1)
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_client(self, client_socket, client_addr):
        """处理客户端连接"""
        try:
            # 第一步: 接收客户端 SOCKS5 握手请求
            data = client_socket.recv(1024)
            if not data or data[0] != 5:
                client_socket.close()
                return
            
            # 回复: 不需要身份验证
            client_socket.send(b'\x05\x00')
            
            # 第二步: 接收连接请求
            data = client_socket.recv(1024)
            if data[1] != 1:  # 只支持 CONNECT
                client_socket.close()
                return
            
            # 解析目标地址
            addr_type = data[3]
            target_host = None
            target_port = None
            
            if addr_type == 1:  # IPv4
                target_host = '.'.join(map(str, data[4:8]))
                target_port = struct.unpack('>H', data[8:10])[0]
            elif addr_type == 3:  # 域名
                domain_len = data[4]
                target_host = data[5:5+domain_len].decode('utf-8')
                target_port = struct.unpack('>H', data[5+domain_len:7+domain_len])[0]
            elif addr_type == 4:  # IPv6
                target_host = ':'.join([hex(struct.unpack('>H', data[4+i*2:6+i*2])[0])[2:] for i in range(8)])
                target_port = struct.unpack('>H', data[20:22])[0]
            
            if not target_host or not target_port:
                client_socket.close()
                return
            
            logger.info(f"[连接] 来自 {client_addr[0]}:{client_addr[1]}")
            logger.info(f"  → 目标: {target_host}:{target_port}")
            
            # 连接目标服务器
            try:
                target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_socket.connect((target_host, target_port))
                
                # 回复: 连接成功
                client_socket.send(b'\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x00')
                
                # 双向转发数据
                self.forward_data(client_socket, target_socket, client_addr)
                
            except socket.error as e:
                logger.warning(f"  ✗ 连接失败: {e}")
                client_socket.send(b'\x05\x01')
                client_socket.close()
        except Exception as e:
            logger.error(f"处理客户端错误: {e}")
        finally:
            client_socket.close()
    
    def forward_data(self, client_socket, target_socket, client_addr):
        """双向转发数据"""
        def recv_and_send(src, dst, direction):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
            except:
                pass
        
        # 创建双向转发线程
        c2t = threading.Thread(
            target=recv_and_send,
            args=(client_socket, target_socket, 'client->target')
        )
        t2c = threading.Thread(
            target=recv_and_send,
            args=(target_socket, client_socket, 'target->client')
        )
        
        c2t.daemon = True
        t2c.daemon = True
        
        c2t.start()
        t2c.start()
        
        c2t.join()
        t2c.join()
        
        logger.info(f"  ✓ 连接已关闭\n")
        target_socket.close()


if __name__ == '__main__':
    port = 1080
    
    # 支持命令行参数指定端口
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"无效的端口号: {sys.argv[1]}")
            sys.exit(1)
    
    server = SOCKS5Server('127.0.0.1', port)
    server.start()
