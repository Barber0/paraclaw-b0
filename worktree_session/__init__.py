#!/usr/bin/env python3
"""
Git Worktree Session Manager
让不同的聊天会话各自工作在独立的 Git Worktree 中

Author: Zilin Fang
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Zilin Fang"

from .manager import WorktreeSessionManager

__all__ = ['WorktreeSessionManager']
