#!/usr/bin/env python3
"""
para-branch - Git Worktree Session Manager
统一的简单接口：只关心绑定和切换
"""

import os
import sys
import json
import getpass
import subprocess
from pathlib import Path
from datetime import datetime


class WorktreeManager:
    """统一的管理器，自动处理个人/团队场景"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.openclaw'
        self.config_file = self.config_dir / 'worktree-sessions.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_context(self):
        """获取当前上下文：用户 + 平台 + 会话"""
        username = getpass.getuser()
        
        # 检测平台
        if 'FEISHU_CHAT_ID' in os.environ or 'feishu' in os.environ.get('OPENCLAW_CHANNEL', '').lower():
            platform = 'feishu'
        elif 'DISCORD_GUILD_ID' in os.environ:
            platform = 'discord'
        elif 'SLACK_CHANNEL' in os.environ:
            platform = 'slack'
        else:
            platform = os.environ.get('OPENCLAW_PLATFORM', 'local')
        
        # 会话ID优先级
        session_id = os.environ.get('CHAT_ID') or \
                     os.environ.get('OPENCLAW_SESSION_ID') or \
                     os.environ.get('SESSION_KEY') or \
                     f"{username}_{platform}"
        
        return {
            'username': username,
            'platform': platform,
            'session_id': session_id,
            'key': f"{username}:{platform}:{session_id[:20]}"
        }
    
    def _load(self):
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save(self, data):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def bind(self, repo_path, branch, label=None):
        """绑定当前会话到分支"""
        ctx = self._get_context()
        repo = Path(repo_path).resolve()
        
        if not (repo / '.git').exists():
            raise ValueError(f"不是Git仓库: {repo}")
        
        # 创建worktree路径
        base = repo.parent / f"{repo.name}-worktrees"
        short_user = ctx['username'][:8]
        worktree = base / f"{short_user}_{branch}"
        
        # 创建git worktree
        self._git_worktree(repo, branch, worktree)
        
        # 保存绑定
        data = self._load()
        data[ctx['key']] = {
            'username': ctx['username'],
            'platform': ctx['platform'],
            'repo': str(repo),
            'branch': branch,
            'worktree': str(worktree),
            'label': label or f"{ctx['username']}@{ctx['platform']}",
            'updated': datetime.now().isoformat()
        }
        self._save(data)
        
        return {
            'branch': branch,
            'worktree': str(worktree),
            'label': label or ctx['username']
        }
    
    def _git_worktree(self, repo, branch, worktree):
        """创建git worktree"""
        # 检查分支
        result = subprocess.run(
            ['git', '-C', str(repo), 'branch', '--list', branch],
            capture_output=True, text=True
        )
        # 创建分支（如果不存在）
        if branch not in result.stdout:
            subprocess.run(['git', '-C', str(repo), 'branch', branch], 
                          capture_output=True)
        # 创建worktree
        if not worktree.exists():
            subprocess.run(['git', '-C', str(repo), 'worktree', 'add',
                          str(worktree), branch], capture_output=True)
    
    def get_current(self):
        """获取当前会话的绑定"""
        ctx = self._get_context()
        data = self._load()
        return data.get(ctx['key'])
    
    def list_all(self, repo=None):
        """列出所有绑定"""
        data = self._load()
        ctx = self._get_context()
        results = []
        
        for key, info in data.items():
            if repo is None or info['repo'] == str(Path(repo).resolve()):
                is_me = key == ctx['key']
                results.append({
                    'is_me': is_me,
                    'label': info.get('label', key),
                    'user': info['username'],
                    'platform': info['platform'],
                    'branch': info['branch'],
                    'worktree': info['worktree'],
                    'updated': info.get('updated', '')
                })
        
        return sorted(results, key=lambda x: x['updated'], reverse=True)
    
    def switch(self, new_branch):
        """切换到新分支"""
        current = self.get_current()
        if not current:
            raise ValueError("还没有绑定，先执行 bind")
        return self.bind(current['repo'], new_branch, current.get('label'))
    
    def unbind(self):
        """解除当前绑定"""
        ctx = self._get_context()
        data = self._load()
        if ctx['key'] in data:
            del data[ctx['key']]
            self._save(data)
            return True
        return False
    
    def cd_cmd(self):
        """获取进入worktree的命令"""
        current = self.get_current()
        if current:
            return f"cd '{current['worktree']}'"
        return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='para-branch: 绑定聊天会话到Git分支',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
简单用法:
  绑定:   para-branch bind ~/myproject feature-xxx
  查看:   para-branch info
  切换:   para-branch switch feature-yyy
  列出:   para-branch list
  进入:   cd $(para-branch cd)

多用户支持:
  不同用户/平台自动隔离，list可以看到所有人的绑定
        """
    )
    
    sub = parser.add_subparsers(dest='cmd', help='命令')
    
    # bind
    p_bind = sub.add_parser('bind', help='绑定到分支')
    p_bind.add_argument('repo', help='仓库路径')
    p_bind.add_argument('branch', help='分支名')
    p_bind.add_argument('--label', '-l', help='标签（可选）')
    
    # info
    sub.add_parser('info', help='查看当前绑定')
    
    # switch
    p_switch = sub.add_parser('switch', help='切换到新分支')
    p_switch.add_argument('branch', help='新分支名')
    
    # list
    p_list = sub.add_parser('list', help='列出所有绑定')
    p_list.add_argument('--repo', '-r', help='过滤仓库')
    
    # unbind
    sub.add_parser('unbind', help='解除绑定')
    
    # cd
    sub.add_parser('cd', help='输出cd命令')
    
    args = parser.parse_args()
    m = WorktreeManager()
    
    try:
        if args.cmd == 'bind':
            r = m.bind(args.repo, args.branch, args.label)
            print(f"✅ 绑定: {r['branch']}")
            print(f"   路径: {r['worktree']}")
            if args.label:
                print(f"   标签: {args.label}")
        
        elif args.cmd == 'info':
            c = m.get_current()
            if c:
                print(f"📍 分支: {c['branch']}")
                print(f"   仓库: {c['repo']}")
                print(f"   路径: {c['worktree']}")
                print(f"   身份: {c.get('label', '未知')}")
            else:
                print("⚠️  未绑定")
        
        elif args.cmd == 'switch':
            r = m.switch(args.branch)
            print(f"✅ 切换: {r['branch']}")
            print(f"   路径: {r['worktree']}")
        
        elif args.cmd == 'list':
            items = m.list_all(args.repo)
            if items:
                print(f"📋 共 {len(items)} 个绑定")
                for item in items:
                    me = "👉" if item['is_me'] else "  "
                    print(f"\n{me} {item['label']}")
                    print(f"     {item['branch']} | {item['platform']}")
            else:
                print("暂无绑定")
        
        elif args.cmd == 'unbind':
            if m.unbind():
                print("✅ 已解除")
            else:
                print("未绑定")
        
        elif args.cmd == 'cd':
            cmd = m.cd_cmd()
            if cmd:
                print(cmd)
            else:
                print("# 未绑定", file=sys.stderr)
                sys.exit(1)
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
