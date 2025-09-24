"""
GitHub Bot 主类模块
"""

import threading
import time
import yaml
from logging import Logger
from typing import Dict, Any, Optional

from ncatbot.core import BotClient
from ncatbot.core.api import BotAPI
from ncatbot.utils import config, get_log

from .webhook import GitHubWebhookHandler


class GitHubBot:
    """GitHub Bot 主类，负责整合所有功能"""

    def __init__(self, config_path: str = "gh_config.yaml"):
        """
        初始化GitHub Bot

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.bot: Optional[BotClient] = None
        self.api: Optional[BotAPI] = None
        self.logger: Logger = get_log("ghbot")  # 直接初始化logger
        self.webhook_handler: Optional[GitHubWebhookHandler] = None
        self.webhook_thread: Optional[threading.Thread] = None

        # 加载配置
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def start(self, bot_debug: bool = True, webhook_debug: bool = False):
        """
        启动GitHub Bot

        Args:
            bot_debug: 是否开启bot调试模式
            webhook_debug: 是否开启webhook调试模式
        """
        try:
            # 启动机器人后端
            self._start_bot_backend(bot_debug)

            # 启动webhook服务
            self._start_webhook_server(webhook_debug)

            # 发送启动通知
            self._send_startup_notification()

            self.logger.info("✅ 所有服务已启动，Bot正在运行...")
            self.logger.info("按 Ctrl+C 停止服务")

        except Exception as e:
            error_msg = f"❌ 启动GitHub Bot时出错: {e}"
            self.logger.error(error_msg)
            if self.api and config.root:
                self.api.send_private_text_sync(config.root, error_msg)
            raise

    def _start_bot_backend(self, debug: bool = True):
        """启动机器人后端"""
        self.bot = BotClient()
        self.api = self.bot.run_backend(debug=debug)
        self.logger.info("🤖 NapCat机器人后端已启动")

    def _start_webhook_server(self, debug: bool = False):
        """启动webhook服务器"""
        if not self.api:
            raise RuntimeError("Bot后端未启动，无法启动webhook服务")

        # 创建webhook处理器
        self.webhook_handler = GitHubWebhookHandler(self.api, self.config_data)
        webhook_port = self.config_data.get("github", {}).get("port", 5000)

        # 在新线程中运行webhook服务器
        self.webhook_thread = threading.Thread(
            target=self.webhook_handler.run,
            kwargs={"host": "0.0.0.0", "port": webhook_port, "debug": debug},
            daemon=True,
        )
        self.webhook_thread.start()

        self.logger.info(f"🌐 GitHub Webhook服务器已启动在端口 {webhook_port}")

    def _send_startup_notification(self):
        """发送启动通知"""
        if not self.api:
            return

        # 发送bot启动通知
        if config.root:
            self.api.send_private_text_sync(config.root, "🤖 GitHub监听Bot已启动")

        # 发送webhook启动通知
        webhook_port = self.config_data.get("github", {}).get("port", 5000)
        webhook_msg = f"🌐 GitHub Webhook服务已启动\n📡 监听端口: {webhook_port}\n🔗 Webhook URL: http://你的服务器IP:{webhook_port}/webhook"

        if config.root:
            self.api.send_private_text_sync(config.root, webhook_msg)

    def run(self, bot_debug: bool = True, webhook_debug: bool = False):
        """
        运行GitHub Bot（阻塞模式）

        Args:
            bot_debug: 是否开启bot调试模式
            webhook_debug: 是否开启webhook调试模式
        """
        self.start(bot_debug, webhook_debug)

        # 保持主线程运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """停止GitHub Bot"""
        self.logger.info("🛑 收到停止信号，正在关闭服务...")

        # 这里可以添加更多清理逻辑
        # 比如优雅关闭webhook服务器等

    def is_running(self) -> bool:
        """检查Bot是否正在运行"""
        return (
            self.bot is not None
            and self.api is not None
            and self.webhook_thread is not None
            and self.webhook_thread.is_alive()
        )

    def get_webhook_url(self) -> str:
        """获取webhook URL"""
        port = self.config_data.get("github", {}).get("port", 5000)
        return f"http://你的服务器IP:{port}/webhook"

    def get_health_check_url(self) -> str:
        """获取健康检查URL"""
        port = self.config_data.get("github", {}).get("port", 5000)
        return f"http://你的服务器IP:{port}/health"
