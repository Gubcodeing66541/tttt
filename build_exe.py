"""
Telegram 群聊监听系统打包脚本
使用 PyInstaller 将程序打包成可执行文件

Author: kyle
Date: 2025-10-28 18:09:20
"""
import os
import subprocess
import sys
import shutil

def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装，版本: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        return False

def install_dependencies():
    """安装依赖"""
    print("\n=== 安装依赖 ===")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✓ 依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败: {e}")
        return False

def clean_build_dirs():
    """清理构建目录"""
    print("\n=== 清理构建目录 ===")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"删除: {dir_name}")
            shutil.rmtree(dir_name, ignore_errors=True)

def build_executable():
    """构建可执行文件"""
    print("\n=== 开始构建可执行文件 ===")
    try:
        # 运行 PyInstaller
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "telegram_monitor.spec"
        ], check=True)
        print("✓ 构建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 构建失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Telegram 群聊监听系统 - 打包工具")
    print("=" * 60)
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("\n正在安装 PyInstaller...")
        if not install_dependencies():
            print("\n✗ 打包失败")
            return False
    
    # 询问用户是否清理旧的构建
    response = input("\n是否清理旧的构建文件？(y/n): ").strip().lower()
    if response == 'y':
        clean_build_dirs()
    
    # 构建可执行文件
    if build_executable():
        print("\n" + "=" * 60)
        print("✓ 打包完成！")
        print("=" * 60)
        print("\n可执行文件位置: dist/TelegramMonitor")
        print("\n注意事项:")
        print("1. 需要确保目标机器上有所需的系统库")
        print("2. telegram_session.session 文件需要单独提供")
        print("3. api_config.json 文件会自动包含在打包中")
        print("\n使用方法:")
        print("在 Windows 上: 直接运行 TelegramMonitor.exe")
        print("在 macOS/Linux 上: 运行 ./TelegramMonitor")
        return True
    else:
        print("\n✗ 打包失败")
        return False

if __name__ == "__main__":
    main()

