"""
GitHub Bot 主类模块
"""

import threading
import yaml
from logging import Logger
from typing import Dict, Any, Optional

from ncatbot.utils import config, get_log

from ncatbot.plugin_system import NcatBotPlugin, command_registry, group_filter
from ncatbot.core.event import GroupMessageEvent

from .webhook import GitHubWebhookHandler

LOG: Logger = get_log("ghbot")


class GitHubBotPlugin(NcatBotPlugin):
    """GitHub 监听插件"""

    name = "GitHubBotPlugin"
    version = "0.0.1"
    author = "KirisameVanilla"

    gh_command_group = command_registry.group("gh", description="GitHub 监听插件指令组")

    async def on_load(self):
        """
        初始化GitHub Bot

        Args:
            config_path: 配置文件路径
        """
        self.config_path = "gh_config.yaml"
        self.config_data: Dict[str, Any] = {}
        self.webhook_handler: Optional[GitHubWebhookHandler] = None
        self.webhook_thread: Optional[threading.Thread] = None

        # 加载配置
        self._load_config()

        self.start(webhook_debug=False)

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def start(self, webhook_debug: bool = False):
        """
        启动GitHub Bot

        Args:
            webhook_debug: 是否开启webhook调试模式
        """
        try:
            # 启动webhook服务
            self._start_webhook_server(webhook_debug)

            LOG.info("✅ 所有服务已启动，Bot正在运行...")

        except Exception as e:
            error_msg = f"❌ 启动GitHub Bot时出错: {e}"
            LOG.error(error_msg)
            if self.api and config.root:
                self.api.send_private_text_sync(config.root, error_msg)
            raise

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

        LOG.info(f"🌐 GitHub Webhook服务器已启动在端口 {webhook_port}")

    @gh_command_group.command("ping", description="大笨蛋你还活着吗")
    async def is_running(self, event: GroupMessageEvent):
        """检查Bot是否正在运行"""
        is_alive = (
            self.api is not None
            and self.webhook_thread is not None
            and self.webhook_thread.is_alive()
        )
        message = "大笨蛋我还活着" if is_alive else "似了喵"
        await event.reply(message, at=False)

    @group_filter
    @command_registry.command("ghbot", description="基础命令")
    async def on_group_message(self, event: GroupMessageEvent):
        await event.reply(text="干嘛", at=False)
