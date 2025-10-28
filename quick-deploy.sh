#!/bin/bash
# 一键提交到 GitHub 并触发 Windows EXE 自动打包

set -e

echo "=========================================="
echo "🚀 快速部署 - Windows EXE 打包"
echo "=========================================="
echo ""

# 检查是否在 Git 仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 这不是一个 Git 仓库"
    exit 1
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 检测到未提交的更改"
    echo ""
    
    # 显示更改
    echo "更改内容："
    git status --short
    
    echo ""
    read -p "是否提交这些更改？(y/n): " confirm
    
    if [ "$confirm" = "y" ]; then
        # 添加所有文件
        git add .
        
        # 获取提交信息
        read -p "请输入提交信息（按回车使用默认信息）: " commit_msg
        
        if [ -z "$commit_msg" ]; then
            commit_msg="Add PyInstaller build configuration for Windows EXE - $(date +"%Y-%m-%d %H:%M:%S")"
        fi
        
        git commit -m "$commit_msg"
        echo "✅ 已提交更改"
    else
        echo "❌ 已取消"
        exit 1
    fi
fi

# 检查远程仓库
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo "❌ 未配置远程仓库"
    echo ""
    echo "请先添加远程仓库："
    echo "  git remote add origin https://github.com/你的用户名/tg.git"
    exit 1
fi

# 显示当前分支
current_branch=$(git branch --show-current)
echo ""
echo "当前分支: $current_branch"

# 获取下一个版本号
read -p "请输入版本号（如 v1.0.0，按回车使用 v1.0.0）: " version
if [ -z "$version" ]; then
    version="v1.0.0"
fi

# 检查是否已经存在该 tag
if git rev-parse "$version" > /dev/null 2>&1; then
    echo ""
    read -p "⚠️  标签 $version 已存在，是否覆盖？(y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "❌ 已取消"
        exit 1
    fi
    git tag -d "$version"
fi

echo ""
echo "📦 创建标签: $version"
git tag -a "$version" -m "Release $version - Windows EXE"

echo ""
read -p "是否推送到 GitHub 并触发自动打包？(y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "❌ 已取消"
    exit 1
fi

echo ""
echo "📤 推送代码到 GitHub..."
git push origin "$current_branch"

echo ""
echo "📤 推送标签到 GitHub..."
git push origin "$version"

echo ""
echo "=========================================="
echo "✅ 已触发 Windows EXE 自动打包！"
echo "=========================================="
echo ""
echo "📊 查看打包进度："
echo "https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//' | sed 's/\.git$//')/actions"
echo ""
echo "📦 下载 EXE（打包完成后，约 5-10 分钟）："
echo "https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//' | sed 's/\.git$//')/releases/tag/$version"
echo ""
echo "⏳ 请等待 GitHub Actions 自动打包完成..."

