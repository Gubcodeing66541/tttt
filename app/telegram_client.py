"""
Telegram 客户端多进程实现
处理 Telegram API 的所有操作，与主进程通过队列通信
"""
import asyncio
import logging
from typing import List, Optional
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import Channel, InputPeerEmpty, User
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramWorker:
    """Telegram 工作进程 - 处理所有 Telegram 相关操作"""
    
    def __init__(self, api_id: int, api_hash: str, 
                 command_queue, response_queue, result_queue):
        """
        初始化 Telegram 工作进程
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            command_queue: 命令队列（主进程 -> 工作进程）
            response_queue: 响应队列（工作进程 -> 主进程）
            result_queue: 结果队列（工作进程 -> 主进程）
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.command_queue = command_queue
        self.response_queue = response_queue
        self.result_queue = result_queue
        
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.is_listening = False
        self.monitor_config = None
        self.monitor_target = None
        
        # 监听任务
        self.monitor_task = None
        
    async def run(self):
        """运行工作进程主循环"""
        logger.info("Telegram 工作进程启动")
        
        try:
            while True:
                # 从命令队列获取命令
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    await self.handle_command(command)
                else:
                    await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            await self.cleanup()
    
    async def handle_command(self, command: dict):
        """处理命令"""
        cmd_type = command.get('type')
        logger.info(f"处理命令: {cmd_type}")
        
        if cmd_type == 'connect':
            await self.connect()
        elif cmd_type == 'send_code':
            await self.send_code(command['phone'])
        elif cmd_type == 'verify_code':
            await self.verify_code(command['code'], command.get('password'))
        elif cmd_type == 'get_dialogs':
            await self.get_dialogs()
        elif cmd_type == 'start_monitor':
            await self.start_monitor(command)
        elif cmd_type == 'stop_monitor':
            await self.stop_monitor()
        elif cmd_type == 'disconnect':
            await self.disconnect()
        else:
            logger.warning(f"未知命令类型: {cmd_type}")
    
    async def connect(self):
        """连接 Telegram"""
        try:
            if self.client is None:
                self.client = TelegramClient(
                    'telegram_session',
                    self.api_id,
                    self.api_hash
                )
                await self.client.connect()
                self.is_connected = await self.client.is_user_authorized()
                
                self.response_queue.put({
                    'type': 'connect_response',
                    'success': True,
                    'is_authorized': self.is_connected
                })
                logger.info(f"连接成功，已授权: {self.is_connected}")
            else:
                self.response_queue.put({
                    'type': 'connect_response',
                    'success': True,
                    'is_authorized': self.is_connected,
                    'message': '已经连接'
                })
        except Exception as e:
            logger.error(f"连接失败: {e}")
            self.response_queue.put({
                'type': 'connect_response',
                'success': False,
                'error': str(e)
            })
    
    async def send_code(self, phone: str):
        """发送验证码"""
        try:
            # 如果已有客户端且已断开，先清理
            if self.client is not None:
                try:
                    if self.client.is_connected():
                        await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            # 创建新客户端连接
            self.client = TelegramClient(
                'telegram_session',
                self.api_id,
                self.api_hash
            )
            await self.client.connect()
            
            await self.client.send_code_request(phone)
            
            self.response_queue.put({
                'type': 'code_sent',
                'success': True,
                'message': '验证码已发送'
            })
            logger.info(f"验证码已发送到: {phone}")
        except Exception as e:
            logger.error(f"发送验证码失败: {e}")
            
            # 清理失败的客户端
            if self.client is not None:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            # 友好的错误提示
            error_msg = str(e)
            if 'already used' in error_msg or '所有可用选项' in error_msg:
                user_msg = '验证码选项已用尽，请等待15-30分钟后重试'
            elif 'FloodWaitError' in error_msg:
                user_msg = '请求过于频繁，请稍后重试'
            else:
                user_msg = str(e)
            
            self.response_queue.put({
                'type': 'code_sent',
                'success': False,
                'error': user_msg
            })
    
    async def verify_code(self, code: str, password: Optional[str] = None):
        """验证登录代码"""
        try:
            if self.client is None:
                self.response_queue.put({
                    'type': 'verify_response',
                    'success': False,
                    'error': '未连接'
                })
                return
            
            # 如果已经需要密码状态，直接尝试密码验证
            if hasattr(self.client, '_password_auth') and self.client._password_auth:
                if password:
                    await self._verify_password(password)
                else:
                    self.response_queue.put({
                        'type': 'verify_response',
                        'success': False,
                        'error': '需要二次密码'
                    })
                return
            
            # 先尝试验证码验证
            try:
                await self.client.sign_in(self.client._phone, code)
                self.is_connected = True
                
                self.response_queue.put({
                    'type': 'verify_response',
                    'success': True,
                    'message': '登录成功'
                })
                logger.info("登录成功")
                
            except SessionPasswordNeededError:
                # 需要二次密码
                logger.info("验证码正确，需要二次密码")
                self.client._password_auth = True  # 标记需要密码状态
                
                # 如果有密码，尝试用密码登录
                if password:
                    await self._verify_password(password)
                else:
                    # 没有密码，返回需要密码的提示
                    self.response_queue.put({
                        'type': 'verify_response',
                        'success': False,
                        'error': 'need_password',
                        'message': '验证码正确，请输入二次密码'
                    })
            
        except Exception as e:
            logger.error(f"验证失败: {e}")
            
            # 判断错误类型
            error_msg = str(e)
            if 'password' in error_msg.lower() or '密码' in error_msg:
                self.response_queue.put({
                    'type': 'verify_response',
                    'success': False,
                    'error': '二次密码错误'
                })
            else:
                self.response_queue.put({
                    'type': 'verify_response',
                    'success': False,
                    'error': str(e)
                })
    
    async def _verify_password(self, password: str):
        """验证二次密码"""
        try:
            # 第二次调用 sign_in，使用密码
            await self.client.sign_in(password=password)
            
            # 检查是否成功
            self.is_connected = True
            
            # 清除密码状态标记
            if hasattr(self.client, '_password_auth'):
                delattr(self.client, '_password_auth')
            
            self.response_queue.put({
                'type': 'verify_response',
                'success': True,
                'message': '登录成功'
            })
            logger.info("登录成功（已使用二次密码）")
            
        except Exception as e:
            logger.error(f"二次密码验证失败: {e}")
            
            # 判断是否是密码错误
            error_msg = str(e)
            if 'password' in error_msg.lower() or '密码' in error_msg.lower():
                self.response_queue.put({
                    'type': 'verify_response',
                    'success': False,
                    'error': '二次密码错误'
                })
            else:
                self.response_queue.put({
                    'type': 'verify_response',
                    'success': False,
                    'error': f'登录失败: {str(e)}'
                })
    
    async def get_dialogs(self):
        """获取群聊列表"""
        try:
            if not self.is_connected:
                self.response_queue.put({
                    'type': 'dialogs_response',
                    'success': False,
                    'error': '未登录'
                })
                return
            
            dialogs = await self.client.get_dialogs(limit=None)
            
            # 过滤出群聊
            groups = []
            for dialog in dialogs:
                if isinstance(dialog.entity, Channel):
                    participants_count = getattr(dialog.entity, 'participants_count', 0)
                    groups.append({
                        'id': dialog.entity.id,
                        'title': dialog.entity.title or f"群聊 {dialog.entity.id}",
                        'username': dialog.entity.username or '',
                        'participants_count': participants_count
                    })
            
            self.response_queue.put({
                'type': 'dialogs_response',
                'success': True,
                'groups': groups
            })
            logger.info(f"获取到 {len(groups)} 个群聊")
            
        except Exception as e:
            logger.error(f"获取群聊列表失败: {e}")
            self.response_queue.put({
                'type': 'dialogs_response',
                'success': False,
                'error': str(e)
            })
    
    async def start_monitor(self, config: dict):
        """开始监听"""
        try:
            self.monitor_config = {
                'target_group_id': config['target_group_id'],
                'keywords': config['keywords'],
                'messages': config['messages'],
                'interval': config.get('interval', 1)
            }
            self.monitor_target = config['target_group_id']
            self.is_listening = True
            
            # 注册事件处理器
            self.client.add_event_handler(
                self.handle_new_message,
                events.NewMessage(chats=self.monitor_target)
            )
            
            self.response_queue.put({
                'type': 'monitor_started',
                'success': True,
                'message': '监听已开始'
            })
            logger.info(f"开始监听群聊: {self.monitor_target}")
            
        except Exception as e:
            logger.error(f"启动监听失败: {e}")
            self.response_queue.put({
                'type': 'monitor_started',
                'success': False,
                'error': str(e)
            })
    
    async def handle_new_message(self, event):
        """处理新消息事件"""
        if not self.is_listening or not self.monitor_config:
            return
        
        try:
            message_text = event.message.text or ""
            keywords = self.monitor_config['keywords']
            
            # 检查是否包含关键字
            matched = any(keyword in message_text for keyword in keywords)
            
            if matched:
                logger.info(f"匹配到关键字: {message_text}")
                await self.send_messages()
                
        except Exception as e:
            logger.error(f"处理新消息时出错: {e}")
            self.result_queue.put({
                'type': 'error',
                'error': str(e)
            })
    
    async def stop_monitor(self):
        """停止监听"""
        try:
            self.is_listening = False
            self.monitor_config = None
            
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
                self.monitor_task = None
            
            # 移除事件处理器
            if self.client:
                self.client.remove_event_handler(self.handle_new_message)
            
            self.response_queue.put({
                'type': 'monitor_stopped',
                'success': True,
                'message': '监听已停止'
            })
            logger.info("监听已停止")
            
        except Exception as e:
            logger.error(f"停止监听失败: {e}")
    
    async def send_messages(self):
        """按顺序发送消息"""
        if not self.monitor_config:
            return
        
        messages = self.monitor_config['messages']
        interval = self.monitor_config.get('interval', 1)
        
        for msg in messages:
            try:
                await self.client.send_message(self.monitor_target, msg)
                logger.info(f"发送消息: {msg}")
                
                self.result_queue.put({
                    'type': 'message_sent',
                    'content': msg
                })
                
                if interval > 0:
                    await asyncio.sleep(interval)
                    
            except FloodWaitError as e:
                logger.warning(f"触发了 Flood Wait: {e.seconds}秒")
                await asyncio.sleep(e.seconds)
                
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                self.result_queue.put({
                    'type': 'error',
                    'error': f'发送消息失败: {str(e)}'
                })
    
    async def disconnect(self):
        """断开连接"""
        try:
            await self.stop_monitor()
            
            if self.client:
                await self.client.disconnect()
                self.client = None
                self.is_connected = False
            
            self.response_queue.put({
                'type': 'disconnected',
                'success': True
            })
            logger.info("已断开连接")
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        logger.info("清理资源")
        await self.disconnect()


def telegram_worker_process(api_id, api_hash, command_queue, 
                           response_queue, result_queue):
    """
    工作进程入口函数
    """
    # 设置信号处理
    def signal_handler(sig, frame):
        logger.info("收到停止信号，准备退出")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建工作进程
    worker = TelegramWorker(api_id, api_hash, 
                           command_queue, response_queue, result_queue)
    
    # 运行事件循环
    asyncio.run(worker.run())

