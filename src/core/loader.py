"""
本体加载器 (Ontology Loader)
负责加载和解析 RDF/OWL 本体，构建知识图谱基础结构
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

# 初始化模块级日志记录器，用于记录本体加载过程中的异常和关键事件
logger = logging.getLogger(__name__)


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
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        # 解析JSONL中的每一行，捕获可能的JSON格式错误
                        item = json.loads(line)
                    except (json.JSONDecodeError, ValueError) as e:
                        # JSON解析失败时记录警告并跳过该行，避免整个加载过程中断
                        logger.warning(f"JSONL第{line_num}行解析失败，跳过: {e}")
                        continue
                    etype, parsed = self._parse_item(item)
                    if entity_type == "all" or etype == entity_type.rstrip('s'):
                        yield etype, parsed
            else:
                # 简单实现：对于标准 JSON，依然采用一次性加载，或者提示使用 JSONL
                try:
                    data = json.load(f)
                except (json.JSONDecodeError, ValueError) as e:
                    # 整个JSON文件解析失败，抛出更详细的错误信息帮助定位问题
                    raise ValueError(f"JSON文件解析失败 '{self.file_path}': {e}") from e
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
        """
        加载 RDF/XML 格式本体
        
        使用 Python 内置的 xml.etree.ElementTree 解析 RDF/XML 格式文件，
        避免引入外部依赖库。支持解析类定义、属性定义和实例声明。
        
        Args:
            path: RDF/XML 文件路径
            
        Returns:
            加载后的 OntologyLoader 实例
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: 文件格式错误时抛出
        """
        import xml.etree.ElementTree as ET
        import logging
        
        # 检查文件是否存在，避免后续操作失败
        if not path.exists():
            raise FileNotFoundError(f"RDF/XML 文件不存在: {path}")
        
        # 定义 RDF 和 RDFS 命名空间，用于解析 XML 元素
        # 使用标准 W3C 命名空间 URI，确保兼容性
        namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'owl': 'http://www.w3.org/2002/07/owl#'
        }
        
        try:
            # 解析 XML 文件，获取根元素
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError as e:
            # XML 格式错误时提供清晰的错误信息
            raise ValueError(f"RDF/XML 文件格式错误: {e}")
        
        # 从根元素提取文件中定义的所有命名空间
        # 这允许处理使用自定义命名空间的本体文件
        for prefix, uri in root.attrib.items():
            if prefix.startswith('{'):
                continue
            if prefix.startswith('xmlns:'):
                ns_prefix = prefix[6:]  # 去掉 'xmlns:' 前缀
                self.prefixes[ns_prefix] = uri
        
        # 遍历所有 RDF Description 元素，解析本体内容
        # RDF/XML 使用 Description 元素描述资源
        for description in root.findall('.//rdf:Description', namespaces):
            # 获取资源的 URI，这是资源的唯一标识
            about = description.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
            if not about:
                # 跳过没有 URI 的匿名资源（blank nodes）
                continue
            
            # 解析类定义：检查是否为 rdfs:Class 或 owl:Class
            # 这是本体中类的标准声明方式
            type_elem = description.find('rdf:type', namespaces)
            if type_elem is not None:
                type_uri = type_elem.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                if type_uri in [
                    'http://www.w3.org/2000/01/rdf-schema#Class',
                    'http://www.w3.org/2002/07/owl#Class'
                ]:
                    # 提取类标签，优先使用 rdfs:label，否则从 URI 生成
                    label_elem = description.find('rdfs:label', namespaces)
                    label = label_elem.text if label_elem is not None else about.split('#')[-1].split('/')[-1]
                    
                    # 提取父类信息，支持 rdfs:subClassOf 关系
                    super_classes = []
                    for sub_class in description.findall('rdfs:subClassOf', namespaces):
                        parent = sub_class.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                        if parent:
                            super_classes.append(parent)
                    
                    # 创建类对象并注册到加载器中
                    self.classes[about] = OntologyClass(
                        uri=about,
                        label=label,
                        super_classes=super_classes
                    )
                    continue
                
                # 解析属性定义：检查是否为 rdf:Property 或 owl:ObjectProperty/DatatypeProperty
                if type_uri in [
                    'http://www.w3.org/1999/02/22-rdf-syntax-ns#Property',
                    'http://www.w3.org/2002/07/owl#ObjectProperty',
                    'http://www.w3.org/2002/07/owl#DatatypeProperty'
                ]:
                    # 提取属性标签
                    label_elem = description.find('rdfs:label', namespaces)
                    label = label_elem.text if label_elem is not None else about.split('#')[-1].split('/')[-1]
                    
                    # 提取 domain 和 range 定义，用于属性约束
                    domain = []
                    for d in description.findall('rdfs:domain', namespaces):
                        d_uri = d.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                        if d_uri:
                            domain.append(d_uri)
                    
                    range_vals = []
                    for r in description.findall('rdfs:range', namespaces):
                        r_uri = r.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                        if r_uri:
                            range_vals.append(r_uri)
                    
                    # 根据类型确定属性类别：对象属性或数据属性
                    prop_type = 'object' if type_uri != 'http://www.w3.org/2002/07/owl#DatatypeProperty' else 'datatype'
                    
                    self.properties[about] = OntologyProperty(
                        uri=about,
                        label=label,
                        domain=domain,
                        range=range_vals,
                        property_type=prop_type
                    )
                    continue
                
                # 解析实例定义：任何有类型的资源都视为实例
                if type_uri:
                    label_elem = description.find('rdfs:label', namespaces)
                    label = label_elem.text if label_elem is not None else about.split('#')[-1].split('/')[-1]
                    
                    # 收集实例的所有类型声明
                    types = [type_uri]
                    
                    # 解析实例的属性断言（简单属性值）
                    assertions = {}
                    for child in description:
                        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        if tag not in ['type', 'label']:
                            # 提取属性值，优先使用 resource 引用，否则使用文本内容
                            resource = child.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                            if resource:
                                assertions[child.tag] = resource
                            elif child.text:
                                assertions[child.tag] = child.text.strip()
                    
                    self.individuals[about] = OntologyIndividual(
                        uri=about,
                        label=label,
                        types=types,
                        assertions=assertions
                    )
        
        # 记录加载结果，便于调试和监控
        logger = logging.getLogger(__name__)
        logger.info(f"RDF/XML 加载完成: {len(self.classes)} 个类, {len(self.properties)} 个属性, {len(self.individuals)} 个实例")
        
        return self
    
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
