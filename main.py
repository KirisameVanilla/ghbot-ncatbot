"""
GitHub Bot 主入口文件
"""

from ghbot import GitHubBot


def main():
    """主函数"""
    # 创建并启动GitHub Bot
    bot = GitHubBot("gh_config.yaml")

    # 运行Bot（阻塞模式）
    bot.run(bot_debug=True, webhook_debug=False)


if __name__ == "__main__":
    main()
