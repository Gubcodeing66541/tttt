# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件
Telegram 群聊监听系统打包配置
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# 设置 Python 运行时环境
os.environ['PYTHONIOENCODING'] = 'utf-8'

block_cipher = None

# 收集所有需要的模块和数据文件
datas = []

# 收集 Telethon 相关数据文件
try:
    telethon_datas = collect_all('telethon')
    datas += telethon_datas[0]  # data files
except:
    pass

# 收集 Jinja2 模板文件
try:
    jinja2_datas = collect_data_files('jinja2')
    datas += jinja2_datas
except:
    pass

# 添加 HTML 模板文件
datas += [('app/templates', 'app/templates')]

# 隐藏的导入模块
hiddenimports = [
    # FastAPI 相关
    'fastapi',
    'fastapi.applications',
    'fastapi.routing',
    'fastapi.middleware',
    'fastapi.staticfiles',
    'pydantic',
    'pydantic.json',
    'uvicorn',
    'uvicorn.protocols',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'websockets',
    'websockets.server',
    
    # Telegram 相关
    'telethon',
    'telethon.client',
    'telethon.sessions',
    'telethon.tl',
    'telethon.tl.functions',
    'telethon.tl.types',
    'telethon.network',
    'telethon.helpers',
    'telethon.extensions',
    'telethon.crypto',
    
    # 其他依赖
    'aiohttp',
    'aiofiles',
    'multipart',
    'asyncio',
    'async_generator',
    'async_timeout',
    
    # 数据处理
    'json',
    'orjson',
    'msgpack',
    'cryptg',
    
    # 加密相关
    'rsa',
    'rsa.core',
    'rsa.pkcs1',
    'rsa.pkcs1_v15',
    'rsa.pem',
    'rsa.asn1',
    'rsa.common',
    'rsa.randnum',
    'rsa.transform',
    
    # WebSocket
    'websockets',
    'websockets.client',
    
    # 应用模块
    'app.api',
    'app.process_manager',
    'app.telegram_client',
]

# 分析主程序
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 创建 PYZ 文件（Python 字节码）
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TelegramMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口，用于查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以在这里指定图标文件
)

