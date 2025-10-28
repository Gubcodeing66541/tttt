"""
进程管理器 - 管理主进程和工作进程的通信
"""
import multiprocessing
from queue import Empty
import logging
import time
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessManager:
    """进程管理器 - 管理与 Telegram 工作进程的通信"""
    
    def __init__(self, api_id: int, api_hash: str):
        """
        初始化进程管理器
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
        """
        self.api_id = api_id
        self.api_hash = api_hash
        
        # 创建进程间通信队列
        self.command_queue = multiprocessing.Queue()
        self.response_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        
        # 工作进程
        self.worker_process: Optional[multiprocessing.Process] = None
        
        # 状态
        self.is_running = False
        self.results: list = []
    
    def start(self):
        """启动工作进程"""
        if self.is_running:
            logger.warning("工作进程已在运行")
            return
        
        try:
            self.worker_process = multiprocessing.Process(
                target=self._worker_target,
                args=(
                    self.api_id,
                    self.api_hash,
                    self.command_queue,
                    self.response_queue,
                    self.result_queue
                ),
                daemon=True
            )
            self.worker_process.start()
            self.is_running = True
            logger.info("工作进程已启动")
        except Exception as e:
            logger.error(f"启动工作进程失败: {e}")
            raise
    
    def stop(self):
        """停止工作进程"""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            
            # 发送断开命令
            if self.worker_process:
                self.command_queue.put({'type': 'disconnect'})
                
                # 等待进程结束
                self.worker_process.join(timeout=5)
                
                if self.worker_process.is_alive():
                    logger.warning("工作进程未正常结束，强制终止")
                    self.worker_process.terminate()
                    self.worker_process.join(timeout=3)
                    if self.worker_process.is_alive():
                        self.worker_process.kill()
                
                self.worker_process = None
            
            logger.info("工作进程已停止")
            
        except Exception as e:
            logger.error(f"停止工作进程失败: {e}")
    
    def send_command(self, command: Dict[str, Any]):
        """发送命令到工作进程"""
        if not self.is_running:
            logger.error("工作进程未运行")
            return False
        
        try:
            self.command_queue.put(command)
            logger.info(f"发送命令: {command.get('type')}")
            return True
        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            return False
    
    def get_response(self, timeout: float = 1.0, filter_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """从工作进程获取响应
        
        Args:
            timeout: 超时时间（秒）
            filter_type: 如果指定，只返回匹配该类型的响应
        """
        try:
            # 如果不是过滤模式，直接获取
            if filter_type is None:
                response = self.response_queue.get(timeout=timeout)
                logger.info(f"收到响应: {response.get('type')}")
                return response
            
            # 过滤模式：清空队列中不匹配的响应，直到找到匹配的或超时
            start_time = time.time()
            while True:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(f"响应超时，未找到类型: {filter_type}")
                    return None
                
                try:
                    response = self.response_queue.get(timeout=0.1)
                    if response.get('type') == filter_type:
                        logger.info(f"收到匹配响应: {filter_type}")
                        return response
                    else:
                        logger.warning(f"收到不匹配的响应: {response.get('type')}，期望: {filter_type}")
                        # 继续循环等待
                except Empty:
                    continue
                    
        except Exception as e:
            logger.error(f"获取响应失败: {e}")
            return None
    
    def get_result(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """获取结果（来自 result_queue）"""
        try:
            result = self.result_queue.get(timeout=timeout)
            self.results.append(result)
            logger.info(f"收到结果: {result.get('type')}")
            return result
        except Empty:
            return None
        except Exception as e:
            logger.error(f"获取结果失败: {e}")
            return None
    
    def check_results(self):
        """检查所有待处理结果"""
        results = []
        while True:
            result = self.get_result(timeout=0)
            if result is None:
                break
            results.append(result)
        return results
    
    def clear_results(self):
        """清空结果列表"""
        self.results = []
        while not self.result_queue.empty():
            try:
                self.result_queue.get(timeout=0.1)
            except Empty:
                break
    
    @staticmethod
    def _worker_target(api_id, api_hash, command_queue, response_queue, result_queue):
        """工作进程目标函数"""
        from .telegram_client import telegram_worker_process
        
        try:
            telegram_worker_process(api_id, api_hash, 
                                   command_queue, response_queue, result_queue)
        except Exception as e:
            logger.error(f"工作进程异常: {e}")
        finally:
            logger.info("工作进程退出")

