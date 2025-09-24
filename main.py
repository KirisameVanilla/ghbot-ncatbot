from ncatbot.core import BotClient
from ncatbot.core.api import BotAPI
from ncatbot.utils import config

import yaml

# 基础配置（示例）
with open("debug_config.yaml", "r", encoding="utf-8") as f:
    config_data = yaml.load(f.read(), Loader=yaml.FullLoader)

config.set_bot_uin(config_data["bot_uin"])

if config_data["root"]:
    config.set_root(config_data["root"])

bot: BotClient = BotClient()
api: BotAPI = bot.run_backend(debug=True)  # 后台线程启动，返回全局 API（同步友好）

# 同步接口主动发消息（示例群号/QQ 号请替换）
if config_data["group"]:
    api.send_group_text_sync(config_data["group"], "后端已启动：Hello from backend")
if config_data["root"]:
    api.send_private_text_sync(config_data["root"], "后端问候：Hi")

print("后台已运行，继续做其他同步任务……")
