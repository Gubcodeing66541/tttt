# Telegram 群聊消息监听和自动发送系统

一个基于 FastAPI 和 Telethon 的在线 Telegram 消息监听和自动回复系统。

## 功能特性

- ✅ Telegram API 登录验证（支持二次验证）
- ✅ 群聊列表获取和选择
- ✅ 关键字匹配监听
- ✅ 自动消息发送（可设置间隔时间）
- ✅ 多进程架构，业务逻辑与TG进程分离
- ✅ 网页界面操作，使用简单

## 安装步骤

### 方式一：使用 UV（推荐）

#### 1. 安装 UV（如果还没有）

```bash
# macOS 或 Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

#### 2. 安装依赖

```bash
uv sync
```

#### 3. 配置 Telegram API

前往 [my.telegram.org](https://my.telegram.org) 获取你的 API ID 和 API Hash。

创建 `.env` 文件：

```bash
# 复制示例文件
cp config.env.example .env
```

编辑 `.env` 文件并填入你的凭证：

```env
API_ID=your_api_id
API_HASH=your_api_hash
```

**详细配置指南请查看 [SETUP.md](SETUP.md)**

#### 4. 启动服务

```bash
uv run python main.py
```

### 方式二：使用传统 pip

#### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置 Telegram API

前往 [my.telegram.org](https://my.telegram.org) 获取你的 API ID 和 API Hash。

在项目根目录创建 `.env` 文件：

```env
API_ID=your_api_id
API_HASH=your_api_hash
```

#### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 使用流程

1. **输入登录信息**
   - 输入手机号
   - 输入密码
   - 输入二次密码（如果启用了两步验证）
   - 点击"获取验证码"按钮

2. **输入验证码**
   - 输入收到的验证码
   - 点击"确定登录"
   - 如果验证码错误，可以重新输入

3. **选择监听群聊**
   - 登录成功后，获取群聊列表
   - 从列表中选择要监听消息的群

4. **配置监听规则**
   - 输入需要匹配的关键字
   - 输入要发送的消息列表（每行一条）
   - 设置消息发送间隔时间（秒）

5. **开始监听**
   - 点击"开始监听"按钮
   - 系统开始执行监听任务

6. **自动响应**
   - 监听到包含关键字的消息后，按顺序发送配置的消息
   - 等待下次匹配关键词

## 项目结构

```
tg/
├── main.py                 # 主程序入口
├── app/
│   ├── __init__.py
│   ├── api.py             # FastAPI 路由定义
│   ├── telegram_client.py # Telegram 客户端多进程实现
│   ├── process_manager.py # 进程管理
│   └── templates/
│       └── index.html     # 前端页面
├── requirements.txt        # Python 依赖
└── README.md              # 项目说明
```

## 技术架构

- **后端**: FastAPI + Uvicorn
- **前端**: HTML + JavaScript (原生)
- **Telegram**: Telethon
- **进程通信**: Queue + multiprocessing
- **消息队列**: asyncio.Queue

## 注意事项

⚠️ **安全提示**:
- 妥善保管你的 Telegram API 凭证
- 不要将 `.env` 文件提交到版本控制系统
- 在生产环境中使用 HTTPS

## 许可证

MIT License

