"""
Skill: 调压柜质量全量审计
Type: logic
Desc: 自动联通 GB 27791 和设备参数进行闭环合规扫描。
"""

MATCH (e:Entity {type:'Regulator'})-[:has_parameter]->(p) ...