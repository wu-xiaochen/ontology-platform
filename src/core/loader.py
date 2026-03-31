"""
本体加载器 (Ontology Loader)
负责加载和解析 RDF/OWL 本体，构建知识图谱基础结构
"""

import json
import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class OntologyClass:
    """本体类"""
    uri: str
    label: str
    super_classes: list[str] = field(default_factory=list)
    equivalent_classes: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class OntologyProperty:
    """本体属性"""
    uri: str
    label: str
    domain: list[str] = field(default_factory=list)
    range: list[str] = field(default_factory=list)
    super_properties: list[str] = field(default_factory=list)
    property_type: str = "object"  # object, datatype, annotation


@dataclass
class OntologyIndividual:
    """本体实例"""
    uri: str
    label: str
    types: list[str] = field(default_factory=list)
    assertions: dict[str, Any] = field(default_factory=dict)


class StreamingOntologyLoader:
    """
    流式本体加载器 (Streaming Ontology Loader)
    通过迭代器方式读取本体，降低内存开销
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.prefixes: dict[str, str] = {}
        
    def stream_entities(self, entity_type: str = "all"):
        """
        流式获取实体
        
        Args:
            entity_type: 实体类型 (classes, properties, individuals, all)
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
            
        # 这里实现一个基于生成器的加载逻辑
        # 对于大规模本体，推荐使用 JSONL 格式 (每行一个 JSON 对象)
        with open(self.file_path, 'r', encoding='utf-8') as f:
            if self.file_path.suffix == '.jsonl':
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    etype, parsed = self._parse_item(item)
                    if entity_type == "all" or etype == entity_type.rstrip('s'):
                        yield etype, parsed
            else:
                # 简单实现：对于标准 JSON，依然采用一次性加载，或者提示使用 JSONL
                data = json.load(f)
                self.prefixes = data.get('prefixes', {})
                
                if entity_type in ["classes", "all"]:
                    for item in data.get('classes', []):
                        yield "class", self._parse_class(item)
                
                if entity_type in ["properties", "all"]:
                    for item in data.get('properties', []):
                        yield "property", self._parse_property(item)
                        
                if entity_type in ["individuals", "all"]:
                    for item in data.get('individuals', []):
                        yield "individual", self._parse_individual(item)
    
    def _parse_class(self, data: dict) -> OntologyClass:
        return OntologyClass(
            uri=data['uri'],
            label=data.get('label', data['uri'].split('#')[-1]),
            super_classes=data.get('super_classes', []),
            equivalent_classes=data.get('equivalent_classes', []),
            properties=data.get('properties', {})
        )

    def _parse_property(self, data: dict) -> OntologyProperty:
        return OntologyProperty(
            uri=data['uri'],
            label=data.get('label', data['uri'].split('#')[-1]),
            domain=data.get('domain', []),
            range=data.get('range', []),
            super_properties=data.get('super_properties', []),
            property_type=data.get('property_type', 'object')
        )
        
    def _parse_individual(self, data: dict) -> OntologyIndividual:
        return OntologyIndividual(
            uri=data['uri'],
            label=data.get('label', data['uri'].split('#')[-1]),
            types=data.get('types', []),
            assertions=data.get('assertions', {})
        )

    def _parse_item(self, item: dict):
        """解析 JSONL 中的通用项"""
        etype = item.get('type')
        if etype == 'class':
            return "class", self._parse_class(item)
        elif etype == 'property':
            return "property", self._parse_property(item)
        elif etype == 'individual':
            return "individual", self._parse_individual(item)
        return "unknown", item


class OntologyLoader:
    """
    本体加载器
    
    支持加载:
    - JSON 格式的本体 (推荐)
    - Turtle (.ttl) 格式
    - RDF/XML (.rdf) 格式
    
    示例:
        loader = OntologyLoader()
        ontology = loader.load("ontology.json")
        print(f"加载了 {len(ontology.classes)} 个类")
    """
    
    def __init__(self):
        self.classes: dict[str, OntologyClass] = {}
        self.properties: dict[str, OntologyProperty] = {}
        self.individuals: dict[str, OntologyIndividual] = {}
        self.prefixes: dict[str, str] = {}
        
    def load(self, file_path: str) -> 'OntologyLoader':
        """加载本体文件"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.json':
            return self._load_json(path)
        elif suffix == '.ttl':
            return self._load_turtle(path)
        elif suffix == '.rdf':
            return self._load_rdfxml(path)
        else:
            raise ValueError(f"不支持的格式: {suffix}")
    
    def _load_json(self, path: Path) -> 'OntologyLoader':
        """加载 JSON 格式本体"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 加载前缀
        self.prefixes = data.get('prefixes', {})
        
        # 加载类
        for cls_data in data.get('classes', []):
            cls = OntologyClass(
                uri=cls_data['uri'],
                label=cls_data.get('label', cls_data['uri'].split('#')[-1]),
                super_classes=cls_data.get('super_classes', []),
                equivalent_classes=cls_data.get('equivalent_classes', []),
                properties=cls_data.get('properties', {})
            )
            self.classes[cls.uri] = cls
        
        # 加载属性
        for prop_data in data.get('properties', []):
            prop = OntologyProperty(
                uri=prop_data['uri'],
                label=prop_data.get('label', prop_data['uri'].split('#')[-1]),
                domain=prop_data.get('domain', []),
                range=prop_data.get('range', []),
                super_properties=prop_data.get('super_properties', []),
                property_type=prop_data.get('property_type', 'object')
            )
            self.properties[prop.uri] = prop
        
        # 加载实例
        for ind_data in data.get('individuals', []):
            ind = OntologyIndividual(
                uri=ind_data['uri'],
                label=ind_data.get('label', ind_data['uri'].split('#')[-1]),
                types=ind_data.get('types', []),
                assertions=ind_data.get('assertions', {})
            )
            self.individuals[ind.uri] = ind
        
        return self
    
    def _load_turtle(self, path: Path) -> 'OntologyLoader':
        """加载 Turtle 格式本体 (简化实现)"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析前缀
        prefix_pattern = r'@prefix\s+(\w+):\s+<(.+)>'
        for match in re.finditer(prefix_pattern, content):
            self.prefixes[match.group(1)] = match.group(2)
        
        # 简化: 解析类定义
        class_pattern = r'<(\w+)>\s+a\s+rdfs:Class'
        for match in re.finditer(class_pattern, content):
            uri = match.group(1)
            self.classes[uri] = OntologyClass(uri=uri, label=uri.split('#')[-1])
        
        return self
    
    def _load_rdfxml(self, path: Path) -> 'OntologyLoader':
        """加载 RDF/XML 格式本体 (占位实现)"""
        # 实际项目中可使用 rdflib 库
        raise NotImplementedError("RDF/XML 格式加载需要 rdflib 库")
    
    def get_class(self, uri: str) -> Optional[OntologyClass]:
        """获取类"""
        return self.classes.get(uri)
    
    def get_property(self, uri: str) -> Optional[OntologyProperty]:
        """获取属性"""
        return self.properties.get(uri)
    
    def get_individual(self, uri: str) -> Optional[OntologyIndividual]:
        """获取实例"""
        return self.individuals.get(uri)
    
    def get_all_subclasses(self, class_uri: str, direct: bool = False) -> set[str]:
        """
        获取类的所有子类
        
        Args:
            class_uri: 父类 URI
            direct: 是否只返回直接子类
        
        Returns:
            子类 URI 集合
        """
        result = set()
        for uri, cls in self.classes.items():
            if class_uri in cls.super_classes:
                result.add(uri)
                if not direct:
                    result.update(self.get_all_subclasses(uri))
        return result
    
    def get_all_superclasses(self, class_uri: str, direct: bool = False) -> set[str]:
        """
        获取类的所有父类
        
        Args:
            class_uri: 子类 URI
            direct: 是否只返回直接父类
        
        Returns:
            父类 URI 集合
        """
        cls = self.classes.get(class_uri)
        if not cls:
            return set()
        
        result = set(cls.super_classes)
        if not direct:
            for super_uri in cls.super_classes:
                result.update(self.get_all_superclasses(super_uri))
        return result
    
    def expand_uri(self, prefixed_uri: str) -> str:
        """展开前缀 URI"""
        if prefixed_uri.startswith('http'):
            return prefixed_uri
        
        if ':' in prefixed_uri:
            prefix, local = prefixed_uri.split(':', 1)
            if prefix in self.prefixes:
                return self.prefixes[prefix] + local
        return prefixed_uri
    
    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            'prefixes': self.prefixes,
            'classes': [
                {
                    'uri': c.uri,
                    'label': c.label,
                    'super_classes': c.super_classes,
                    'equivalent_classes': c.equivalent_classes,
                    'properties': c.properties
                }
                for c in self.classes.values()
            ],
            'properties': [
                {
                    'uri': p.uri,
                    'label': p.label,
                    'domain': p.domain,
                    'range': p.range,
                    'super_properties': p.super_properties,
                    'property_type': p.property_type
                }
                for p in self.properties.values()
            ],
            'individuals': [
                {
                    'uri': i.uri,
                    'label': i.label,
                    'types': i.types,
                    'assertions': i.assertions
                }
                for i in self.individuals.values()
            ]
        }


# 便捷函数
def create_sample_ontology() -> OntologyLoader:
    """创建示例本体 (用于测试)"""
    loader = OntologyLoader()
    
    # 添加类
    loader.classes['http://example.org/Thing'] = OntologyClass(
        uri='http://example.org/Thing',
        label='Thing',
        super_classes=[],
        properties={'comment': '所有事物的根类'}
    )
    
    loader.classes['http://example.org/Animal'] = OntologyClass(
        uri='http://example.org/Animal',
        label='Animal',
        super_classes=['http://example.org/Thing'],
        properties={'comment': '动物'}
    )
    
    loader.classes['http://example.org/Person'] = OntologyClass(
        uri='http://example.org/Person',
        label='Person',
        super_classes=['http://example.org/Thing'],
        properties={'comment': '人'}
    )
    
    loader.classes['http://example.org/Student'] = OntologyClass(
        uri='http://example.org/Student',
        label='Student',
        super_classes=['http://example.org/Person'],
        properties={'comment': '学生'}
    )
    
    loader.classes['http://example.org/Teacher'] = OntologyClass(
        uri='http://example.org/Teacher',
        label='Teacher',
        super_classes=['http://example.org/Person'],
        properties={'comment': '教师'}
    )
    
    # 添加属性
    loader.properties['http://example.org/hasName'] = OntologyProperty(
        uri='http://example.org/hasName',
        label='hasName',
        domain=['http://example.org/Thing'],
        range=['http://www.w3.org/2001/XMLSchema#string'],
        property_type='datatype'
    )
    
    loader.properties['http://example.org/knows'] = OntologyProperty(
        uri='http://example.org/knows',
        label='knows',
        domain=['http://example.org/Person'],
        range=['http://example.org/Person'],
        property_type='object'
    )
    
    loader.properties['http://example.org/teaches'] = OntologyProperty(
        uri='http://example.org/teaches',
        label='teaches',
        domain=['http://example.org/Teacher'],
        range=['http://example.org/Student'],
        property_type='object'
    )
    
    # 添加实例
    loader.individuals['http://example.org/Alice'] = OntologyIndividual(
        uri='http://example.org/Alice',
        label='Alice',
        types=['http://example.org/Student'],
        assertions={'http://example.org/hasName': 'Alice'}
    )
    
    loader.individuals['http://example.org/Bob'] = OntologyIndividual(
        uri='http://example.org/Bob',
        label='Bob',
        types=['http://example.org/Teacher'],
        assertions={'http://example.org/hasName': 'Bob'}
    )
    
    return loader


if __name__ == '__main__':
    # 测试代码
    print("=== 本体加载器测试 ===\n")
    
    # 创建示例本体
    loader = create_sample_ontology()
    
    print(f"加载了 {len(loader.classes)} 个类")
    print(f"加载了 {len(loader.properties)} 个属性")
    print(f"加载了 {len(loader.individuals)} 个实例\n")
    
    # 测试查询
    print("--- 类层次查询 ---")
    print(f"Person 的所有父类: {loader.get_all_superclasses('http://example.org/Person')}")
    print(f"Thing 的所有子类: {loader.get_all_subclasses('http://example.org/Thing')}")
    
    print("\n--- 类信息 ---")
    student = loader.get_class('http://example.org/Student')
    if student:
        print(f"Student: {student.label}")
        print(f"  父类: {student.super_classes}")
        print(f"  注释: {student.properties.get('comment')}")
    
    print("\n--- 实例信息 ---")
    alice = loader.get_individual('http://example.org/Alice')
    if alice:
        print(f"Alice: {alice.types}")
        print(f"  属性: {alice.assertions}")
