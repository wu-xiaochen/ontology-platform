"""
Clawra Neural Console - Design System & Theme
Focusing on Glassmorphism and Neon Aesthetics (Aligned with Awesome Design MD)
"""

import streamlit as st

# ─────────────────────────────────────────────
# Design Tokens
# ─────────────────────────────────────────────
COLORS = {
    "background": "#0E1117",
    "sidebar": "#161B22",
    "primary": "#00D4FF",  # Cyber Blue
    "secondary": "#FF6B6B",  # Neon Crimson
    "accent": "#FFCC00",  # Volt Yellow
    "glass": "rgba(255, 255, 255, 0.05)",
    "glass_border": "rgba(255, 255, 255, 0.1)",
    "text": "#E6EDF3",
    "text_dark": "#8B949E"
}

# ─────────────────────────────────────────────
# Custom CSS Implementation
# ─────────────────────────────────────────────
def apply_theme():
    """将全局样式注入 Streamlit"""
    st.markdown(f"""
    <style>
        /* 1. Global Reset & Typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: {COLORS['text']};
        }}

        .stApp {{
            background: radial-gradient(circle at 50% 50%, #1a1f2c 0%, #0e1117 100%);
        }}

        /* 2. Glassmorphism Containers */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['sidebar']} !important;
            border-right: 1px solid {COLORS['glass_border']};
        }}

        .stMetric {{
            background: {COLORS['glass']};
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px !important;
            border: 1px solid {COLORS['glass_border']};
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            transition: transform 0.3s ease;
        }}
        
        .stMetric:hover {{
            transform: translateY(-5px);
            border-color: {COLORS['primary']};
        }}

        /* 3. Neural Trace Cards */
        .trace-card {{
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            border-left: 4px solid {COLORS['primary']};
            border-radius: 0 10px 10px 0;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(5px);
        }}

        .trace-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid {COLORS['glass_border']};
            padding-bottom: 8px;
            margin-bottom: 10px;
        }}

        .agent-tag {{
            background: {COLORS['secondary']};
            color: white;
            padding: 2px 10px;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .latency-tag {{
            color: {COLORS['text_dark']};
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
        }}

        /* 4. Interactive Elements */
        .stButton>button {{
            background: transparent !important;
            border: 1px solid {COLORS['primary']} !important;
            color: {COLORS['primary']} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }}

        .stButton>button:hover {{
            background: {COLORS['primary']} !important;
            color: #000 !important;
            box-shadow: 0 0 20px {COLORS['primary']}44;
            transform: scale(1.02);
        }}

        /* 5. Custom Status Boxes */
        .reasoning-bubble {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px dashed {COLORS['glass_border']};
            border-radius: 8px;
            padding: 10px;
            margin-top: 5px;
        }}

        /* Scrollbar Styling */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: {COLORS['glass_border']};
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['primary']}44;
        }}
    </style>
    """, unsafe_allow_html=True)
