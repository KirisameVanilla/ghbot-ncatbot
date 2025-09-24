"""
GitHub Bot 模块

一个用于处理GitHub webhook并发送QQ通知的模块
"""

from .bot import GitHubBot
from .webhook import GitHubWebhookHandler

__version__ = "1.0.0"
__all__ = ["GitHubBot", "GitHubWebhookHandler"]
