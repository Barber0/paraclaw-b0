#!/usr/bin/env python3
"""
增强型 Worktree Session Manager - 支持会话标签持久化
解决重启后 Session ID 变化的问题
"""

import os
import sys
import json
import hashlib
from pathlib import Path


class PersistentWorktreeManager:
    """
    增强型 Worktree 管理器，支持多种方式识别持久化会话
    
    识别优先级：
    1. 显式 session_id 参数
    2. OPENCLAW_SESSION_ID（稳定）
    3. CHAT_ID（飞书/Discord群聊ID，永久稳定）
    4. 会话标签（用户自定义）
    5. 项目+分支组合的 hash（备用方案）
    """
    
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.openclaw")
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "worktree-sessions.json"
        self.label_file = self.config_dir / "worktree-session-labels.json"
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
    
    def _load_labels(self) -> dict:
        """加载用户自定义的标签映射"""
        if not self.label_file.exists():
            return {}
        try:
            with open(self.label_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_labels(self, labels: dict):
        with open(self.label_file, 'w', encoding='utf-8') as f:
            json.dump(labels, f, indent=2, ensure_ascii=False)
    
    def get_session_id(self) -> str:
        """
        获取当前 Session ID，支持多种来源
        """
        # 优先级1：OPENCLAW_SESSION_ID（推荐，OpenClaw原生）
        if 'OPENCLAW_SESSION_ID' in os.environ:
            return os.environ['OPENCLAW_SESSION_ID']
        
        # 优先级2：CHAT_ID（飞书/Discord等平台）
        if 'CHAT_ID' in os.environ:
            return os.environ['CHAT_ID']
        
        # 优先级3：SESSION_KEY
        if 'SESSION_KEY' in os.environ:
            return os.environ['SESSION_KEY']
        
        # 备用：基于工作目录生成稳定ID
        cwd = os.getcwd()
        return f"cwd_{hashlib.md5(cwd.encode()).hexdigest()[:16]}"
    
    def get_session_label(self, session_id: str) -> str:
        """获取会话的人类可读标签"""
        labels = self._load_labels()
        return labels.get(session_id, session_id[:20] + "...")
    
    def set_session_label(self, session_id: str, label: str):
        """为会话设置标签，方便识别"""
        labels = self._load_labels()
        labels[session_id] = label
        self._save_labels(labels)
    
    def find_binding_by_label(self, label: str) -> tuple:
        """通过标签查找绑定"""
        labels = self._load_labels()
        mappings = self._load_mappings()
        
        for session_id, session_label in labels.items():
            if session_label == label or label in session_label:
                if session_id in mappings:
                    return session_id, mappings[session_id]
        return None, None
    
    def get_all_bindings_with_labels(self) -> list:
        """获取所有绑定及其标签"""
        mappings = self._load_mappings()
        labels = self._load_labels()
        
        result = []
        for session_id, info in mappings.items():
            result.append({
                'session_id': session_id,
                'label': labels.get(session_id, session_id[:20] + "..."),
                'repo_path': info['repo_path'],
                'branch_name': info['branch_name'],
                'worktree_path': info['worktree_path'],
                'created_at': info.get('created_at', '未知')
            })
        return result
    
    def bind_session_to_worktree(self, session_id: str, repo_path: str, 
                                 branch_name: str, worktree_path: str = None,
                                 label: str = None) -> dict:
        """绑定 Session 到 Worktree，可选添加标签"""
        from worktree_session.manager import WorktreeSessionManager
        
        # 使用基础管理器执行绑定
        base_manager = WorktreeSessionManager(self.config_dir)
        info = base_manager.bind_session_to_worktree(
            session_id, repo_path, branch_name, worktree_path
        )
        
        # 如果提供了标签，保存标签
        if label:
            self.set_session_label(session_id, label)
        
        return info


def main():
    """增强型 CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Persistent Worktree Session Manager - 重启也能记住分支',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
持久化特性:
  - 绑定信息保存到 ~/.openclaw/worktree-sessions.json
  - 支持为会话设置人类可读标签
  - 通过标签查找绑定，应对 Session ID 变化

标签管理:
  worktree-session-p label "我的项目"           # 为当前会话设置标签
  worktree-session-p find "我的项目"            # 通过标签查找绑定
  worktree-session-p list --with-labels         # 显示所有绑定及标签
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # label 命令
    label_parser = subparsers.add_parser('label', help='为当前会话设置标签')
    label_parser.add_argument('label_text', help='标签文本')
    label_parser.add_argument('--session', '-s', help='Session ID')
    
    # find 命令
    find_parser = subparsers.add_parser('find', help='通过标签查找绑定')
    find_parser.add_argument('label_text', help='要查找的标签')
    
    # list 命令（增强版）
    list_parser = subparsers.add_parser('list', help='列出所有绑定')
    list_parser.add_argument('--with-labels', '-l', action='store_true', 
                            help='显示标签')
    
    args = parser.parse_args()
    
    manager = PersistentWorktreeManager()
    
    if args.command == 'label':
        session_id = args.session or manager.get_session_id()
        manager.set_session_label(session_id, args.label_text)
        print(f"✅ 已为 Session 设置标签: {args.label_text}")
        print(f"   Session ID: {session_id[:40]}...")
    
    elif args.command == 'find':
        session_id, info = manager.find_binding_by_label(args.label_text)
        if info:
            print(f"✅ 找到绑定:")
            print(f"   标签: {args.label_text}")
            print(f"   分支: {info['branch_name']}")
            print(f"   Worktree: {info['worktree_path']}")
        else:
            print(f"❌ 未找到标签为 '{args.label_text}' 的绑定")
    
    elif args.command == 'list' and args.with_labels:
        bindings = manager.get_all_bindings_with_labels()
        if bindings:
            print(f"📋 所有绑定关系（共 {len(bindings)} 个）")
            for i, b in enumerate(bindings, 1):
                print(f"\n  {i}. {b['label']}")
                print(f"     🌿 分支: {b['branch_name']}")
                print(f"     📁 Worktree: {b['worktree_path']}")
        else:
            print("⚠️ 当前没有绑定的 Session")
    
    else:
        # 其他命令使用基础管理器
        from worktree_session.cli import main as base_main
        base_main()


if __name__ == '__main__':
    main()
