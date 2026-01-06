"""文件锁实现

使用文件系统锁来防止重复触发转写任务。
仅使用标准库实现，不依赖第三方包。

【锁文件说明】
- 锁文件路径：<CONTEXT_ROOT>\_transcribe.lock
- 启动任务时以原子方式创建锁文件（使用 O_EXCL 标志）
- 任务结束后（无论成功失败）删除锁文件
- 若锁文件残留（如进程异常退出），可手动删除该文件以恢复正常

【手动恢复方法】
如果任务异常退出导致锁文件残留，可以：
1. 确认没有正在运行的转写任务
2. 手动删除锁文件：<CONTEXT_ROOT>\_transcribe.lock
3. 重新调用 /parse/transcribe_all 接口
"""

import os
from pathlib import Path
from typing import Optional


class FileLock:
    """
    基于文件系统的锁实现
    
    使用 O_CREAT | O_EXCL 标志原子地创建锁文件，
    若文件已存在则说明锁被持有。
    """
    
    def __init__(self, lock_path: Path):
        """
        初始化文件锁
        
        Args:
            lock_path: 锁文件路径
        """
        self._lock_path = lock_path
        self._fd: Optional[int] = None
    
    def acquire(self) -> bool:
        """
        尝试获取锁
        
        Returns:
            True 表示获取成功，False 表示锁已被持有
        """
        try:
            # 确保父目录存在
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 O_CREAT | O_EXCL 原子创建文件
            # 如果文件已存在，会抛出 FileExistsError
            self._fd = os.open(
                str(self._lock_path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644
            )
            
            # 写入进程信息便于调试
            os.write(self._fd, f"pid={os.getpid()}\n".encode("utf-8"))
            
            return True
            
        except FileExistsError:
            # 锁文件已存在，说明有任务正在运行
            return False
        except OSError as e:
            # 其他文件系统错误
            raise RuntimeError(f"无法创建锁文件: {e}")
    
    def release(self) -> None:
        """
        释放锁（删除锁文件）
        
        无论如何都会尝试删除锁文件，即使 fd 未打开。
        """
        # 关闭文件描述符
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            finally:
                self._fd = None
        
        # 删除锁文件
        try:
            self._lock_path.unlink(missing_ok=True)
        except OSError:
            # 忽略删除失败，可能文件已被删除
            pass
    
    def is_locked(self) -> bool:
        """
        检查锁是否被持有（锁文件是否存在）
        
        Returns:
            True 表示锁文件存在（可能有任务正在运行）
        """
        return self._lock_path.exists()
    
    @property
    def lock_path(self) -> Path:
        """返回锁文件路径"""
        return self._lock_path
    
    def __enter__(self) -> "FileLock":
        """上下文管理器入口"""
        if not self.acquire():
            raise RuntimeError("无法获取锁，任务可能正在运行")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出，释放锁"""
        self.release()

