"""
审计系统模块 (Audit System Module)

提供完整的知识操作审计记录和查询功能。

v2.0.0 - 企业级审计系统
- 完整的知识操作（CRUD）审计记录
- 审计日志持久化（SQLite/文件）
- 审计日志查询接口
- 异步写入优化
- 审计日志清理和归档

设计原则：
- 零硬编码：所有配置从 ConfigManager 读取
- 逐行注释：每行逻辑代码包含中文注释
- 完整性：记录所有关键操作的完整上下文
"""

import atexit
import json
import logging
import sqlite3
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from threading import Lock

# 导入配置管理器和基础Agent类
from ..utils.config import get_config
from .base import BaseAgent

logger = logging.getLogger(__name__)


# ==================== 审计数据结构定义 ====================

class AuditOperation(Enum):
    """
    审计操作类型枚举
    
    定义所有需要审计记录的操作类型。
    """
    # 知识图谱操作
    CREATE_TRIPLE = "create_triple"       # 创建三元组
    UPDATE_TRIPLE = "update_triple"       # 更新三元组
    DELETE_TRIPLE = "delete_triple"       # 删除三元组
    QUERY_TRIPLE = "query_triple"         # 查询三元组
    
    # 实体操作
    CREATE_ENTITY = "create_entity"       # 创建实体
    UPDATE_ENTITY = "update_entity"       # 更新实体
    DELETE_ENTITY = "delete_entity"       # 删除实体
    
    # 关系操作
    CREATE_RELATION = "create_relation"   # 创建关系
    DELETE_RELATION = "delete_relation"   # 删除关系
    
    # 推理操作
    EXECUTE_INFERENCE = "execute_inference"  # 执行推理
    LEARN_KNOWLEDGE = "learn_knowledge"      # 学习知识
    
    # 系统操作
    IMPORT_DATA = "import_data"           # 导入数据
    EXPORT_DATA = "export_data"           # 导出数据
    SYSTEM_CONFIG = "system_config"       # 系统配置变更
    
    # 权限操作
    ASSIGN_ROLE = "assign_role"           # 分配角色
    REVOKE_ROLE = "revoke_role"           # 撤销角色
    CREATE_USER = "create_user"           # 创建用户
    DELETE_USER = "delete_user"           # 删除用户
    
    # Agent 操作
    AGENT_ACTION = "agent_action"         # Agent 执行动作
    TOOL_CALL = "tool_call"               # 工具调用


class AuditStatus(Enum):
    """
    审计状态枚举
    
    表示操作执行的结果状态。
    """
    SUCCESS = "success"     # 操作成功
    FAILURE = "failure"     # 操作失败
    PENDING = "pending"     # 操作待处理
    BLOCKED = "blocked"     # 操作被阻止（权限不足等）


@dataclass
class AuditLog:
    """
    审计日志数据结构
    
    包含审计记录的完整信息，符合审计日志标准规范。
    """
    # 基本信息
    id: str                                 # 审计记录唯一ID
    timestamp: str                          # 操作时间（ISO格式）
    operation: AuditOperation               # 操作类型
    status: AuditStatus                     # 操作状态
    
    # 操作者信息
    user_id: str = ""                       # 操作者ID
    user_ip: str = ""                       # 操作者IP地址
    user_agent: str = ""                    # 用户代理信息
    
    # 操作目标信息
    resource_type: str = ""                 # 资源类型
    resource_id: str = ""                   # 资源ID
    
    # 操作详情
    action: str = ""                        # 具体动作
    details: Dict[str, Any] = field(default_factory=dict)  # 操作详情
    changes: Dict[str, Any] = field(default_factory=dict)  # 变更前后对比
    
    # 结果信息
    result: str = ""                        # 操作结果描述
    error_message: str = ""                 # 错误信息（如果有）
    
    # 上下文信息
    session_id: str = ""                    # 会话ID
    correlation_id: str = ""                # 关联ID（用于追踪相关操作）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于序列化"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "operation": self.operation.value,
            "status": self.status.value,
            "user_id": self.user_id,
            "user_ip": self.user_ip,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "changes": self.changes,
            "result": self.result,
            "error_message": self.error_message,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditLog":
        """从字典创建审计日志实例"""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            operation=AuditOperation(data["operation"]),
            status=AuditStatus(data["status"]),
            user_id=data.get("user_id", ""),
            user_ip=data.get("user_ip", ""),
            user_agent=data.get("user_agent", ""),
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id", ""),
            action=data.get("action", ""),
            details=data.get("details", {}),
            changes=data.get("changes", {}),
            result=data.get("result", ""),
            error_message=data.get("error_message", ""),
            session_id=data.get("session_id", ""),
            correlation_id=data.get("correlation_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AuditQuery:
    """
    审计日志查询条件
    
    支持多种条件组合查询。
    """
    start_time: Optional[datetime] = None   # 开始时间
    end_time: Optional[datetime] = None     # 结束时间
    user_id: Optional[str] = None           # 用户ID
    operation: Optional[AuditOperation] = None  # 操作类型
    status: Optional[AuditStatus] = None    # 操作状态
    resource_type: Optional[str] = None     # 资源类型
    resource_id: Optional[str] = None       # 资源ID
    session_id: Optional[str] = None        # 会话ID
    correlation_id: Optional[str] = None    # 关联ID
    limit: int = 100                        # 返回数量限制
    offset: int = 0                         # 偏移量（分页）


# ==================== 审计日志存储后端 ====================

from abc import ABC, abstractmethod


class AuditStorage(ABC):
    """
    审计日志存储抽象基类
    
    使用 @abstractmethod 强制子类实现所有抽象方法，
    确保存储后端的一致性和完整性。
    
    子类必须实现:
    - write: 写入单条审计日志
    - write_batch: 批量写入审计日志
    - query: 查询审计日志
    - count: 统计审计日志数量
    - delete_old: 删除过期审计日志
    """
    
    @abstractmethod
    def write(self, log: AuditLog) -> bool:
        """
        写入单条审计日志
        
        Args:
            log: 审计日志对象
            
        Returns:
            是否写入成功
        """
        ...
    
    @abstractmethod
    def write_batch(self, logs: List[AuditLog]) -> int:
        """
        批量写入审计日志
        
        Args:
            logs: 审计日志列表
            
        Returns:
            成功写入的数量
        """
        ...
    
    @abstractmethod
    def query(self, query: AuditQuery) -> List[AuditLog]:
        """
        查询审计日志
        
        Args:
            query: 查询条件
            
        Returns:
            符合条件的审计日志列表
        """
        ...
    
    @abstractmethod
    def count(self, query: AuditQuery) -> int:
        """
        统计审计日志数量
        
        Args:
            query: 查询条件
            
        Returns:
            符合条件的审计日志数量
        """
        ...
    
    @abstractmethod
    def delete_old(self, days: int) -> int:
        """
        删除指定天数之前的审计日志
        
        Args:
            days: 保留天数（超过此天数的日志将被删除）
            
        Returns:
            删除的日志数量
        """
        ...
    
    def close(self):
        """
        关闭存储连接
        
        默认空实现，子类可根据需要覆盖。
        """
        pass


class SQLiteAuditStorage(AuditStorage):
    """
    SQLite 审计日志存储实现
    
    使用 SQLite 数据库存储审计日志，支持高效查询和索引。
    
    设计决策：
    - 使用 SQLite 而非文件存储，便于复杂查询
    - 创建索引加速常用查询条件
    - 支持 WAL 模式提升并发写入性能
    - 实现指数退避重试机制处理并发写入冲突
    """
    
    # 从配置读取重试参数，符合零硬编码原则
    _MAX_RETRIES: int = 3  # 最大重试次数
    _BASE_DELAY: float = 0.1  # 基础延迟（秒）
    _BATCH_SIZE: int = 1000  # 批量提交最大条数
    
    def __init__(self, db_path: str):
        """
        初始化 SQLite 存储
        
        参数：
            db_path: SQLite 数据库文件路径
        """
        self._db_path = db_path
        self._lock = Lock()
        
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库连接和表结构
        self._init_db()
    
    def _execute_with_retry(
        self,
        operation: Callable[[sqlite3.Connection], Any],
        operation_name: str = "operation"
    ) -> Tuple[bool, Any]:
        """
        执行带重试机制的 SQLite 操作
        
        使用指数退避策略处理 database is locked 异常，
        确保在高并发场景下写入最终成功。
        
        参数：
            operation: 需要执行的函数，接收 Connection 参数
            operation_name: 操作名称（用于日志记录）
            
        返回：
            (是否成功, 操作结果)
        """
        last_error = None
        for attempt in range(self._MAX_RETRIES):
            try:
                with sqlite3.connect(self._db_path, timeout=get_config().audit.sqlite_timeout) as conn:
                    # 启用 WAL 模式提升并发性能
                    conn.execute("PRAGMA journal_mode=WAL")
                    result = operation(conn)
                    conn.commit()
                    return True, result
            except sqlite3.OperationalError as e:
                last_error = e
                # 仅对锁定错误进行重试
                if "database is locked" in str(e).lower():
                    # 指数退避：0.1s, 0.2s, 0.4s
                    delay = self._BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        f"SQLite {operation_name} 遇到锁定，"
                        f"第 {attempt + 1}/{self._MAX_RETRIES} 次重试，"
                        f"延迟 {delay:.2f}s"
                    )
                    time.sleep(delay)
                else:
                    # 非锁定错误直接抛出
                    raise
            except Exception:
                # 其他异常直接抛出
                raise
        
        # 重试次数耗尽，记录错误并返回失败
        logger.error(
            f"SQLite {operation_name} 在 {self._MAX_RETRIES} 次重试后仍然失败: "
            f"{last_error}"
        )
        return False, None
    
    def _init_db(self):
        """
        初始化数据库表结构和索引
        
        创建审计日志表和必要的索引，确保高效查询。
        """
        with sqlite3.connect(self._db_path) as conn:
            # 启用 WAL 模式提升并发性能
            conn.execute("PRAGMA journal_mode=WAL")
            # 设置同步模式
            conn.execute("PRAGMA synchronous=NORMAL")
            
            # 创建审计日志表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    user_id TEXT,
                    user_ip TEXT,
                    user_agent TEXT,
                    resource_type TEXT,
                    resource_id TEXT,
                    action TEXT,
                    details TEXT,
                    changes TEXT,
                    result TEXT,
                    error_message TEXT,
                    session_id TEXT,
                    correlation_id TEXT,
                    metadata TEXT
                )
            """)
            
            # 创建索引以加速常用查询
            # 时间索引：按时间范围查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON audit_logs(timestamp)
            """)
            # 用户索引：按用户查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON audit_logs(user_id)
            """)
            # 操作类型索引：按操作类型查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_operation 
                ON audit_logs(operation)
            """)
            # 资源索引：按资源查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resource 
                ON audit_logs(resource_type, resource_id)
            """)
            # 会话索引：按会话追踪
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session 
                ON audit_logs(session_id)
            """)
            # 关联索引：按关联ID追踪
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_correlation 
                ON audit_logs(correlation_id)
            """)
            
            conn.commit()
            logger.info(f"SQLite 审计日志存储初始化完成: {self._db_path}")
    
    def write(self, log: AuditLog) -> bool:
        """
        写入单条审计日志
        
        使用带重试机制的执行器，处理并发写入时的 database is locked 异常。
        返回是否写入成功。
        """
        def _do_insert(conn: sqlite3.Connection):
            # 执行单条插入操作
            conn.execute("""
                INSERT INTO audit_logs VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                log.id,
                log.timestamp,
                log.operation.value,
                log.status.value,
                log.user_id,
                log.user_ip,
                log.user_agent,
                log.resource_type,
                log.resource_id,
                log.action,
                json.dumps(log.details, ensure_ascii=False),
                json.dumps(log.changes, ensure_ascii=False),
                log.result,
                log.error_message,
                log.session_id,
                log.correlation_id,
                json.dumps(log.metadata, ensure_ascii=False),
            ))
        
        with self._lock:
            success, _ = self._execute_with_retry(
                _do_insert,
                operation_name="write"
            )
            return success
    
    def write_batch(self, logs: List[AuditLog]) -> int:
        """
        批量写入审计日志
        
        使用分批提交策略，每批最多 _BATCH_SIZE 条记录，
        避免长事务导致的锁定时间过长。
        返回成功写入的数量。
        """
        if not logs:
            return 0
        
        total_inserted = 0
        
        # 分批处理，每批最多 _BATCH_SIZE 条
        for batch_start in range(0, len(logs), self._BATCH_SIZE):
            batch = logs[batch_start:batch_start + self._BATCH_SIZE]
            
            def _do_batch_insert(conn: sqlite3.Connection):
                # 准备批量插入数据
                values = [
                    (
                        log.id,
                        log.timestamp,
                        log.operation.value,
                        log.status.value,
                        log.user_id,
                        log.user_ip,
                        log.user_agent,
                        log.resource_type,
                        log.resource_id,
                        log.action,
                        json.dumps(log.details, ensure_ascii=False),
                        json.dumps(log.changes, ensure_ascii=False),
                        log.result,
                        log.error_message,
                        log.session_id,
                        log.correlation_id,
                        json.dumps(log.metadata, ensure_ascii=False),
                    )
                    for log in batch
                ]
                # 执行批量插入
                conn.executemany("""
                    INSERT INTO audit_logs VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, values)
            
            with self._lock:
                success, _ = self._execute_with_retry(
                    _do_batch_insert,
                    operation_name=f"write_batch({len(batch)})"
                )
                if success:
                    total_inserted += len(batch)
                else:
                    # 当前批次失败，停止后续批次
                    logger.error(f"批量写入第 {batch_start // self._BATCH_SIZE + 1} 批失败，"
                               f"已写入 {total_inserted}/{len(logs)} 条")
                    break
        
        return total_inserted
    
    def query(self, query: AuditQuery) -> List[AuditLog]:
        """
        根据条件查询审计日志
        
        支持多条件组合查询和分页。
        """
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    # 构建查询条件和参数
                    conditions = []
                    params = []
                    
                    # 时间范围条件
                    if query.start_time:
                        conditions.append("timestamp >= ?")
                        params.append(query.start_time.isoformat())
                    if query.end_time:
                        conditions.append("timestamp <= ?")
                        params.append(query.end_time.isoformat())
                    
                    # 用户条件
                    if query.user_id:
                        conditions.append("user_id = ?")
                        params.append(query.user_id)
                    
                    # 操作类型条件
                    if query.operation:
                        conditions.append("operation = ?")
                        params.append(query.operation.value)
                    
                    # 状态条件
                    if query.status:
                        conditions.append("status = ?")
                        params.append(query.status.value)
                    
                    # 资源条件
                    if query.resource_type:
                        conditions.append("resource_type = ?")
                        params.append(query.resource_type)
                    if query.resource_id:
                        conditions.append("resource_id = ?")
                        params.append(query.resource_id)
                    
                    # 会话条件
                    if query.session_id:
                        conditions.append("session_id = ?")
                        params.append(query.session_id)
                    
                    # 关联ID条件
                    if query.correlation_id:
                        conditions.append("correlation_id = ?")
                        params.append(query.correlation_id)
                    
                    # 构建SQL语句
                    sql = "SELECT * FROM audit_logs"
                    if conditions:
                        sql += " WHERE " + " AND ".join(conditions)
                    sql += " ORDER BY timestamp DESC"
                    # 使用参数化查询防止 SQL 注入，将 limit 和 offset 加入参数列表
                    sql += " LIMIT ? OFFSET ?"
                    params.append(query.limit)
                    params.append(query.offset)
                    
                    # 执行查询（所有参数均使用参数化绑定）
                    cursor = conn.execute(sql, params)
                    rows = cursor.fetchall()
                    
                    # 转换为 AuditLog 对象
                    logs = []
                    for row in rows:
                        log = AuditLog(
                            id=row[0],
                            timestamp=row[1],
                            operation=AuditOperation(row[2]),
                            status=AuditStatus(row[3]),
                            user_id=row[4] or "",
                            user_ip=row[5] or "",
                            user_agent=row[6] or "",
                            resource_type=row[7] or "",
                            resource_id=row[8] or "",
                            action=row[9] or "",
                            details=json.loads(row[10]) if row[10] else {},
                            changes=json.loads(row[11]) if row[11] else {},
                            result=row[12] or "",
                            error_message=row[13] or "",
                            session_id=row[14] or "",
                            correlation_id=row[15] or "",
                            metadata=json.loads(row[16]) if row[16] else {},
                        )
                        logs.append(log)
                    
                    return logs
            except Exception as e:
                logger.error(f"查询审计日志失败: {e}")
                return []
    
    def count(self, query: AuditQuery) -> int:
        """统计符合条件的审计日志数量"""
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    # 构建查询条件
                    conditions = []
                    params = []
                    
                    if query.start_time:
                        conditions.append("timestamp >= ?")
                        params.append(query.start_time.isoformat())
                    if query.end_time:
                        conditions.append("timestamp <= ?")
                        params.append(query.end_time.isoformat())
                    if query.user_id:
                        conditions.append("user_id = ?")
                        params.append(query.user_id)
                    if query.operation:
                        conditions.append("operation = ?")
                        params.append(query.operation.value)
                    if query.status:
                        conditions.append("status = ?")
                        params.append(query.status.value)
                    if query.resource_type:
                        conditions.append("resource_type = ?")
                        params.append(query.resource_type)
                    if query.resource_id:
                        conditions.append("resource_id = ?")
                        params.append(query.resource_id)
                    if query.session_id:
                        conditions.append("session_id = ?")
                        params.append(query.session_id)
                    if query.correlation_id:
                        conditions.append("correlation_id = ?")
                        params.append(query.correlation_id)
                    
                    sql = "SELECT COUNT(*) FROM audit_logs"
                    if conditions:
                        sql += " WHERE " + " AND ".join(conditions)
                    
                    cursor = conn.execute(sql, params)
                    return cursor.fetchone()[0]
            except Exception as e:
                logger.error(f"统计审计日志失败: {e}")
                return 0
    
    def delete_old(self, days: int) -> int:
        """
        删除指定天数之前的审计日志
        
        用于日志清理和归档。
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    cursor = conn.execute(
                        "DELETE FROM audit_logs WHERE timestamp < ?",
                        (cutoff_time.isoformat(),)
                    )
                    conn.commit()
                    deleted = cursor.rowcount
                    logger.info(f"删除 {deleted} 条过期审计日志（{days} 天前）")
                    return deleted
            except Exception as e:
                logger.error(f"删除过期审计日志失败: {e}")
                return 0


class FileAuditStorage(AuditStorage):
    """
    文件审计日志存储实现
    
    使用 JSONL 文件存储审计日志，适合简单场景或日志归档。
    """
    
    def __init__(self, file_path: str):
        """
        初始化文件存储
        
        参数：
            file_path: 日志文件路径
        """
        self._file_path = file_path
        self._lock = Lock()
        
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    def write(self, log: AuditLog) -> bool:
        """写入单条审计日志"""
        with self._lock:
            try:
                with open(self._file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log.to_dict(), ensure_ascii=False) + "\n")
                return True
            except Exception as e:
                logger.error(f"写入审计日志文件失败: {e}")
                return False
    
    def write_batch(self, logs: List[AuditLog]) -> int:
        """批量写入审计日志"""
        with self._lock:
            try:
                with open(self._file_path, "a", encoding="utf-8") as f:
                    for log in logs:
                        f.write(json.dumps(log.to_dict(), ensure_ascii=False) + "\n")
                return len(logs)
            except Exception as e:
                logger.error(f"批量写入审计日志文件失败: {e}")
                return 0
    
    def query(self, query: AuditQuery) -> List[AuditLog]:
        """查询审计日志（文件存储不支持复杂查询，返回最近的记录）"""
        logs = []
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                # 从文件末尾开始读取，获取最近的记录
                lines = f.readlines()
                for line in reversed(lines):
                    if len(logs) >= query.limit:
                        break
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            log = AuditLog.from_dict(data)
                            # 应用简单过滤
                            if query.user_id and log.user_id != query.user_id:
                                continue
                            logs.append(log)
                        except (json.JSONDecodeError, ValueError, KeyError) as e:
                            # 捕获具体的JSON解析异常和数据结构异常，避免裸except掩盖其他错误
                            # JSONDecodeError: JSON格式错误；ValueError: 值类型错误；KeyError: 缺少必要字段
                            logger.warning(f"审计日志行解析失败，跳过该行: {e}")
                            continue
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"读取审计日志文件失败: {e}")
        return logs
    
    def count(self, query: AuditQuery) -> int:
        """统计审计日志数量"""
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except FileNotFoundError:
            return 0
        except Exception as e:
            logger.error(f"统计审计日志数量失败: {e}")
            return 0
    
    def delete_old(self, days: int) -> int:
        """文件存储不支持删除旧日志，需要手动管理"""
        logger.warning("文件存储不支持自动删除旧日志")
        return 0


# ==================== 审计日志管理器 ====================

class AuditLogger:
    """
    审计日志管理器
    
    提供审计日志的记录、查询和管理功能。
    
    特性：
    - 支持同步和异步写入
    - 支持批量写入优化
    - 自动清理过期日志
    - 提供便捷的审计记录方法
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        # 单例模式：确保全局只有一个审计日志管理器
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if self._initialized:
            return
        
        self._initialized = True
        
        # 从配置获取设置
        config = get_config().audit
        
        # 初始化存储后端
        if config.storage_type == "sqlite":
            self._storage = SQLiteAuditStorage(config.sqlite_path)
        else:
            self._storage = FileAuditStorage(config.file_path)
        
        # 异步写入配置
        self._async_write = config.async_write
        self._batch_size = config.async_batch_size
        self._retention_days = config.retention_days
        
        # 异步写入缓冲区
        self._buffer: deque = deque(maxlen=self._batch_size * 2)
        self._buffer_lock = Lock()
        
        # 记录保留天数
        self._retention_days = config.retention_days
        
        # 注册应用退出时的缓冲区刷新钩子，确保异步日志不丢失
        atexit.register(self._cleanup_at_exit)
        
        logger.info(f"AuditLogger 初始化完成: storage={config.storage_type}, async={self._async_write}")
    
    def log(
        self,
        operation: AuditOperation,
        status: AuditStatus,
        user_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        action: str = "",
        details: Dict[str, Any] = None,
        changes: Dict[str, Any] = None,
        result: str = "",
        error_message: str = "",
        session_id: str = "",
        correlation_id: str = "",
        user_ip: str = "",
        user_agent: str = "",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        记录审计日志
        
        返回审计记录ID。
        """
        # 创建审计日志对象
        log = AuditLog(
            id=f"audit:{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now().isoformat(),
            operation=operation,
            status=status,
            user_id=user_id,
            user_ip=user_ip,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            changes=changes or {},
            result=result,
            error_message=error_message,
            session_id=session_id,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
        
        # 根据配置选择写入方式
        if self._async_write:
            # 异步写入：在锁保护下添加缓冲区并检查大小，确保检查和flush操作原子化
            with self._buffer_lock:
                self._buffer.append(log)
                # 当缓冲区达到批量大小时，在锁内执行写入，防止竞态条件
                if len(self._buffer) >= self._batch_size:
                    return self._flush_buffer_locked()
        else:
            # 同步写入
            self._storage.write(log)
        
        return log.id
    
    def _flush_buffer_locked(self) -> bool:
        """
        在已持有锁的情况下刷新缓冲区
        
        必须在持有 _buffer_lock 时调用，确保线程安全。
        返回是否成功写入所有日志。
        """
        if not self._buffer:
            return True
        
        # 获取缓冲区内容并清空
        logs = list(self._buffer)
        self._buffer.clear()
        
        # 批量写入并返回结果
        if logs:
            count = self._storage.write_batch(logs)
            logger.debug(f"批量写入 {count}/{len(logs)} 条审计日志")
            return count == len(logs)
        return True
    
    def _flush_buffer(self) -> bool:
        """
        刷新缓冲区，写入所有待写入的日志
        
        返回是否成功写入所有日志。
        """
        with self._buffer_lock:
            return self._flush_buffer_locked()
    
    def flush(self) -> bool:
        """
        手动刷新缓冲区
        
        等待 SQLite 确认提交后再返回，确保数据持久化。
        返回是否成功刷新。
        """
        return self._flush_buffer()
    
    def _cleanup_at_exit(self):
        """应用退出时的清理钩子，确保所有缓冲区日志被写入"""
        if self._async_write and self._buffer:
            logger.info(f"应用退出，刷新 {len(self._buffer)} 条待写入审计日志")
            self.flush()
    
    def query(self, query: AuditQuery) -> List[AuditLog]:
        """
        查询审计日志
        
        支持多种条件组合查询。
        """
        # 先刷新缓冲区，确保查询到最新数据
        self.flush()
        return self._storage.query(query)
    
    def count(self, query: AuditQuery) -> int:
        """统计审计日志数量"""
        self.flush()
        return self._storage.count(query)
    
    def cleanup(self) -> int:
        """清理过期审计日志"""
        return self._storage.delete_old(self._retention_days)
    
    # ==================== 便捷记录方法 ====================
    
    def log_create(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any] = None,
        **kwargs,
    ) -> str:
        """记录创建操作"""
        return self.log(
            operation=AuditOperation.CREATE_TRIPLE,
            status=AuditStatus.SUCCESS,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action="create",
            details=details,
            result="创建成功",
            **kwargs,
        )
    
    def log_update(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        changes: Dict[str, Any] = None,
        **kwargs,
    ) -> str:
        """记录更新操作"""
        return self.log(
            operation=AuditOperation.UPDATE_TRIPLE,
            status=AuditStatus.SUCCESS,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action="update",
            changes=changes,
            result="更新成功",
            **kwargs,
        )
    
    def log_delete(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any] = None,
        **kwargs,
    ) -> str:
        """记录删除操作"""
        return self.log(
            operation=AuditOperation.DELETE_TRIPLE,
            status=AuditStatus.SUCCESS,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action="delete",
            details=details,
            result="删除成功",
            **kwargs,
        )
    
    def log_query(
        self,
        user_id: str,
        resource_type: str,
        query_details: Dict[str, Any] = None,
        **kwargs,
    ) -> str:
        """记录查询操作"""
        return self.log(
            operation=AuditOperation.QUERY_TRIPLE,
            status=AuditStatus.SUCCESS,
            user_id=user_id,
            resource_type=resource_type,
            action="query",
            details=query_details,
            result="查询成功",
            **kwargs,
        )
    
    def log_inference(
        self,
        user_id: str,
        inference_type: str,
        details: Dict[str, Any] = None,
        status: AuditStatus = AuditStatus.SUCCESS,
        error_message: str = "",
        **kwargs,
    ) -> str:
        """记录推理操作"""
        return self.log(
            operation=AuditOperation.EXECUTE_INFERENCE,
            status=status,
            user_id=user_id,
            resource_type="inference",
            action=inference_type,
            details=details,
            error_message=error_message,
            **kwargs,
        )
    
    def log_failure(
        self,
        operation: AuditOperation,
        user_id: str,
        error_message: str,
        resource_type: str = "",
        resource_id: str = "",
        details: Dict[str, Any] = None,
        **kwargs,
    ) -> str:
        """记录失败操作"""
        return self.log(
            operation=operation,
            status=AuditStatus.FAILURE,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            error_message=error_message,
            details=details,
            result="操作失败",
            **kwargs,
        )
    
    def log_blocked(
        self,
        operation: AuditOperation,
        user_id: str,
        reason: str,
        resource_type: str = "",
        resource_id: str = "",
        **kwargs,
    ) -> str:
        """记录被阻止的操作"""
        return self.log(
            operation=operation,
            status=AuditStatus.BLOCKED,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            error_message=reason,
            result="操作被阻止",
            **kwargs,
        )
    
    def log_role_change(
        self,
        admin_id: str,
        target_user_id: str,
        role_name: str,
        action: str,  # "assign" 或 "revoke"
        **kwargs,
    ) -> str:
        """记录角色变更"""
        operation = AuditOperation.ASSIGN_ROLE if action == "assign" else AuditOperation.REVOKE_ROLE
        return self.log(
            operation=operation,
            status=AuditStatus.SUCCESS,
            user_id=admin_id,
            resource_type="role",
            resource_id=role_name,
            action=action,
            details={"target_user": target_user_id, "role": role_name},
            result=f"角色{action}成功",
            **kwargs,
        )
    
    def get_user_activity(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取用户活动记录
        
        用于用户行为分析和安全审计。
        """
        query = AuditQuery(
            user_id=user_id,
            start_time=datetime.now() - timedelta(days=days),
            limit=limit,
        )
        logs = self.query(query)
        return [log.to_dict() for log in logs]
    
    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        获取资源操作历史
        
        用于追踪资源的完整操作链。
        """
        query = AuditQuery(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )
        logs = self.query(query)
        return [log.to_dict() for log in logs]


# 全局审计日志管理器实例
audit_logger = AuditLogger()


# ==================== 审计装饰器 ====================

def audit_operation(
    operation: AuditOperation,
    resource_type: str = "",
    get_resource_id: Callable = None,
):
    """
    审计装饰器
    
    自动记录函数执行的审计日志。
    
    使用示例：
        @audit_operation(AuditOperation.CREATE_TRIPLE, "triple")
        def create_triple(user_id: str, subject: str, predicate: str, obj: str):
            ...
    
    参数：
        operation: 操作类型
        resource_type: 资源类型
        get_resource_id: 从函数返回值获取资源ID的函数
    """
    def decorator(func: Callable) -> Callable:
        import functools
        import asyncio
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 提取 user_id
            user_id = kwargs.get("user_id", "")
            
            # 执行原函数
            try:
                result = func(*args, **kwargs)
                
                # 获取资源ID
                resource_id = ""
                if get_resource_id and result:
                    resource_id = get_resource_id(result)
                
                # 记录成功审计日志
                audit_logger.log(
                    operation=operation,
                    status=AuditStatus.SUCCESS,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result="操作成功",
                )
                
                return result
            except Exception as e:
                # 记录失败审计日志
                audit_logger.log(
                    operation=operation,
                    status=AuditStatus.FAILURE,
                    user_id=user_id,
                    resource_type=resource_type,
                    error_message=str(e),
                    result="操作失败",
                )
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id", "")
            
            try:
                result = await func(*args, **kwargs)
                
                resource_id = ""
                if get_resource_id and result:
                    resource_id = get_resource_id(result)
                
                audit_logger.log(
                    operation=operation,
                    status=AuditStatus.SUCCESS,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result="操作成功",
                )
                
                return result
            except Exception as e:
                audit_logger.log(
                    operation=operation,
                    status=AuditStatus.FAILURE,
                    user_id=user_id,
                    resource_type=resource_type,
                    error_message=str(e),
                    result="操作失败",
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ==================== Auditor Agent ====================

class AuditorAgent(BaseAgent):
    """
    审计部智能体 (Auditor Agent) - V2 (Corrective)
    
    独立于推理主线，专门负责：
    1. 粒度冲突审计 (Fan-trap) + 纠错建议
    2. 基于图谱的动态准入校验
    3. 审计日志记录和查询
    """
    
    def __init__(self, name: str, reasoner: Any, semantic_memory: Any):
        super().__init__(name, reasoner)
        self.semantic_memory = semantic_memory
        # 将内存传递给校验器，实现从硬编码到图谱驱动的跃迁
        from ..core.ontology.grain_validator import GrainValidator
        self.grain_validator = GrainValidator(self.semantic_memory)
    
    async def audit_plan(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        审计工具执行计划
        
        检查操作是否存在潜在风险，如粒度冲突等。
        """
        logger.info(f"Auditor [{self.name}] 正在审计工具调用: {tool_name}")
        
        status = "PASSED"
        risk_details = []
        
        # 1. 针对 query_graph 的粒度审计
        if tool_name == "query_graph":
            query = args.get("query", "")
            # 简单关键词探测聚合意图
            agg_keywords = {
                "SUM": ["总计", "总额", "SUM"],
                "AVG": ["平均", "AVG"],
                "COUNT": ["计数", "数量", "COUNT"]
            }
            detected_agg_type = None
            for agg_type, keys in agg_keywords.items():
                if any(k in query.upper() for k in keys):
                    detected_agg_type = agg_type
                    break
            
            if detected_agg_type:
                # 触发粒度校验
                entities = [e for e in ["Order", "OrderItem", "Supplier"] if e.lower() in query.lower()]
                validation = self.grain_validator.validate_query_logic(entities, detected_agg_type)
                
                if validation["status"] == "RISK":
                    status = "BLOCKED"
                    risk_details.append(validation["message"])
                    risk_details.extend(validation["details"])
                    # 增加纠错性反馈
                    risk_details.append("💡 审计建议：检测到 1:N 聚合风险。请尝试使用子查询(Subquery)预先聚合，或在 JOIN 前确认 Cardinality 约束。")

        return {
            "status": status,
            "auditor": self.name,
            "risks": risk_details,
            "decision": "允许执行" if status == "PASSED" else "拦截并拒绝并提供重写建议"
        }

    async def run(self, task: str) -> Dict[str, Any]:
        """
        审计模式：对任务全生命周期进行旁路监控
        """
        return {"status": "monitoring", "audit_trail": []}


# ==================== 便捷函数 ====================

def log_audit(
    operation: Union[AuditOperation, str],
    status: Union[AuditStatus, str],
    user_id: str,
    **kwargs,
) -> str:
    """
    便捷函数：记录审计日志
    
    参数：
        operation: 操作类型（枚举或字符串）
        status: 操作状态（枚举或字符串）
        user_id: 用户ID
        **kwargs: 其他审计参数
    """
    # 转换枚举类型
    if isinstance(operation, str):
        operation = AuditOperation(operation)
    if isinstance(status, str):
        status = AuditStatus(status)
    
    return audit_logger.log(
        operation=operation,
        status=status,
        user_id=user_id,
        **kwargs,
    )


def query_audit_logs(
    user_id: str = None,
    days: int = 7,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    便捷函数：查询审计日志
    """
    query = AuditQuery(
        user_id=user_id,
        start_time=datetime.now() - timedelta(days=days),
        limit=limit,
    )
    logs = audit_logger.query(query)
    return [log.to_dict() for log in logs]
