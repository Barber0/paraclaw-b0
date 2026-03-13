#!/usr/bin/env python3
"""
Git Worktree Session Manager - CLI 入口
Author: Zilin Fang
"""

import sys
import argparse
from worktree_session import WorktreeSessionManager


def main():
    parser = argparse.ArgumentParser(
        description='Git Worktree Session Manager - 让不同群聊各自工作在独立分支',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
快速使用:
  worktree-session bind ~/myapp feature-xxx    # 绑定当前群聊到分支
  worktree-session info                          # 查看当前绑定
  worktree-session switch feature-yyy           # 切换到新分支
  worktree-session list                          # 列出所有绑定
  worktree-session unbind                        # 解除绑定

环境变量:
  OPENCLAW_SESSION_ID    Session ID（优先级最高）
  SESSION_KEY            Session ID
  CHAT_ID                Session ID
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # bind 命令
    bind_parser = subparsers.add_parser('bind', help='绑定 session 到 worktree')
    bind_parser.add_argument('repo_path', nargs='?', help='仓库路径（可选，默认当前目录）')
    bind_parser.add_argument('branch_name', help='分支名称')
    bind_parser.add_argument('--session', '-s', help='Session ID（默认自动获取）')
    bind_parser.add_argument('--worktree', '-w', help='Worktree 路径（默认自动创建）')
    
    # info 命令
    info_parser = subparsers.add_parser('info', help='查看当前 session 的绑定信息')
    info_parser.add_argument('--session', '-s', help='Session ID（默认当前 session）')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有绑定')
    
    # unbind 命令
    unbind_parser = subparsers.add_parser('unbind', help='解除绑定')
    unbind_parser.add_argument('--session', '-s', help='Session ID（默认当前 session）')
    
    # switch 命令
    switch_parser = subparsers.add_parser('switch', help='切换到新分支')
    switch_parser.add_argument('new_branch', help='新分支名称')
    switch_parser.add_argument('--session', '-s', help='Session ID（默认当前 session）')
    
    # cd 命令
    cd_parser = subparsers.add_parser('cd', help='获取 cd 命令')
    cd_parser.add_argument('--session', '-s', help='Session ID（默认当前 session）')
    
    args = parser.parse_args()
    
    manager = WorktreeSessionManager()
    
    if args.command == 'bind':
        repo_path = args.repo_path if args.repo_path else '.'
        session_id = args.session or manager.get_session_id()
        try:
            info = manager.bind_session_to_worktree(
                session_id, repo_path, args.branch_name, args.worktree
            )
            print(f"✅ 绑定成功")
            print(f"  🌿 分支: {info['branch_name']}")
            print(f"  📁 Worktree: {info['worktree_path']}")
            print(f"  📂 原仓库: {info['repo_path']}")
            print(f"\n💡 提示: 使用 'worktree-session cd' 获取进入目录的命令")
        except Exception as e:
            print(f"❌ 绑定失败: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'info':
        session_id = args.session or manager.get_session_id()
        info = manager.get_session_worktree(session_id)
        if info:
            print(f"📋 当前 Session 绑定信息")
            print(f"  🌿 分支: {info['branch_name']}")
            print(f"  📁 Worktree: {info['worktree_path']}")
            print(f"  📂 原仓库: {info['repo_path']}")
            print(f"  ⏰ 创建时间: {info.get('created_at', '未知')}")
        else:
            print(f"⚠️ 当前 Session 未绑定 worktree")
            print("💡 使用: worktree-session bind <repo> <branch> 进行绑定")
    
    elif args.command == 'list':
        mappings = manager.list_all_bindings()
        if mappings:
            print(f"📋 所有 Session 绑定关系（共 {len(mappings)} 个）")
            for i, (session_id, info) in enumerate(mappings.items(), 1):
                session_display = session_id[:40] + "..." if len(session_id) > 40 else session_id
                print(f"\n  {i}. Session: {session_display}")
                print(f"     🌿 分支: {info['branch_name']}")
                print(f"     📁 Worktree: {info['worktree_path']}")
        else:
            print("⚠️ 当前没有绑定的 Session")
    
    elif args.command == 'unbind':
        session_id = args.session or manager.get_session_id()
        if manager.unbind_session(session_id):
            print("✅ 解除绑定成功")
            print("💡 注意: worktree 目录未删除，如需清理请手动删除")
        else:
            print(f"⚠️ Session 未找到绑定")
    
    elif args.command == 'switch':
        session_id = args.session or manager.get_session_id()
        info = manager.switch_branch(session_id, args.new_branch)
        if info:
            print(f"✅ 切换成功")
            print(f"  🌿 新分支: {info['branch_name']}")
            print(f"  📁 新 Worktree: {info['worktree_path']}")
        else:
            print("❌ 切换失败，当前 session 可能未绑定", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'cd':
        session_id = args.session or manager.get_session_id()
        cmd = manager.get_cd_command(session_id)
        if cmd:
            print(cmd)
        else:
            print("# 当前 Session 未绑定 worktree", file=sys.stderr)
            print("# 使用: worktree-session bind <repo> <branch>", file=sys.stderr)
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
