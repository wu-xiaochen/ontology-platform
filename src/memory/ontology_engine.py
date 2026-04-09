"""
Ontology Engine - 基于 OWL 2 标准的本体引擎

该模块集成 Owlready2，为系统提供标准的语义 Web 能力：
1. 本体文件 (.owl) 的加载与动态管理
2. 基于类继承、互斥 (disjointWith) 及基数约束的逻辑验证
3. 自动推理器 (HermiT/Pellet) 集成，发现隐含关系
4. 知识图谱三元组与 OWL 实例的 OOM (Ontology Oriented Mapping)
"""

import logging
import os
from typing import List, Dict, Any, Optional
from owlready2 import *

from ..utils.config import get_config

logger = logging.getLogger(__name__)

class OntologyEngine:
    """
    本体引擎核心类
    
    负责维护系统的模式 (Schema) 与分类体系。
    """
    
    def __init__(self, onto_path: Optional[str] = None):
        """
        初始化本体引擎
        
        Args:
            onto_path: 本地 .owl 文件的路径。如果为空，将创建内存本体。
        """
        self.config = get_config()
        self.onto_path = onto_path or os.path.join(self.config.app.data_dir, "clawra_core.owl")
        
        # 探测 Java 环境，决定是否启用 HermiT
        self.java_available = self._check_java()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.onto_path), exist_ok=True)
        
        # 初始化本体库
        self.onto = self._load_or_create_ontology()
        
        if not self.java_available:
            logger.warning("⚠️ 系统未检测到 Java 环境。高级语义推理 (HermiT) 已禁用，将切换至 Python 原生逻辑保底模式。")
        
        logger.info(f"本体引擎就绪: {self.onto.base_iri}")

    def _check_java(self) -> bool:
        """检查系统是否安装了 Java"""
        import subprocess
        try:
            # 执行 java -version 检查
            subprocess.run(["java", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _load_or_create_ontology(self) -> Ontology:
        """加载现有本体或创建新本体"""
        if os.path.exists(self.onto_path):
            try:
                onto = get_ontology(f"file://{self.onto_path}").load()
                logger.info(f"成功加载本地本体: {self.onto_path}")
                return onto
            except Exception as e:
                logger.error(f"加载本体失败: {e}，将创建新本体")
        
        # 创建默认本体
        onto = get_ontology("http://clawra.ai/ontology/core#")
        with onto:
            # 定义基础元类
            class Entity(Thing): pass
            class Process(Thing): pass
            class Property(Thing): pass
            
            # 定义基础谓词
            class is_a(ObjectProperty):
                domain = [Entity]
                range = [Entity]
            
            class part_of(ObjectProperty, TransitiveProperty):
                domain = [Entity]
                range = [Entity]
                
        logger.info("已初始化默认核心本体结构")
        return onto

    def sync_reasoner(self):
        """
        执行自动推理 (Reasoning)
        
        通过调用内置逻辑推理器（如 HermiT），检测本体冲突并自动补全隐含推理。
        """
        if not self.java_available:
            logger.info("由于环境缺失 Java，跳过 HermiT 推理同步。系统将使用静态逻辑校验。")
            return

        try:
            with self.onto:
                sync_reasoner_hermit(infer_property_values=True)
            logger.info("本体推理同步完成")
        except Exception as e:
            logger.error(f"推理失败: {e}")

    def validate_contradiction(self, subject: str, predicate: str, obj: str) -> bool:
        """
        基于本体约束检测三元组是否违反逻辑
        
        包含：
        1. 互斥校验 (Disjointness)
        2. 域/值域校验 (Domain/Range)
        """
        with self.onto:
            # 查找实例
            sub_instance = self.onto.search_one(iri=f"*{subject}")
            obj_target = self.onto.search_one(iri=f"*{obj}")
            
            # 情况 A: 谓词是 is_a — 执行分类互斥校验
            if predicate == "is_a":
                if sub_instance and obj_target:
                    # 检查实例所属的所有类
                    for cls in sub_instance.is_a:
                        if not hasattr(cls, "disjoints"):
                            continue
                        # 遍历互斥集
                        for disjoint in cls.disjoints():
                            if obj_target in disjoint.entities:
                                logger.warning(f"🚨 逻辑冲突 (Disjoint): {subject} 不能属于 {obj} (原因: {cls} 与 {obj_target} 被定义为互斥)")
                                return False
                                
            # 情况 B: 谓词是 ObjectProperty — 执行域/值域校验
            prop = self.onto.search_one(iri=f"*{predicate}")
            if prop and isinstance(prop, ObjectProperty):
                # 校验 Domain
                if sub_instance:
                    for domain_cls in prop.domain:
                        if not any(isinstance(sub_instance, d) for d in prop.domain):
                            logger.warning(f"🚨 域冲突 (Domain): {subject} 不符合 {predicate} 的主语要求 (应为 {prop.domain})")
                            return False
                # 校验 Range
                if obj_target:
                    for range_cls in prop.range:
                        if not any(isinstance(obj_target, r) for r in prop.range):
                            logger.warning(f"🚨 值域冲突 (Range): {obj} 不符合 {predicate} 的宾语要求 (应为 {prop.range})")
                            return False
                            
        return True

    def save(self):
        """持久化本体到文件"""
        self.onto.save(file=self.onto_path, format="rdfxml")
        logger.info(f"本体文件已保存: {self.onto_path}")

    def add_class(self, class_name: str, parent_class: str = "Entity"):
        """动态添加本体类"""
        with self.onto:
            parent = self.onto.search_one(iri=f"*{parent_class}") or self.onto.Entity
            new_class = type(class_name, (parent,), {"namespace": self.onto})
        return new_class

    def add_instance(self, name: str, class_name: str):
        """动态添加实体实例"""
        with self.onto:
            cls = self.onto.search_one(iri=f"*{class_name}") or self.onto.Entity
            instance = cls(name)
        return instance
