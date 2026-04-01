"""
流式加载器测试 (Streaming Loader Tests)
"""
import sys
import os
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.loader import StreamingOntologyLoader

def test_streaming_json(tmp_path):
    """测试标准 JSON 的流式读取"""
    data = {
        "prefixes": {"ex": "http://example.org/"},
        "classes": [
            {"uri": "ex:Class1", "label": "Class 1"},
            {"uri": "ex:Class2", "label": "Class 2"}
        ],
        "properties": [
            {"uri": "ex:prop1", "label": "Prop 1"}
        ],
        "individuals": [
            {"uri": "ex:ind1", "label": "Ind 1"}
        ]
    }
    
    file_path = tmp_path / "test.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    loader = StreamingOntologyLoader(str(file_path))
    entities = list(loader.stream_entities())
    
    assert len(entities) == 4
    assert entities[0][0] == "class"
    assert entities[0][1].uri == "ex:Class1"
    assert entities[2][0] == "property"
    assert entities[3][0] == "individual"

def test_streaming_jsonl(tmp_path):
    """测试 JSONL 格式的流式读取"""
    items = [
        {"type": "class", "uri": "ex:C1", "label": "C1"},
        {"type": "property", "uri": "ex:P1", "label": "P1"},
        {"type": "individual", "uri": "ex:I1", "label": "I1"}
    ]
    
    file_path = tmp_path / "test.jsonl"
    with open(file_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item) + "\n")
            
    loader = StreamingOntologyLoader(str(file_path))
    entities = list(loader.stream_entities())
    
    assert len(entities) == 3
    assert entities[0][0] == "class"
    assert entities[1][0] == "property"
    assert entities[2][0] == "individual"

if __name__ == "__main__":
    # 模拟 tmp_path 如果手动运行
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        tp = Path(tmp_dir)
        test_streaming_json(tp)
        test_streaming_jsonl(tp)
        print("Streaming tests passed!")
