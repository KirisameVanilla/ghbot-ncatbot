import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify
from ncatbot.core.api import BotAPI


class GitHubWebhookHandler:
    """GitHub Webhook处理器"""
    
    def __init__(self, bot_api: BotAPI, config: Dict[str, Any]):
        self.bot_api = bot_api
        self.config = config
        self.webhook_secret = config.get('github', {}).get('webhook_secret', '')
        
        # 创建Flask应用
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """设置路由"""
        @self.app.route('/webhook', methods=['POST'])
        def handle_webhook():
            return self._handle_webhook_request()
            
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})
    
    def _verify_signature(self, payload: bytes, signature: str) -> bool:
        """验证GitHub webhook签名"""
        if not self.webhook_secret:
            return True  # 如果没有设置密钥，跳过验证
            
        if not signature:
            return False
            
        # GitHub发送的签名格式：sha256=xxxxx
        try:
            sha_name, signature = signature.split('=')
        except ValueError:
            return False
            
        if sha_name != 'sha256':
            return False
            
        # 计算期望的签名
        mac = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            digestmod=hashlib.sha256
        )
        
        return hmac.compare_digest(mac.hexdigest(), signature)
    
    def _handle_webhook_request(self):
        """处理webhook请求"""
        try:
            # 获取签名
            signature = request.headers.get('X-Hub-Signature-256', '')
            
            # 验证签名
            if not self._verify_signature(request.data, signature):
                return jsonify({"error": "Invalid signature"}), 401
            
            # 获取事件类型
            event_type = request.headers.get('X-GitHub-Event')
            if not event_type:
                return jsonify({"error": "Missing event type"}), 400
            
            # 解析payload
            payload = request.get_json()
            if not payload:
                return jsonify({"error": "Invalid JSON payload"}), 400
            
            # 处理事件
            self._process_github_event(event_type, payload)
            
            return jsonify({"status": "ok"}), 200
            
        except Exception as e:
            print(f"处理webhook时出错: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    def _process_github_event(self, event_type: str, payload: Dict[str, Any]):
        """处理GitHub事件"""
        # 获取仓库信息
        repo_info = payload.get('repository', {})
        repo_name = repo_info.get('full_name', 'Unknown')
        
        # 检查仓库白名单
        whitelist = self.config.get('notifications', {}).get('repo_whitelist', [])
        if whitelist and repo_name not in whitelist:
            return
        
        # 检查事件是否需要通知
        events_config = self.config.get('notifications', {}).get('events', {})
        
        message = None
        
        if event_type == 'push' and events_config.get('push', False):
            message = self._format_push_message(payload)
        elif event_type == 'pull_request' and events_config.get('pull_request', False):
            message = self._format_pull_request_message(payload)
        elif event_type == 'issues' and events_config.get('issues', False):
            message = self._format_issues_message(payload)
        elif event_type == 'release' and events_config.get('release', False):
            message = self._format_release_message(payload)
        elif event_type == 'star' and events_config.get('star', False):
            message = self._format_star_message(payload)
        elif event_type == 'fork' and events_config.get('fork', False):
            message = self._format_fork_message(payload)
        
        if message:
            self._send_notifications(message)
    
    def _format_push_message(self, payload: Dict[str, Any]) -> str:
        """格式化推送消息"""
        repo = payload['repository']['full_name']
        pusher = payload['pusher']['name']
        ref = payload['ref'].split('/')[-1]  # 分支名
        commits = payload.get('commits', [])
        
        message = f"🔄 [{repo}] 新推送\n"
        message += f"👤 推送者: {pusher}\n"
        message += f"🌿 分支: {ref}\n"
        message += f"📝 提交数: {len(commits)}\n"
        
        if commits:
            message += "\n最新提交:\n"
            for commit in commits[-3:]:  # 最多显示3个提交
                author = commit['author']['name']
                msg = commit['message'].split('\n')[0][:50]  # 取第一行，最多50字符
                message += f"  • {author}: {msg}\n"
        
        return message.strip()
    
    def _format_pull_request_message(self, payload: Dict[str, Any]) -> str:
        """格式化PR消息"""
        action = payload['action']
        pr = payload['pull_request']
        repo = payload['repository']['full_name']
        
        action_map = {
            'opened': '创建了',
            'closed': '关闭了',
            'merged': '合并了',
            'reopened': '重新打开了'
        }
        
        action_text = action_map.get(action, action)
        
        message = f"🔀 [{repo}] PR {action_text}\n"
        message += f"👤 作者: {pr['user']['login']}\n"
        message += f"📋 标题: {pr['title']}\n"
        message += f"🔗 链接: {pr['html_url']}"
        
        return message
    
    def _format_issues_message(self, payload: Dict[str, Any]) -> str:
        """格式化Issue消息"""
        action = payload['action']
        issue = payload['issue']
        repo = payload['repository']['full_name']
        
        action_map = {
            'opened': '创建了',
            'closed': '关闭了',
            'reopened': '重新打开了'
        }
        
        action_text = action_map.get(action, action)
        
        message = f"🐛 [{repo}] Issue {action_text}\n"
        message += f"👤 作者: {issue['user']['login']}\n"
        message += f"📋 标题: {issue['title']}\n"
        message += f"🔗 链接: {issue['html_url']}"
        
        return message
    
    def _format_release_message(self, payload: Dict[str, Any]) -> str:
        """格式化发布消息"""
        action = payload['action']
        release = payload['release']
        repo = payload['repository']['full_name']
        
        if action == 'published':
            message = f"🚀 [{repo}] 新版本发布\n"
            message += f"🏷️ 版本: {release['tag_name']}\n"
            message += f"📝 标题: {release['name']}\n"
            message += f"🔗 链接: {release['html_url']}"
        else:
            return ""
        
        return message
    
    def _format_star_message(self, payload: Dict[str, Any]) -> str:
        """格式化点星消息"""
        action = payload['action']
        repo = payload['repository']['full_name']
        user = payload['sender']['login']
        
        if action == 'created':
            message = f"⭐ [{repo}] 获得新星标\n"
            message += f"👤 用户: {user}\n"
            message += f"🌟 总星数: {payload['repository']['stargazers_count']}"
        else:
            return ""
        
        return message
    
    def _format_fork_message(self, payload: Dict[str, Any]) -> str:
        """格式化Fork消息"""
        repo = payload['repository']['full_name']
        user = payload['sender']['login']
        
        message = f"🍴 [{repo}] 被Fork\n"
        message += f"👤 用户: {user}\n"
        message += f"🔢 总Fork数: {payload['repository']['forks_count']}"
        
        return message
    
    def _send_notifications(self, message: str):
        """发送通知消息"""
        notifications_config = self.config.get('notifications', {})
        
        # 发送到群组
        groups = notifications_config.get('groups', [])
        for group_id in groups:
            try:
                self.bot_api.send_group_text_sync(group_id, message)
            except Exception as e:
                print(f"发送群消息失败 {group_id}: {e}")
        
        # 发送给用户
        users = notifications_config.get('users', [])
        for user_id in users:
            try:
                self.bot_api.send_private_text_sync(user_id, message)
            except Exception as e:
                print(f"发送私聊消息失败 {user_id}: {e}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """运行webhook服务器"""
        print(f"GitHub Webhook服务器启动在 http://{host}:{port}")
        print(f"Webhook URL: http://{host}:{port}/webhook")
        self.app.run(host=host, port=port, debug=debug)