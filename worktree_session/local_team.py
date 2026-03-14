#!/usr/bin/env python3
"""
本地团队版 Worktree Session Manager
支持同一机器上的多用户/多平台绑定管理
"""

import os
import sys
import json
import getpass
from pathlib import Path
from datetime import datetime


class LocalTeamManager:
    """
    本地团队管理器
    
    设计目标：
    - 支持同一机器上的多用户（不同账号/不同平台）
    - 绑定信息存储在 ~/.openclaw/worktree-sessions.json（本地）
    - Git 远程协作由 Git 自己处理，我们只管理本地 worktree 映射
    """
    
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.openclaw")
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "worktree-sessions.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_mappings(self) -> dict:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_mappings(self, mappings: dict):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
    
    def get_user_context(self) -> dict:
        """
        获取当前用户上下文
        组合：系统用户名 + 平台标识
        """
        username = getpass.getuser()
        
        # 检测平台
        if 'FEISHU_CHAT_ID' in os.environ or 'CHAT_ID' in os.environ and 'feishu' in os.environ.get('OPENCLAW_CHANNEL', '').lower():
            platform = 'feishu'
        elif 'DISCORD_GUILD_ID' in os.environ:
            platform = 'discord'
        elif 'SLACK_CHANNEL' in os.environ:
            platform = 'slack'
        else:
            platform = os.environ.get('OPENCLAW_PLATFORM', 'local')
        
        # 检测会话ID
        session_id = os.environ.get('CHAT_ID') or \
                     os.environ.get('OPENCLAW_SESSION_ID') or \
                     os.environ.get('SESSION_KEY') or \
                     f"{username}_{platform}"
        
        return {
            'username': username,
            'platform': platform,
            'session_id': session_id,
            'user_key': f"{username}:{platform}:{session_id[:20]}"
        }
    
    def bind_worktree(self, repo_path: str, branch_name: str, 
                     label: str = None) -> dict:
        """
        绑定当前用户上下文到 worktree
        """
        ctx = self.get_user_context()
        user_key = ctx['user_key']
        
        repo_path = Path(repo_path).resolve()
        
        # 检查仓库有效性
        if not (repo_path / ".git").exists():
            raise ValueError(f"无效的 Git 仓库: {repo_path}")
        
        # 确定 worktree 路径
        worktree_base = repo_path.parent / f"{repo_path.name}-worktrees"
        
        # 用户标识加入路径，避免冲突
        user_short = ctx['username'][:8]
        worktree_path = worktree_base / f"{user_short}_{branch_name}"
        
        # 创建 Git worktree
        self._create_git_worktree(repo_path, branch_name, worktree_path)
        
        # 保存绑定
        mappings = self._load_mappings()
        mappings[user_key] = {
            'username': ctx['username'],
            'platform': ctx['platform'],
            'session_id': ctx['session_id'],
            'repo_path': str(repo_path),
            'branch_name': branch_name,
            'worktree_path': str(worktree_path),
            'label': label or f"{ctx['username']}@{ctx['platform']}",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self._save_mappings(mappings)
        
        return {
            'user_key': user_key,
            'username': ctx['username'],
            'platform': ctx['platform'],
            'branch': branch_name,
            'worktree': str(worktree_path),
            'label': label or f"{ctx['username']}@{ctx['platform']}"
        }
    
    def _create_git_worktree(self, repo_path: Path, branch: str, worktree_path: Path):
        """创建 Git worktree"""
        import subprocess
        
        # 检查分支是否存在
        result = subprocess.run(
            ['git', '-C', str(repo_path), 'branch', '--list', branch],
            capture_output=True, text=True
        )
        
        # 创建分支（如果不存在）
        if branch not in result.stdout:
            subprocess.run(
                ['git', '-C', str(repo_path), 'branch', branch],
                capture_output=True
            )
        
        # 创建 worktree（如果不存在）
        if not worktree_path.exists():
            subprocess.run(
                ['git', '-C', str(repo_path), 'worktree', 'add', 
                 str(worktree_path), branch],
                capture_output=True
            )
    
    def get_my_binding(self) -> dict:
        """获取当前用户的绑定"""
        ctx = self.get_user_context()
        mappings = self._load_mappings()
        return mappings.get(ctx['user_key'])
    
    def get_all_local_bindings(self, repo_path: str = None) -> list:
        """
        获取本机所有用户的绑定
        可选按仓库过滤
        """
        mappings = self._load_mappings()
        results = []
        
        for user_key, info in mappings.items():
            if repo_path is None or info['repo_path'] == str(Path(repo_path).resolve()):
                results.append({
                    'user_key': user_key,
                    'username': info['username'],
                    'platform': info['platform'],
                    'label': info.get('label', user_key),
                    'branch': info['branch_name'],
                    'worktree': info['worktree_path'],
                    'repo': info['repo_path'],
                    'updated_at': info.get('updated_at', '未知')
                })
        
        return sorted(results, key=lambda x: x['updated_at'], reverse=True)
    
    def get_cd_command(self) -> str:
        """获取进入当前用户 worktree 的命令"""
        binding = self.get_my_binding()
        if binding:
            return f"cd '{binding['worktree_path']}'"
        return None
    
    def switch_branch(self, new_branch: str) -> dict:
        """切换到新分支（创建新 worktree）"""
        binding = self.get_my_binding()
        if not binding:
            raise ValueError("当前用户未绑定 worktree")
        
        return self.bind_worktree(
            binding['repo_path'], 
            new_branch,
            binding.get('label')
        )
    
    def unbind(self) -> bool:
        """解除当前用户的绑定"""
        ctx = self.get_user_context()
        mappings = self._load_mappings()
        
        if ctx['user_key'] in mappings:
            del mappings[ctx['user_key']]
            self._save_mappings(mappings)
            return True
        return False


def main():
    """本地团队版 CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Local Team Worktree Manager - 本地多用户多平台支持',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
本地团队特性:
  - 支持同一机器上的多用户/多平台
  - 每个用户有独立的 worktree 路径
  - 绑定信息存储在 ~/.openclaw/（本地）
  - Git 远程协作由 Git 处理，我们只管理本地 worktree

示例:
  # 用户 A（飞书）绑定
  worktree-session-local bind ~/project feature-auth --label "Alice飞书"
  
  # 用户 B（Discord，同一机器不同账号）绑定  
  worktree-session-local bind ~/project feature-payment --label "BobDiscord"
  
  # 查看本机所有绑定
  worktree-session-local list
  
  # 查看当前用户的绑定
  worktree-session-local info
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # bind
    bind_parser = subparsers.add_parser('bind', help='绑定 worktree')
    bind_parser.add_argument('repo_path', help='仓库路径')
    bind_parser.add_argument('branch_name', help='分支名')
    bind_parser.add_argument('--label', '-l', help='用户标签')
    
    # info
    info_parser = subparsers.add_parser('info', help='查看当前用户绑定')
    
    # list
    list_parser = subparsers.add_parser('list', help='查看本机所有绑定')
    list_parser.add_argument('--repo', '-r', help='按仓库过滤')
    
    # switch
    switch_parser = subparsers.add_parser('switch', help='切换分支')
    switch_parser.add_argument('new_branch', help='新分支名')
    
    # unbind
    unbind_parser = subparsers.add_parser('unbind', help='解除绑定')
    
    # cd
    cd_parser = subparsers.add_parser('cd', help='获取 cd 命令')
    
    args = parser.parse_args()
    
    manager = LocalTeamManager()
    
    if args.command == 'bind':
        result = manager.bind_worktree(args.repo_path, args.branch_name, args.label)
        print(f"✅ 绑定成功")
        print(f"   用户: {result['username']}")
        print(f"   平台: {result['platform']}")
        print(f"   分支: {result['branch']}")
        print(f"   Worktree: {result['worktree']}")
        if args.label:
            print(f"   标签: {args.label}")
    
    elif args.command == 'info':
        binding = manager.get_my_binding()
        if binding:
            ctx = manager.get_user_context()
            print(f"📋 当前用户绑定")
            print(f"   用户: {binding['username']}")
            print(f"   平台: {binding['platform']}")
            print(f"   标签: {binding.get('label', '无')}")
            print(f"   分支: {binding['branch_name']}")
            print(f"   Worktree: {binding['worktree_path']}")
            print(f"   仓库: {binding['repo_path']}")
        else:
            print("⚠️ 当前用户未绑定 worktree")
            print(f"   当前上下文: {manager.get_user_context()['user_key']}")
    
    elif args.command == 'list':
        bindings = manager.get_all_local_bindings(args.repo)
        if bindings:
            print(f"📋 本机所有绑定（共 {len(bindings)} 个）")
            current_ctx = manager.get_user_context()
            for b in bindings:
                is_me = b['user_key'] == current_ctx['user_key']
                marker = "👉" if is_me else "  "
                print(f"\n{marker} {b['label']}")
                print(f"     用户: {b['username']} | 平台: {b['platform']}")
                print(f"     分支: {b['branch']}")
                print(f"     路径: {b['worktree']}")
        else:
            print("⚠️ 本机没有绑定记录")
    
    elif args.command == 'switch':
        result = manager.switch_branch(args.new_branch)
        print(f"✅ 切换成功")
        print(f"   新分支: {result['branch']}")
        print(f"   新路径: {result['worktree']}")
    
    elif args.command == 'unbind':
        if manager.unbind():
            print("✅ 解除绑定成功")
        else:
            print("⚠️ 未找到绑定")
    
    elif args.command == 'cd':
        cmd = manager.get_cd_command()
        if cmd:
            print(cmd)
        else:
            print("# 未找到绑定", file=sys.stderr)
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
