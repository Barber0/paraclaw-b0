#!/usr/bin/env python3
"""
团队级 Worktree Session Manager - 支持多人协作
绑定信息存储在项目目录，随 Git 共享
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime


class TeamWorktreeManager:
    """
    团队级 Worktree 管理器
    
    核心设计：
    - 绑定信息存储在项目目录 .paraclaw/worktree-sessions.json
    - 随 Git 提交共享给团队成员
    - 支持多人同时开发不同分支
    - 自动检测冲突（两人绑定同一分支）
    """
    
    def __init__(self, repo_path=None):
        """
        Args:
            repo_path: Git 仓库路径，默认当前目录
        """
        if repo_path is None:
            repo_path = self._find_git_root() or '.'
        self.repo_path = Path(repo_path).resolve()
        self.config_dir = self.repo_path / '.paraclaw'
        self.config_file = self.config_dir / 'worktree-sessions.json'
        self._ensure_config_dir()
    
    def _find_git_root(self) -> str:
        """查找 Git 根目录"""
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / '.git').exists():
                return str(cwd)
            cwd = cwd.parent
        return None
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_mappings(self) -> dict:
        """加载团队绑定信息"""
        if not self.config_file.exists():
            return {'sessions': {}, 'members': {}}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'sessions': {}, 'members': {}}
    
    def _save_mappings(self, mappings: dict):
        """保存团队绑定信息"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
    
    def get_user_id(self) -> str:
        """
        生成用户唯一标识
        组合：用户名 + 主机名 + 平台
        """
        import getpass
        import socket
        
        username = getpass.getuser()
        hostname = socket.gethostname()
        platform = os.environ.get('OPENCLAW_PLATFORM', 'unknown')
        
        # 生成短哈希
        user_str = f"{username}@{hostname}:{platform}"
        user_hash = hashlib.md5(user_str.encode()).hexdigest()[:8]
        
        return f"{username}_{user_hash}"
    
    def get_session_id(self) -> str:
        """获取当前 Session ID"""
        for env_var in ['OPENCLAW_SESSION_ID', 'CHAT_ID', 'SESSION_KEY']:
            if env_var in os.environ:
                return os.environ[env_var]
        return self.get_user_id()
    
    def bind_team_worktree(self, branch_name: str, user_name: str = None, 
                          platform: str = None) -> dict:
        """
        绑定到团队 Worktree
        
        Args:
            branch_name: 分支名
            user_name: 用户标识（可选，默认自动生成）
            platform: 平台标识（可选，如 feishu/discord/slack）
        """
        user_id = user_name or self.get_user_id()
        session_id = self.get_session_id()
        platform = platform or os.environ.get('OPENCLAW_PLATFORM', 'unknown')
        
        # 确定 worktree 路径：项目目录-worktrees/用户名-分支名/
        worktree_base = self.repo_path.parent / f"{self.repo_path.name}-worktrees"
        worktree_path = worktree_base / f"{user_id}_{branch_name}"
        
        mappings = self._load_mappings()
        
        # 检查是否有人已经绑定这个分支
        existing_users = []
        for uid, info in mappings['sessions'].items():
            if info['branch_name'] == branch_name and uid != user_id:
                existing_users.append({
                    'user_id': uid,
                    'platform': info.get('platform', 'unknown'),
                    'updated_at': info.get('updated_at')
                })
        
        # 创建 Git worktree
        self._create_git_worktree(branch_name, worktree_path)
        
        # 保存绑定信息
        mappings['sessions'][user_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'branch_name': branch_name,
            'worktree_path': str(worktree_path),
            'platform': platform,
            'repo_path': str(self.repo_path),
            'updated_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # 更新成员列表
        if user_id not in mappings['members']:
            mappings['members'][user_id] = {
                'first_seen': datetime.now().isoformat(),
                'platforms': []
            }
        if platform not in mappings['members'][user_id]['platforms']:
            mappings['members'][user_id]['platforms'].append(platform)
        
        self._save_mappings(mappings)
        
        result = {
            'user_id': user_id,
            'branch_name': branch_name,
            'worktree_path': str(worktree_path),
            'conflicts': existing_users,
            'message': '绑定成功'
        }
        
        if existing_users:
            result['warning'] = f"注意：{len(existing_users)} 个用户也在开发此分支"
        
        return result
    
    def _create_git_worktree(self, branch_name: str, worktree_path: Path):
        """创建 Git worktree"""
        import subprocess
        
        # 检查分支是否存在
        result = subprocess.run(
            ['git', '-C', str(self.repo_path), 'branch', '--list', branch_name],
            capture_output=True, text=True
        )
        
        # 创建分支（如果不存在）
        if branch_name not in result.stdout:
            subprocess.run(
                ['git', '-C', str(self.repo_path), 'branch', branch_name],
                capture_output=True
            )
        
        # 创建 worktree（如果不存在）
        if not worktree_path.exists():
            subprocess.run(
                ['git', '-C', str(self.repo_path), 'worktree', 'add', 
                 str(worktree_path), branch_name],
                capture_output=True
            )
    
    def get_team_status(self) -> dict:
        """获取团队状态"""
        mappings = self._load_mappings()
        
        # 按分支分组
        branches = {}
        for user_id, info in mappings['sessions'].items():
            branch = info['branch_name']
            if branch not in branches:
                branches[branch] = []
            branches[branch].append({
                'user_id': user_id,
                'platform': info.get('platform', 'unknown'),
                'worktree_path': info['worktree_path'],
                'updated_at': info.get('updated_at'),
                'status': info.get('status', 'active')
            })
        
        return {
            'repo': str(self.repo_path),
            'total_members': len(mappings['members']),
            'active_sessions': len(mappings['sessions']),
            'branches': branches
        }
    
    def find_user_binding(self, user_id: str = None) -> dict:
        """查找用户绑定"""
        user_id = user_id or self.get_user_id()
        mappings = self._load_mappings()
        return mappings['sessions'].get(user_id)
    
    def unbind_team_worktree(self, user_id: str = None) -> bool:
        """解除绑定"""
        user_id = user_id or self.get_user_id()
        mappings = self._load_mappings()
        
        if user_id in mappings['sessions']:
            # 标记为不活跃，但不删除记录（保留历史）
            mappings['sessions'][user_id]['status'] = 'inactive'
            mappings['sessions'][user_id]['unbound_at'] = datetime.now().isoformat()
            self._save_mappings(mappings)
            return True
        return False
    
    def sync_to_git(self, commit_message: str = "Update worktree bindings"):
        """将绑定信息提交到 Git"""
        import subprocess
        
        # 添加配置文件
        subprocess.run(
            ['git', '-C', str(self.repo_path), 'add', str(self.config_file)],
            capture_output=True
        )
        
        # 提交
        result = subprocess.run(
            ['git', '-C', str(self.repo_path), 'commit', '-m', commit_message],
            capture_output=True, text=True
        )
        
        return result.returncode == 0
    
    def get_cd_command(self, user_id: str = None) -> str:
        """获取进入 worktree 的命令"""
        info = self.find_user_binding(user_id)
        if info and info.get('status') == 'active':
            return f"cd '{info['worktree_path']}'"
        return None


def main():
    """团队版 CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Team Worktree Session Manager - 多人协作版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
团队特性:
  - 绑定信息存储在项目 .paraclaw/ 目录
  - 支持 git commit 共享给团队成员
  - 自动检测多人开发同一分支
  - 支持多平台（飞书/Discord/Slack）

示例:
  # 绑定并标识用户和平台
  worktree-session-team bind feature-auth --user alice --platform feishu
  
  # 查看团队状态
  worktree-session-team status
  
  # 提交绑定信息到 git
  worktree-session-team sync
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # bind 命令
    bind_parser = subparsers.add_parser('bind', help='绑定到团队 worktree')
    bind_parser.add_argument('branch_name', help='分支名')
    bind_parser.add_argument('--user', '-u', help='用户标识')
    bind_parser.add_argument('--platform', '-p', help='平台（feishu/discord/slack）')
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='查看团队状态')
    
    # sync 命令
    sync_parser = subparsers.add_parser('sync', help='提交到 git')
    sync_parser.add_argument('--message', '-m', default='Update worktree bindings',
                            help='提交信息')
    
    # cd 命令
    cd_parser = subparsers.add_parser('cd', help='获取 cd 命令')
    cd_parser.add_argument('--user', '-u', help='用户标识')
    
    args = parser.parse_args()
    
    manager = TeamWorktreeManager()
    
    if args.command == 'bind':
        result = manager.bind_team_worktree(
            args.branch_name, 
            user_name=args.user,
            platform=args.platform
        )
        print(f"✅ {result['message']}")
        print(f"   用户: {result['user_id']}")
        print(f"   分支: {result['branch_name']}")
        print(f"   Worktree: {result['worktree_path']}")
        if result.get('warning'):
            print(f"   ⚠️  {result['warning']}")
            for conflict in result['conflicts']:
                print(f"      - {conflict['user_id']} ({conflict['platform']})")
    
    elif args.command == 'status':
        status = manager.get_team_status()
        print(f"📊 项目: {status['repo']}")
        print(f"   团队成员: {status['total_members']}")
        print(f"   活跃会话: {status['active_sessions']}")
        print(f"\n📋 分支分布:")
        for branch, users in status['branches'].items():
            print(f"\n  🌿 {branch} ({len(users)} 人)")
            for u in users:
                status_icon = "🟢" if u['status'] == 'active' else "⚪"
                print(f"     {status_icon} {u['user_id']} ({u['platform']})")
    
    elif args.command == 'sync':
        if manager.sync_to_git(args.message):
            print("✅ 绑定信息已提交到 Git")
            print("   团队成员可以 git pull 查看最新状态")
        else:
            print("⚠️  没有变更需要提交，或提交失败")
    
    elif args.command == 'cd':
        cmd = manager.get_cd_command(args.user)
        if cmd:
            print(cmd)
        else:
            print("# 未找到绑定", file=sys.stderr)
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
