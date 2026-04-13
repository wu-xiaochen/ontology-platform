"""
Clawra Neural Console - Graph Visualizer
Enhanced Pyvis integration for high-fidelity ontology visualization.
"""

import streamlit as st
import os
from pyvis.network import Network
from .theme import COLORS

class NeuralGraphRenderer:
    """高保真神经图谱渲染器"""
    
    def __init__(self, height="500px", bgcolor=COLORS['background']):
        self.height = height
        self.bgcolor = bgcolor

    def render(self, facts, limit=50):
        """核心渲染逻辑"""
        try:
            net = Network(height=self.height, width="100%", bgcolor=self.bgcolor, font_color="white", directed=True)
            
            # 强化物理模拟设置，使其看起来更具有“动态脉冲”感
            # 使用 barnes_hut 布局并增加引力系数
            net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)
            
            # 去除冗余节点
            nodes_added = set()
            
            for fact in facts[:limit]:
                # 根据来源或属性分配颜色
                # 蓝色: Ingested Knowledge | 红色: Global Neo4j | 黄色: Inference
                subject_color = COLORS['primary']
                if fact.source == "neo4j_sample":
                    subject_color = COLORS['secondary']
                elif "inference" in fact.source:
                    subject_color = COLORS['accent']
                
                # 添加主语节点
                if fact.subject not in nodes_added:
                    net.add_node(
                        fact.subject, 
                        label=fact.subject, 
                        color={
                            "background": subject_color,
                            "border": COLORS['glass_border'],
                            "highlight": {"background": COLORS['accent'], "border": "#FFFFFF"}
                        },
                        shadow={"enabled": True, "color": subject_color + "44", "size": 10},
                        shape="dot",
                        size=25 if fact.source != "neo4j_sample" else 15
                    )
                    nodes_added.add(fact.subject)
                
                # 添加宾语节点
                if fact.object not in nodes_added:
                    net.add_node(
                        fact.object, 
                        label=fact.object, 
                        color={
                            "background": "#2D333B", 
                            "border": COLORS['glass_border'],
                            "highlight": COLORS['primary']
                        },
                        shape="dot",
                        size=20
                    )
                    nodes_added.add(fact.object)
                
                # 添加关系边
                net.add_edge(
                    fact.subject, 
                    fact.object, 
                    label=fact.predicate, 
                    color={"color": "#484F58", "highlight": COLORS['primary']},
                    width=1,
                    font={"size": 10, "color": COLORS['text_dark'], "strokeWidth": 0}
                )
            
            # 保存并读取 HTML
            path = "temp_neural_graph.html"
            net.save_graph(path)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            os.remove(path)
            
            # 注入 CSS 以移除 pyvis 可能生成的白色边框
            html = html.replace("<body", '<body style="margin:0; padding:0; overflow:hidden;"')
            
            return html

        except Exception as e:
            return f"Visualization Error: {e}"
