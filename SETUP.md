# 项目配置指南

## 第一步：配置 Telegram API

### 1. 获取 API 凭证

1. 访问 [my.telegram.org](https://my.telegram.org)
2. 使用你的 Telegram 账号登录
3. 点击 "API development tools"
4. 填写应用信息（可随意填写）：
   - App title: Telegram Monitor
   - Short name: monitor
   - URL: （可选）
   - Platform: Web
   - Description: Monitor system
5. 点击 "Create application"
6. 你会得到 `api_id` 和 `api_hash`

### 2. 创建环境变量文件

在项目根目录创建 `.env` 文件：

```bash
# 如果已经有 .env.example 文件
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 凭证：

```env
API_ID=你的_api_id
API_HASH=你的_api_hash
```

例如：
```env
API_ID=123456
API_HASH=abcdef1234567890abcdef1234567890
```

**重要提示：**
- 不要将 `.env` 文件提交到 Git 仓库
- 妥善保管你的 API 凭证
- 不要分享你的 API 凭证给他人

## 第二步：安装依赖

### 使用 UV（推荐）

```bash
uv sync
```

### 或使用传统方式

```bash
pip install -r requirements.txt
```

## 第三步：启动服务

```bash
uv run python main.py
```

或者：

```bash
python main.py
```

服务启动后，访问 http://localhost:8000 使用网页界面。

## 使用流程

1. **登录 Telegram**
   - 输入手机号（格式：+86 138****）
   - 点击"获取验证码"
   - 输入收到的验证码
   - 如果启用了两步验证，输入二次密码

2. **选择群聊**
   - 点击"获取群聊列表"
   - 从列表中选择要监听的群

3. **配置监听规则**
   - 输入关键字（逗号分隔，如：你好,hello,hi）
   - 输入自动回复消息（每行一条）
   - 设置发送间隔时间（秒）

4. **开始监听**
   - 点击"开始监听"
   - 系统会自动监听群聊消息
   - 当检测到关键字时，自动发送配置的消息

## 注意事项

⚠️ **安全提示**:
- 不要在公共场所使用此工具
- 注意遵守 Telegram 的使用条款
- 不要用于垃圾消息或骚扰他人
- 合理设置消息间隔，避免被限制

⚠️ **限制说明**:
- Telegram 对频繁发送消息有限制
- 如果触发 Flood Wait，系统会自动等待
- 建议设置合理的消息间隔（至少 1 秒以上）

## 故障排除

### 登录失败
- 检查 `.env` 文件中的 API_ID 和 API_HASH 是否正确
- 确认网络连接正常
- 尝试重新获取验证码

### 获取群聊列表失败
- 确认已成功登录
- 检查账号是否有加入群聊
- 查看日志输出获取详细错误信息

### 监听不工作
- 确认已选择群聊
- 检查关键字配置是否正确
- 查看浏览器控制台的日志

## 下一步

配置完成后，就可以开始使用系统了！🎉


