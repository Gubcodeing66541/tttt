#!/bin/bash
# Docker 打包脚本
# 注意：PyInstaller 不支持跨平台打包
# 此脚本只能打包当前平台的可执行文件

set -e

echo "=========================================="
echo "Telegram 群聊监听系统 - Docker 打包"
echo "=========================================="

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi

# 清理旧文件
echo ""
echo "清理旧的构建文件..."
rm -rf build dist

# 构建镜像
echo ""
echo "构建 Docker 镜像..."
docker build -f Dockerfile.windows -t telegram-monitor-builder:latest .

# 运行打包
echo ""
echo "开始打包..."
docker run --rm \
  -v "$(pwd)/dist:/work/dist" \
  telegram-monitor-builder:latest

# 检查结果
if [ -f "dist/TelegramMonitor" ]; then
    echo ""
    echo "✅ 打包成功！"
    echo "可执行文件: $(pwd)/dist/TelegramMonitor"
    echo ""
    echo "注意："
    echo "- 这是 macOS/Linux 版本的可执行文件"
    echo "- 如果需要 Windows EXE，请在 Windows 环境中打包"
    echo "- 或者使用 GitHub Actions 自动打包"
else
    echo ""
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi

