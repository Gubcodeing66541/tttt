# 使用 UV 管理项目的命令

## 安装依赖

```bash
uv sync
```

## 运行服务

```bash
uv run python main.py
```

或者：

```bash
uv run uvicorn app.api:app --host 0.0.0.0 --port 8000
```

## 添加依赖

```bash
uv add package_name
```

## 更新依赖

```bash
uv sync --upgrade
```

## 查看环境

```bash
uv pip list
```


