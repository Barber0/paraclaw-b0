#!/usr/bin/env python3
"""
Worktree Session Manager - 核心实现
Author: Zilin Fang
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path


class WorktreeSessionManager:
    """管理 Session 与 Git Worktree 的绑定关系"""
    
    def __init__(self, config_dir=None):
        """初始化管理器
        
        Args:
            config_dir: 配置目录，默认为 ~/.openclaw
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.openclaw")
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "worktree-sessions.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_mappings(self) -> dict:
        """加载所有 Session 到 Worktree 的映射"""
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_mappings(self, mappings: dict):
        """保存映射关系到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
    
    def get_session_id(self) -> str:
        """获取当前 Session ID
        
        按优先级尝试以下环境变量：
        1. OPENCLAW_SESSION_ID
        2. SESSION_KEY
        3. CHAT_ID
        4. 默认值: default
        """
        for env_var in ['OPENCLAW_SESSION_ID', 'SESSION_KEY', 'CHAT_ID']:
            if env_var in os.environ:
                return os.environ[env_var]
        return "default"
    
    def _get_repo_name(self, repo_path: str) -> str:
        """从仓库路径获取仓库名称"""
        return Path(repo_path).name
    
    def _get_worktree_base_path(self, repo_path: str) -> Path:
        """获取 worktree 的基础路径"""
        repo_path = Path(repo_path).resolve()
        return repo_path.parent / f"{repo_path.name}-worktrees"
    
    def _run_git(self, repo_path: str, *args) -> tuple:
        """在指定仓库运行 git 命令"""
        cmd = ['git', '-C', repo_path] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    
    def _branch_exists(self, repo_path: str, branch_name: str) -> bool:
        """检查分支是否存在"""
        code, stdout, _ = self._run_git(repo_path, 'branch', '--list', branch_name)
        return code == 0 and branch_name in stdout
    
    def _worktree_exists(self, repo_path: str, worktree_path: str) -> bool:
        """检查 worktree 是否已存在"""
        code, stdout, _ = self._run_git(repo_path, 'worktree', 'list')
        if code != 0:
            return False
        return worktree_path in stdout
    
    def bind_session_to_worktree(self, session_id: str, repo_path: str, 
                                 branch_name: str, worktree_path: str = None) -> dict:
        """绑定 Session 到 Worktree
        
        Args:
            session_id: 会话 ID
            repo_path: 仓库路径
            branch_name: 分支名称
            worktree_path: 可选，指定 worktree 路径
            
        Returns:
            绑定信息字典
        """
        repo_path = Path(repo_path).resolve()
        
        if not (repo_path / ".git").exists():
            raise ValueError(f"路径不是有效的 Git 仓库: {repo_path}")
        
        # 确定 worktree 路径
        if worktree_path is None:
            worktree_base = self._get_worktree_base_path(repo_path)
            worktree_path = worktree_base / branch_name
        else:
            worktree_path = Path(worktree_path).resolve()
        
        worktree_path_str = str(worktree_path)
        
        # 创建分支（如果不存在）
        if not self._branch_exists(str(repo_path), branch_name):
            code, _, stderr = self._run_git(str(repo_path), 'branch', branch_name)
            if code != 0:
                raise RuntimeError(f"创建分支失败: {stderr}")
            print(f"[创建分支] {branch_name}")
        
        # 创建 worktree（如果不存在）
        if not self._worktree_exists(str(repo_path), worktree_path_str):
            code, _, stderr = self._run_git(
                str(repo_path), 'worktree', 'add', worktree_path_str, branch_name
            )
            if code != 0:
                raise RuntimeError(f"创建 worktree 失败: {stderr}")
            print(f"[创建 Worktree] {worktree_path}")
        else:
            print(f"[复用 Worktree] {worktree_path}")
        
        # 保存绑定关系
        mappings = self._load_mappings()
        mappings[session_id] = {
            'repo_path': str(repo_path),
            'branch_name': branch_name,
            'worktree_path': worktree_path_str,
            'created_at': datetime.now().isoformat()
        }
        self._save_mappings(mappings)
        
        return mappings[session_id]
    
    def get_session_worktree(self, session_id: str) -> dict:
        """获取 Session 绑定的 Worktree 信息"""
        mappings = self._load_mappings()
        return mappings.get(session_id)
    
    def list_all_bindings(self) -> dict:
        """列出所有绑定关系"""
        return self._load_mappings()
    
    def unbind_session(self, session_id: str) -> bool:
        """解除 Session 绑定
        
        注意：此方法只解除绑定关系，不会删除 worktree 目录
        """
        mappings = self._load_mappings()
        if session_id in mappings:
            del mappings[session_id]
            self._save_mappings(mappings)
            return True
        return False
    
    def switch_branch(self, session_id: str, new_branch: str) -> dict:
        """切换到新分支
        
        如果新分支没有 worktree，会自动创建
        """
        info = self.get_session_worktree(session_id)
        if not info:
            return None
        
        return self.bind_session_to_worktree(
            session_id, info['repo_path'], new_branch
        )
    
    def get_cd_command(self, session_id: str) -> str:
        """获取进入 worktree 的 cd 命令"""
        info = self.get_session_worktree(session_id)
        if info and os.path.exists(info['worktree_path']):
            return f"cd '{info['worktree_path']}'"
        return None
