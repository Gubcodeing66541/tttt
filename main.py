"""
Telegram 群聊监听系统 - 主程序入口
"""
import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    print("=" * 60)
    print("Telegram 群聊监听系统")
    print("=" * 60)
    print(f"监听地址: http://localhost:8000")
    print("=" * 60)
    print("请在浏览器中配置 API 凭证")
    print()
    
    # 启动服务
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()

