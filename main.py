import threading
import time
from ncatbot.core import BotClient
from ncatbot.core.api import BotAPI
from ncatbot.utils import config
from github_webhook import GitHubWebhookHandler

import yaml


def main():
    """主函数"""
    # 加载配置
    with open("gh_config.yaml", "r", encoding="utf-8") as f:
        config_data = yaml.load(f.read(), Loader=yaml.FullLoader)

    # 启动机器人
    bot: BotClient = BotClient()
    api: BotAPI = bot.run_backend(debug=True)

    print("🤖 NapCat机器人后端已启动")
    api.send_private_text_sync(config.root, "🤖 GitHub监听Bot已启动")

    # 启动GitHub webhook服务器
    try:
        webhook_handler = GitHubWebhookHandler(api, config_data)
        webhook_port = config_data.get("github", {}).get("port", 5000)

        # 在新线程中运行webhook服务器
        webhook_thread = threading.Thread(
            target=webhook_handler.run,
            kwargs={"host": "0.0.0.0", "port": webhook_port, "debug": False},
            daemon=True,
        )
        webhook_thread.start()

        print(f"🌐 GitHub Webhook服务器已启动在端口 {webhook_port}")

        # 发送webhook启动通知
        webhook_msg = f"🌐 GitHub Webhook服务已启动\n📡 监听端口: {webhook_port}\n🔗 Webhook URL: http://你的服务器IP:{webhook_port}/webhook"

        if config.root:
            api.send_private_text_sync(config.root, webhook_msg)

        # 保持主线程运行
        print("✅ 所有服务已启动，Bot正在运行...")
        print("按 Ctrl+C 停止服务")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，正在关闭服务...")

    except Exception as e:
        error_msg = f"❌ 启动GitHub Webhook服务时出错: {e}"
        print(error_msg)

        if config.root:
            api.send_private_text_sync(config.root, error_msg)


if __name__ == "__main__":
    main()
