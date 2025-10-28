"""
FastAPI 路由定义
"""
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from app.process_manager import ProcessManager
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Group Monitor")

# 全局进程管理器
process_manager: Optional[ProcessManager] = None

# API 配置存储文件
CONFIG_FILE = "api_config.json"


# Pydantic 模型
class APIConfigRequest(BaseModel):
    api_id: str
    api_hash: str


class LoginRequest(BaseModel):
    phone: str
    password: Optional[str] = None
    second_password: Optional[str] = None


class VerifyRequest(BaseModel):
    code: str
    second_password: Optional[str] = None


class StartMonitorRequest(BaseModel):
    target_group_id: int
    keywords: List[str]
    messages: List[str]
    interval: int = 1


def load_config():
    """加载 API 配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None


def save_config(api_id: str, api_hash: str):
    """保存 API 配置"""
    config = {
        'api_id': api_id,
        'api_hash': api_hash
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)


def init_process_manager():
    """初始化进程管理器"""
    global process_manager
    
    config = load_config()
    if not config:
        return False
    
    try:
        process_manager = ProcessManager(int(config['api_id']), config['api_hash'])
        process_manager.start()
        logger.info("进程管理器已启动")
        return True
    except Exception as e:
        logger.error(f"初始化进程管理器失败: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """启动时尝试加载配置"""
    if init_process_manager():
        # 尝试连接检查登录状态
        if process_manager:
            process_manager.send_command({'type': 'connect'})
            response = process_manager.get_response(timeout=3.0)
            if response and response.get('is_authorized'):
                logger.info("检测到已登录状态")
        logger.info("系统已就绪")
    else:
        logger.info("等待用户配置 API 凭证")


@app.on_event("shutdown")
async def shutdown_event():
    global process_manager
    
    if process_manager:
        process_manager.stop()
        logger.info("进程管理器已停止")


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回首页"""
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/config")
async def get_config():
    """获取 API 配置状态"""
    config = load_config()
    
    # 检查登录状态
    is_logged_in = False
    if config and process_manager:
        try:
            process_manager.send_command({'type': 'connect'})
            response = process_manager.get_response(timeout=2.0)
            if response and response.get('is_authorized'):
                is_logged_in = True
        except:
            pass
    
    if config:
        return JSONResponse({
            "configured": True,
            "is_logged_in": is_logged_in,
            "message": "API 已配置" + ("，已登录" if is_logged_in else "，未登录")
        })
    else:
        return JSONResponse({
            "configured": False,
            "is_logged_in": False,
            "message": "请先配置 API 凭证"
        })


@app.post("/api/config")
async def set_config(request: APIConfigRequest):
    """设置 API 配置"""
    try:
        # 验证 API 凭证
        test_manager = ProcessManager(int(request.api_id), request.api_hash)
        test_manager.start()
        
        # 如果测试成功，保存配置
        save_config(request.api_id, request.api_hash)
        
        # 重新初始化全局进程管理器
        global process_manager
        if process_manager:
            process_manager.stop()
        
        process_manager = test_manager
        logger.info("API 配置已保存")
        
        return JSONResponse({
            "success": True,
            "message": "配置成功"
        })
        
    except Exception as e:
        logger.error(f"配置 API 失败: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        })


@app.post("/api/connect")
async def connect():
    """连接 Telegram"""
    if not process_manager:
        return JSONResponse({"success": False, "error": "进程管理器未初始化"})
    
    process_manager.send_command({'type': 'connect'})
    response = process_manager.get_response(timeout=3.0)
    
    if response:
        return JSONResponse(response)
    else:
        return JSONResponse({"success": False, "error": "超时"})


@app.post("/api/send_code")
async def send_code(request: LoginRequest):
    """发送验证码"""
    if not process_manager:
        return JSONResponse({"success": False, "error": "进程管理器未初始化"})
    
    process_manager.send_command({
        'type': 'send_code',
        'phone': request.phone
    })
    response = process_manager.get_response(timeout=30.0, filter_type='code_sent')
    
    if response:
        return JSONResponse(response)
    else:
        return JSONResponse({"success": False, "error": "超时"})


@app.post("/api/verify")
async def verify(request: VerifyRequest):
    """验证登录码"""
    if not process_manager:
        return JSONResponse({"success": False, "error": "进程管理器未初始化"})
    
    # 发送验证命令
    command = {
        'type': 'verify_code',
        'code': request.code
    }
    
    # 如果有二次密码，添加到命令中
    if request.second_password and request.second_password.strip():
        command['password'] = request.second_password
    
    process_manager.send_command(command)
    response = process_manager.get_response(timeout=10.0, filter_type='verify_response')
    
    if response:
        return JSONResponse(response)
    else:
        return JSONResponse({"success": False, "error": "超时"})


@app.get("/api/dialogs")
async def get_dialogs():
    """获取群聊列表"""
    if not process_manager:
        return JSONResponse({"success": False, "error": "进程管理器未初始化"})
    
    process_manager.send_command({'type': 'get_dialogs'})
    response = process_manager.get_response(timeout=10.0, filter_type='dialogs_response')
    
    if response:
        return JSONResponse(response)
    else:
        return JSONResponse({"success": False, "error": "超时"})


@app.post("/api/start_monitor")
async def start_monitor(request: StartMonitorRequest):
    """开始监听"""
    if not process_manager:
        return JSONResponse({"success": False, "error": "进程管理器未初始化"})
    
    process_manager.send_command({
        'type': 'start_monitor',
        'target_group_id': request.target_group_id,
        'keywords': request.keywords,
        'messages': request.messages,
        'interval': request.interval
    })
    response = process_manager.get_response(timeout=5.0)
    
    if response:
        return JSONResponse(response)
    else:
        return JSONResponse({"success": False, "error": "超时"})


@app.post("/api/stop_monitor")
async def stop_monitor():
    """停止监听"""
    if not process_manager:
        return JSONResponse({"success": False, "error": "进程管理器未初始化"})
    
    process_manager.send_command({'type': 'stop_monitor'})
    response = process_manager.get_response(timeout=5.0)
    
    if response:
        return JSONResponse(response)
    else:
        return JSONResponse({"success": False, "error": "超时"})


@app.get("/api/results")
async def get_results():
    """获取监听结果"""
    if not process_manager:
        return JSONResponse({"results": []})
    
    results = process_manager.check_results()
    return JSONResponse({"results": results})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接 - 实时推送监听结果"""
    await websocket.accept()
    
    try:
        while True:
            # 检查新结果
            if process_manager:
                results = process_manager.check_results()
                if results:
                    await websocket.send_json({"results": results})
            
            await asyncio.sleep(0.5)
            
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        await websocket.close()

