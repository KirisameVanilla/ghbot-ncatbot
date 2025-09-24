# ghbot-ncatbot

> [!NOTE]
> 一个基于 [ncatbot](https://github.com/liyihao1110/ncatbot) 和 [NapCatQQ](https://github.com/NapNeko/NapCatQQ) 的 QQ Bot, 用于订阅 GitHub Repo 动态

## 使用

### 配置

- config.yaml

    这是用于设置 ncatbot 的配置文件. 一般来说, 你只需要更改 `root` 和 `bt_uin`

- gh_config.yaml

    这是用于设置本功能的配置文件, 你需要更改:
    1. github.webhook_secret
    2. notifications.groups
    3. notifications.users

### 运行

> [!TIP]
> 建议使用 [uv](https://github.com/astral-sh/uv)

``` bash
git clone https://github.com/KirisameVanilla/ghbot-ncatbot.git
cd ghbot-ncatbot
uv sync
uv run main.py
```
