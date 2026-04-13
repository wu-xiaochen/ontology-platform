"""
Clawra Agent Demo — 自主进化 Agent 框架演示
=============================================

5-Tab 架构:
  1. Agent 对话 — LLM + Clawra 知识增强
  2. 自主学习 — 文本学习 + 规则发现
  3. 本体图谱 — 知识可视化
  4. 推理引擎 — 事实管理 + 前向链推理
  5. 评估与统计 — Benchmark + 成长数据

启动: streamlit run examples/clawra_demo.py
"""
import streamlit as st
import sys
import os
import json
import time
import asyncio
import re
from typing import Dict, List, Any

# 修复导入路径：将项目根目录加入 sys.path（而非 src/），使相对导入正常工作
_DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_DEMO_DIR, '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# VolcEngine Ark LLM 默认配置 (仅在未设置时生效)
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "e2e894dc-4ce5-4a7e-87d5-a7da2c12135a"
if not os.getenv("OPENAI_BASE_URL"):
    os.environ["OPENAI_BASE_URL"] = "https://ark.cn-beijing.volces.com/api/v3"
if not os.getenv("OPENAI_MODEL"):
    os.environ["OPENAI_MODEL"] = "doubao-seed-2-0-pro-260215"

# 导入 Clawra 核心组件（使用 src. 前缀）
from src.clawra import Clawra
from src.evolution.unified_logic import LogicType
from src.evolution.llm_extractor import LLMKnowledgeExtractor
from src.core.reasoner import Fact
from src.utils.config import get_config

# ─────────────────────────────────────────────
# st.rerun() 兼容处理：旧版 Streamlit 使用 experimental_rerun
# 必须在侧边栏之前定义，确保全局可用
# ─────────────────────────────────────────────
def safe_rerun():
    """兼容新旧版本的 rerun 函数"""
    if hasattr(st, 'rerun'):
        st.rerun()
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()

# ─────────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Clawra Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 全局 Design System (inspired by Linear DESIGN.md methodology)
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── 1. Visual Theme: Dark-mode-native, 深色主基调 ── */
:root {
    --bg-primary: #0f1117;
    --bg-surface: #1a1c23;
    --bg-elevated: #262730;
    --text-primary: #fafafa;
    --text-secondary: #c5c8d4;
    --text-muted: #8b8fa3;
    --accent-brand: #5e6ad2;
    --accent-bright: #7170ff;
    --border-subtle: rgba(255,255,255,0.06);
    --border-standard: rgba(255,255,255,0.10);
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
}

/* ── 2. Typography: 紧凑行距, 清晰层次 ── */
[data-testid="stMarkdownContainer"] p { margin-bottom: 0.4rem; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { margin-bottom: 0.5rem; }

/* ── 3. Sidebar: 紧凑化 ── */
section[data-testid="stSidebar"] [data-testid="stMetric"] {
    padding: 0.2rem 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stMetric"] label {
    font-size: 0.75rem !important;
}

/* ── 4. Tab 内容区: 正常滚动, 不截断 ── */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 1rem !important;
}

/* ── 5. Chat 消息气泡: 全宽, 紧凑 ── */
[data-testid="stChatMessage"] {
    max-width: 100%;
    padding: 0.6rem 1rem !important;
}

/* ── 6. Expander: 精简样式 ── */
[data-testid="stExpander"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
}

/* ── 7. Metric 卡片: 紧凑化 ── */
[data-testid="stMetric"] {
    background: transparent;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.3rem !important;
}

/* ── 8. Dataframe: 紧凑 ── */
[data-testid="stDataFrame"] { font-size: 0.85rem; }

/* ── 9. 修复 chat_input: 始终可见 ── */
[data-testid="stChatInput"] {
    padding-top: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 预置知识包
# ─────────────────────────────────────────────
KNOWLEDGE_PACKS = {
    "燃气设备": {
        "texts": [
            "燃气调压箱是一种用于降低燃气管道压力的设备。"
            "如果设备是燃气调压箱，那么需要每6个月进行维护检查。"
            "燃气调压箱的进口压力范围为0.02-0.4 MPa，出口压力应稳定在2-5 kPa。"
            "如果出口压力超过安全阈值，那么必须立即关闭阀门。"
            "调压箱主要品牌包括特瑞斯、春晖、永良。"
            "燃气调压箱属于燃气设备类别。"
        ],
        "facts": [
            ("调压箱A", "is_a", "燃气调压箱", 0.95),
            ("调压箱B", "is_a", "燃气调压箱", 0.95),
            ("燃气调压箱", "is_a", "燃气设备", 0.99),
            ("调压箱A", "出口压力", "3.5kPa", 0.90),
            ("调压箱B", "出口压力", "6.2kPa", 0.90),
            ("调压箱A", "requires", "定期维护", 0.85),
            ("燃气调压箱", "requires", "定期维护", 0.90),
        ],
    },
    "医学": {
        "texts": [
            "糖尿病是一种慢性代谢疾病，主要表现为血糖升高。"
            "如果患者空腹血糖高于7.0 mmol/L，那么需要进一步检查糖化血红蛋白。"
            "如果糖化血红蛋白超过6.5%，那么确诊为糖尿病。"
            "胰岛素是治疗糖尿病的关键药物。"
            "如果血糖超过11.1 mmol/L，那么需要注射胰岛素治疗。"
            "糖尿病患者需要定期监测血糖。"
        ],
        "facts": [
            ("患者张三", "is_a", "糖尿病患者", 0.95),
            ("糖尿病患者", "is_a", "慢性病患者", 0.99),
            ("患者张三", "空腹血糖", "8.5mmol/L", 0.90),
            ("患者张三", "requires", "血糖监测", 0.85),
            ("胰岛素", "is_a", "药物", 0.99),
        ],
    },
}


# ─────────────────────────────────────────────
# LLM 对话辅助
# ─────────────────────────────────────────────
def _get_llm_client():
    """延迟初始化 LLM 客户端"""
    if "llm_client" not in st.session_state:
        from openai import AsyncOpenAI
        cfg = get_config().llm
        st.session_state.llm_client = AsyncOpenAI(
            api_key=cfg.api_key or os.getenv("OPENAI_API_KEY", ""),
            base_url=cfg.base_url or os.getenv("OPENAI_BASE_URL",
                                                "https://ark.cn-beijing.volces.com/api/v3"),
        )
    return st.session_state.llm_client


def _get_model_name() -> str:
    cfg = get_config().llm
    return cfg.model or os.getenv("OPENAI_MODEL", "doubao-seed-2-0-pro-260215")


def _extract_keywords(text: str) -> List[str]:
    """中文关键词提取（停用字切分 + bigram 子词）"""
    stop_chars = set("的是了在和有我你他她什么怎么如何为什么哪些请吗呢一个这个那个需要可以应该关于告诉")
    words = set()
    for seg in re.findall(r'[\u4e00-\u9fff]+', text):
        current = []
        for ch in seg:
            if ch in stop_chars:
                if len(current) >= 2:
                    words.add(''.join(current))
                current = []
            else:
                current.append(ch)
        if len(current) >= 2:
            words.add(''.join(current))
    for w in re.findall(r'[a-zA-Z_]{2,}', text):
        words.add(w)
    extra = set()
    for w in list(words):
        if len(w) > 4:
            for i in range(len(w) - 1):
                sub = w[i:i + 2]
                if sub not in stop_chars:
                    extra.add(sub)
    words |= extra
    return list(words)[:15]


def _retrieve_knowledge(clawra: Clawra, query: str) -> Dict[str, Any]:
    """从 Clawra 知识库检索相关知识"""
    keywords = _extract_keywords(query)

    matched_facts = []
    for kw in keywords:
        for fact in clawra.reasoner.facts:
            fact_text = f"{fact.subject} {fact.predicate} {fact.object}".lower()
            if kw.lower() in fact_text and fact not in matched_facts:
                matched_facts.append(fact)

    matched_patterns = []
    for kw in keywords:
        for pid, p in clawra.logic_layer.patterns.items():
            desc = f"{p.name} {p.description}".lower()
            if kw.lower() in desc and p not in matched_patterns:
                matched_patterns.append(p)

    inference_results = []
    if clawra.reasoner.facts:
        result = clawra.reasoner.forward_chain(max_depth=3)
        if result.conclusions:
            for step in result.conclusions:
                ct = (f"{step.conclusion.subject} "
                      f"{step.conclusion.predicate} "
                      f"{step.conclusion.object}")
                for kw in keywords:
                    if kw.lower() in ct.lower():
                        inference_results.append(step)
                        break

    return {
        "facts": matched_facts,
        "patterns": matched_patterns,
        "inferences": inference_results,
        "has_knowledge": bool(matched_facts or matched_patterns or inference_results),
    }


def _detect_intent(message: str) -> str:
    """检测用户意图: learn / query"""
    triggers = ["学习", "学一下", "记住", "学这个", "帮我学", "请学习",
                "learn", "study", "教你", "告诉你一个知识"]
    msg = message.lower().strip()
    for t in triggers:
        if msg.startswith(t) or f"：{t}" in msg:
            return "learn"
        if t in msg and ("：" in message or ":" in message or "\n" in message):
            return "learn"
    return "query"


def _extract_learn_text(message: str) -> str:
    """提取要学习的文本"""
    prefixes = ["学习：", "学习:", "学习 ", "学一下：", "学一下:", "帮我学：",
                "帮我学:", "请学习：", "请学习:", "learn:", "learn：",
                "教你：", "教你:", "记住：", "记住:"]
    text = message
    for prefix in prefixes:
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
            break
    return text.strip()


def run_async(coro):
    """在 Streamlit 中安全运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=60)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _llm_chat(messages: List[Dict]) -> str:
    """调用 LLM"""
    try:
        resp = await _get_llm_client().chat.completions.create(
            model=_get_model_name(),
            messages=messages,
            temperature=0.5,
            max_tokens=1500,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"LLM 调用失败: {e}"


# ─────────────────────────────────────────────
# 初始化 Session State
# ─────────────────────────────────────────────
if "clawra" not in st.session_state:
    st.session_state.clawra = Clawra()
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "你好！我是 **Clawra Agent** — 一个集成了自主进化引擎的智能助手。\n\n"
            "我能做什么：\n"
            "- 📚 **学习知识**: 发送 `学习：[文本]` 我会自动提取规则和逻辑\n"
            "- 🤖 **智能问答**: 直接提问，我会基于已学习的知识回答\n"
            "- 🔍 **推理增强**: 我的回答会标注知识来源，有据可依\n\n"
            "👈 试试左侧的 **快速加载知识** 按钮，然后向我提问！"
        ),
        "source": "system",
    }]
    st.session_state.learn_log = []
    st.session_state.chat_stats = {"queries": 0, "grounded": 0}

sdk: Clawra = st.session_state.clawra


# ─────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────
def _get_stats() -> Dict:
    """获取统计信息"""
    stats = sdk.get_statistics()
    pattern_stats = stats["patterns"]
    return {
        "patterns": pattern_stats["total_patterns"],
        "facts": stats["facts"],
        "domains": len(pattern_stats.get("by_domain", {})),
        "domain_list": pattern_stats.get("by_domain", {}),
        "by_type": pattern_stats.get("by_type", {}),
        "learning": stats["learning"],
        "queries": st.session_state.chat_stats["queries"],
        "grounded": st.session_state.chat_stats["grounded"],
    }


# ─────────────────────────────────────────────
# 侧边栏
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Clawra Agent")
    stats = _get_stats()

    c1, c2 = st.columns(2)
    c1.metric("知识模式", stats["patterns"])
    c2.metric("事实数", stats["facts"])

    c3, c4 = st.columns(2)
    c3.metric("对话轮次", stats["queries"])
    c4.metric("知识增强", stats["grounded"])

    st.markdown("---")
    st.markdown("### 快速加载知识")

    for pack_name, pack_data in KNOWLEDGE_PACKS.items():
        if st.button(f"📦 加载{pack_name}知识", key=f"load_{pack_name}",
                     use_container_width=True):
            with st.spinner(f"学习{pack_name}知识中..."):
                for text in pack_data["texts"]:
                    sdk.learn(text)
                for s, p, o, c in pack_data["facts"]:
                    sdk.add_fact(s, p, o, c)
                st.session_state.learn_log.append({
                    "time": time.strftime("%H:%M:%S"),
                    "source": pack_name,
                    "texts": len(pack_data["texts"]),
                    "facts": len(pack_data["facts"]),
                })
                # 展示加载结果（包含 LLM 自动生成的事实）
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": (f"✅ 已加载 **{pack_name}** 知识包！\n\n"
                                f"学习了 {len(pack_data['texts'])} 段文本，"
                                f"手动添加 {len(pack_data['facts'])} 条事实，"
                                f"当前事实库共 {len(sdk.reasoner.facts)} 条。"),
                    "source": "system",
                })
            safe_rerun()

    # 加载完整知识库
    gas_path = os.path.join(os.path.dirname(__file__), "../data/gas_knowledge.txt")
    if os.path.exists(gas_path):
        if st.button("📖 加载完整燃气知识库", use_container_width=True):
            with st.spinner("加载 gas_knowledge.txt ..."):
                with open(gas_path, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip()]
                # 每5行为一段学习
                count = 0
                for i in range(0, len(lines), 5):
                    chunk = "。".join(lines[i:i + 5])
                    sdk.learn(chunk)
                    count += 1
                st.session_state.learn_log.append({
                    "time": time.strftime("%H:%M:%S"),
                    "source": "gas_knowledge.txt",
                    "texts": count,
                    "facts": 0,
                })
            safe_rerun()

    st.markdown("---")
    st.markdown("### 已学习领域")
    if stats["domain_list"]:
        for domain, count in stats["domain_list"].items():
            st.markdown(f"- **{domain}**: {count} 个模式")
    else:
        st.caption("暂无 — 请加载知识或在对话中教我")

    st.markdown("---")
    if st.button("🗑️ 重置系统", use_container_width=True):
        sdk.reset()
        st.session_state.messages = st.session_state.messages[:1]
        st.session_state.learn_log = []
        st.session_state.chat_stats = {"queries": 0, "grounded": 0}
        safe_rerun()


# ─────────────────────────────────────────────
# 主界面
# ─────────────────────────────────────────────
st.title("🧠 Clawra Agent")
st.caption("自主学习 · 知识增强推理 · 可追溯 · 可进化")

# ─────────────────────────────────────────────
# chat_input 必须放在顶层（不能在 tabs 内）
# 这是 Streamlit 的限制：st.chat_input 不能放在 tabs/expander/form 内
# ─────────────────────────────────────────────
user_input = st.chat_input("直接提问 / 输入 学习：[文本] 教Agent新知识")

# 将用户输入存入 session_state，供 tabs 内处理
if user_input and user_input.strip():
    st.session_state["pending_user_input"] = user_input.strip()

# 定义 tabs（必须在 chat_input 之后）
tab_chat, tab_learn, tab_ontology, tab_reason, tab_eval = st.tabs([
    "💬 Agent 对话", "📚 自主学习", "🔮 本体图谱", "⚙️ 推理引擎", "📊 评估与统计"
])


# ==============================================
# Tab 1: Agent 对话
# ==============================================


def _process_user_message(user_input: str):
    """处理用户消息：学习 or 问答"""
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_stats["queries"] += 1

    intent = _detect_intent(user_input)

    if intent == "learn":
        learn_text = _extract_learn_text(user_input)
        result = sdk.learn(learn_text)
        if result.get("success"):
            pids = result.get("learned_patterns", [])
            facts_added = result.get("facts_added", 0)
            extracted_facts = result.get("extracted_facts", [])
            details = []
            for pid in pids:
                if pid in sdk.logic_layer.patterns:
                    p = sdk.logic_layer.patterns[pid]
                    details.append(f"- **{p.name}**: {p.description}")

            strategy = result.get('strategy', '')
            strategy_tag = "🤖 LLM 智能提取" if strategy == "llm_extraction" else "📝 模式匹配"

            reply_parts = [
                f"我已学习这段内容（{strategy_tag}）：\n",
                f"**领域**: {result.get('domain', 'generic')}",
                f"**提取模式**: {len(pids)} 个",
                f"**自动事实**: {facts_added} 条",
            ]
            if details:
                reply_parts.append("\n" + "\n".join(details[:10]))
            if extracted_facts:
                reply_parts.append(f"\n自动生成了 {len(extracted_facts)} 条事实三元组，可在「推理引擎」中查看。")
            reply = "\n".join(reply_parts)
            source = "learned"
            st.session_state.learn_log.append({
                "time": time.strftime("%H:%M:%S"),
                "source": "对话学习",
                "texts": 1, "facts": 0,
                "domain": result.get("domain", ""),
                "patterns": len(pids),
            })
        else:
            reply = "未提取到有效知识，请提供更具体的内容。"
            source = "system"

        st.session_state.messages.append({"role": "assistant", "content": reply, "source": source})
        # 存储知识依据（学习模式无额外依据）
        st.session_state["last_knowledge"] = None

    else:
        knowledge = _retrieve_knowledge(sdk, user_input)

        if knowledge["has_knowledge"]:
            st.session_state.chat_stats["grounded"] += 1
            klines = []
            if knowledge["facts"]:
                klines.append("【已学习事实】")
                for f in knowledge["facts"][:15]:
                    klines.append(f"  - {f.subject} —[{f.predicate}]→ {f.object} ({f.confidence:.0%})")
            if knowledge["patterns"]:
                klines.append("\n【已学习规则】")
                for p in knowledge["patterns"][:10]:
                    klines.append(f"  - [{p.logic_type.value}] {p.name}: {p.description}")
            if knowledge["inferences"]:
                klines.append("\n【推理结论】")
                for s in knowledge["inferences"][:10]:
                    klines.append(f"  - {s.conclusion.subject} {s.conclusion.predicate} {s.conclusion.object}")
            ktxt = "\n".join(klines)

            sys_prompt = (
                "你是集成了 Clawra 知识引擎的智能 Agent。以下是你通过学习积累的知识。\n"
                "优先使用已学习知识回答，引用具体事实和规则。\n\n"
                f"=== 知识库 ===\n{ktxt}\n=== 结束 ==="
            )
            source = "learned"
        else:
            sys_prompt = (
                "你是集成了 Clawra 知识引擎的智能 Agent。"
                "当前知识库中没有直接相关的知识。"
                "坦诚告知用户，建议用户通过'学习：[文本]'教你。"
            )
            source = "general"
            knowledge = None

        msgs = [{"role": "system", "content": sys_prompt}]
        for m in st.session_state.messages[-12:]:
            if m["role"] in ("user", "assistant"):
                msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": user_input})

        reply = run_async(_llm_chat(msgs))
        st.session_state.messages.append({"role": "assistant", "content": reply, "source": source})
        st.session_state["last_knowledge"] = knowledge


with tab_chat:
    # ── 顶部知识状态栏 (紧凑单行) ──
    _s = _get_stats()
    graph_stats = sdk.knowledge_graph.statistics() if sdk.knowledge_graph else {}
    st.markdown(
        f'<div style="padding:0.4rem 0.8rem;border-radius:8px;'
        f'background:rgba(94,106,210,0.08);border:1px solid rgba(94,106,210,0.15);'
        f'font-size:0.85rem;margin-bottom:0.5rem">'
        f'📊 <b>知识模式</b> {_s["patterns"]} &nbsp;│&nbsp; '
        f'<b>事实</b> {_s["facts"]} &nbsp;│&nbsp; '
        f'<b>图谱实体</b> {graph_stats.get("total_entities", 0)} &nbsp;│&nbsp; '
        f'<b>对话</b> {_s["queries"]} &nbsp;│&nbsp; '
        f'<b>知识增强</b> {_s["grounded"]}'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── 消息列表: 自然流式布局，内容多时页面整体滚动, chat_input 始终粘底 ──
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            source = msg.get("source", "")
            if source == "learned":
                st.caption("🟢 基于已学习知识 — 来自「自主学习」和「推理引擎」")
            elif source == "general":
                st.caption("⚪ 通用回答 — 在「自主学习」Tab 教我更多知识")

    # 知识依据 (内联在消息流末尾)
    knowledge = st.session_state.get("last_knowledge")
    if knowledge and st.session_state.messages and st.session_state.messages[-1].get("source") == "learned":
        with st.expander("📋 查看知识依据 (图谱+推理+规则)", expanded=False):
            ecol1, ecol2, ecol3 = st.columns(3)
            with ecol1:
                if knowledge.get("facts"):
                    st.markdown("**🟢 事实** (图谱)")
                    for f in knowledge["facts"][:6]:
                        st.markdown(f"- {f.subject} —[{f.predicate}]→ {f.object}")
            with ecol2:
                if knowledge.get("patterns"):
                    st.markdown("**🟡 规则** (学习)")
                    for p in knowledge["patterns"][:5]:
                        st.markdown(f"- [{p.logic_type.value}] {p.name}")
            with ecol3:
                if knowledge.get("inferences"):
                    st.markdown("**🔵 推理链**")
                    for s in knowledge["inferences"][:5]:
                        st.markdown(
                            f"- {s.conclusion.subject} {s.conclusion.predicate} "
                            f"{s.conclusion.object} ← {s.rule.name}")

    # ── 处理用户输入（来自顶层 chat_input，通过 session_state 传递） ──
    pending_input = st.session_state.pop("pending_user_input", None)
    if pending_input:
        _process_user_message(pending_input)
        safe_rerun()


# ==============================================
# Tab 2: 自主学习
# ==============================================
with tab_learn:
    st.markdown("### 📚 自主学习")
    st.info("✨ 输入文本，Agent 自动识别领域、选择策略、提取结构化知识模式。学习的知识会自动流入图谱、推理引擎和对话系统，各Tab之间实时联动。")

    learn_col, result_col = st.columns([1, 1])

    with learn_col:
        learn_text = st.text_area(
            "学习文本",
            height=200,
            placeholder="输入任意领域的文本，例如：\n燃气调压箱是一种用于降低管道压力的设备。\n如果出口压力超过安全阈值，那么必须关闭阀门。",
        )
        domain_hint = st.text_input("领域提示（可选）", placeholder="如: gas_equipment, medical")

        if st.button("🚀 开始学习", use_container_width=True, type="primary"):
            if learn_text.strip():
                with st.spinner("学习中..."):
                    result = sdk.learn(learn_text.strip(),
                                       domain_hint=domain_hint if domain_hint else None)
                st.session_state["last_learn_result"] = result
                st.session_state.learn_log.append({
                    "time": time.strftime("%H:%M:%S"),
                    "source": "手动学习",
                    "texts": 1, "facts": 0,
                    "domain": result.get("domain", ""),
                    "patterns": len(result.get("learned_patterns", [])),
                })
                safe_rerun()
            else:
                st.warning("请输入文本")

    with result_col:
        st.markdown("#### 学习结果")
        lr = st.session_state.get("last_learn_result")
        if lr:
            # 基本信息
            strategy = lr.get('strategy', 'N/A')
            strategy_label = "🤖 LLM 智能提取" if strategy == "llm_extraction" else f"📝 {strategy}"
            st.markdown(f"**领域**: `{lr.get('domain', 'generic')}` &nbsp; **策略**: {strategy_label}")
            
            pids = lr.get("learned_patterns", [])
            facts_added = lr.get("facts_added", 0)
            extracted_facts = lr.get("extracted_facts", [])
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("知识模式", len(pids))
            mc2.metric("自动事实", facts_added)
            mc3.metric("关系三元组", len(extracted_facts))
            
            # 自动生成的事实三元组
            if extracted_facts:
                with st.expander(f"🔗 自动生成的事实三元组 ({len(extracted_facts)} 条)", expanded=True):
                    for ef in extracted_facts:
                        st.markdown(
                            f"- `{ef['subject']}` —[{ef['predicate']}]→ "
                            f"`{ef['object']}` ({ef.get('confidence', 0.8):.0%})"
                        )
            
            # 提取的知识模式
            if pids:
                # 按类型分组展示
                rules = []
                definitions = []
                others = []
                for pid in pids:
                    if pid in sdk.logic_layer.patterns:
                        p = sdk.logic_layer.patterns[pid]
                        if 'rule' in pid or p.logic_type.value == 'rule':
                            rules.append(p)
                        elif 'entity' in pid or p.logic_type.value == 'behavior':
                            definitions.append(p)
                        else:
                            others.append(p)
                
                if rules:
                    with st.expander(f"⚖️ 提取的规则 ({len(rules)} 条)", expanded=True):
                        for p in rules:
                            st.markdown(f"- **{p.name}**: {p.description}")
                            st.caption(f"置信度: {p.confidence:.0%}")
                
                if definitions:
                    with st.expander(f"📖 提取的实体/定义 ({len(definitions)} 条)", expanded=False):
                        for p in definitions:
                            st.markdown(f"- **{p.name}**: {p.description}")
                
                if others:
                    with st.expander(f"📌 其他模式 ({len(others)} 条)", expanded=False):
                        for p in others:
                            st.markdown(f"- **{p.name}** `{p.logic_type.value}`: {p.description}")

            # v2.0: 知识关联视图 — 展示这次学习的知识在图谱中怎么连接
            st.markdown("---")
            st.markdown("✨ **知识关联视图**")
            st.caption("本次学习产生的知识已自动写入图谱、推理引擎和对话系统")
            assoc_col1, assoc_col2, assoc_col3 = st.columns(3)
            with assoc_col1:
                st.markdown("🟢 **图谱 → 本体图谱 Tab**")
                g_stats = sdk.knowledge_graph.statistics()
                st.caption(f"{g_stats.get('total_triples', 0)} 条三元组 / {g_stats.get('total_entities', 0)} 个实体")
            with assoc_col2:
                st.markdown("🟡 **事实 → 推理引擎 Tab**")
                st.caption(f"{len(sdk.reasoner.facts)} 条事实可用于推理")
            with assoc_col3:
                st.markdown("🔵 **模式 → Agent 对话 Tab**")
                st.caption(f"Agent 对话时会自动检索这些知识")

            # 展示关联的图谱三元组 (取最新的几条)
            domain = lr.get('domain', '')
            if domain:
                related = sdk.retrieve_knowledge(domain, top_k=5)
                if related.results:
                    with st.expander(f"🔗 图谱中 [{domain}] 相关知识 ({len(related.results)} 条)", expanded=False):
                        for r in related.results[:5]:
                            st.markdown(
                                f"- `{r.triple.subject}` —[{r.triple.predicate}]→ "
                                f"`{r.triple.object}` ({r.score:.2f})")
        else:
            st.caption("尚未执行学习 — 请在左侧输入文本并点击「开始学习」")

    # 规则发现
    st.markdown("---")
    st.markdown("#### 🔍 规则发现")
    st.caption("从已有知识中归纳新规则")

    if st.button("🔎 发现规则", use_container_width=True):
        with st.spinner("分析中..."):
            facts_dicts = [
                {"subject": f.subject, "predicate": f.predicate,
                 "object": f.object, "confidence": f.confidence}
                for f in sdk.reasoner.facts
            ]
            discovered = sdk.rule_discovery.discover_from_facts(facts_dicts) if facts_dicts else []
        if discovered:
            for r in discovered:
                st.success(f"发现规则: {r.get('name', '')} — {r.get('description', '')}")
        else:
            st.info("暂无新规则可发现。请先添加事实数据。")

    # 学习历史
    st.markdown("---")
    st.markdown("#### 📜 学习历史")
    if st.session_state.learn_log:
        for i, log in enumerate(reversed(st.session_state.learn_log), 1):
            st.markdown(
                f"**{i}.** `{log['time']}` **{log['source']}** — "
                f"{log['texts']} 段文本, {log['facts']} 条事实"
                + (f", {log.get('patterns', '?')} 个模式" if 'patterns' in log else "")
            )
    else:
        st.caption("暂无学习记录")


# ==============================================
# Tab 3: 本体图谱
# ==============================================
with tab_ontology:
    st.markdown("### 🔮 本体图谱 — Agent 的知识结构")
    st.caption("⭐ 图谱数据来自「自主学习」提取的三元组 + 「推理引擎」的结论 — 「Agent 对话」时会自动检索此图谱")

    filter_c1, filter_c2 = st.columns(2)
    with filter_c1:
        all_domains = list(sdk.logic_layer.domain_patterns.keys())
        sel_domain = st.selectbox("按领域过滤", ["全部"] + all_domains)
    with filter_c2:
        type_opts = ["全部"] + [t.value for t in LogicType]
        sel_type = st.selectbox("按逻辑类型过滤", type_opts)

    if sel_domain == "全部":
        disp_patterns = list(sdk.logic_layer.patterns.values())
    else:
        disp_patterns = sdk.logic_layer.get_patterns_by_domain(sel_domain)
    if sel_type != "全部":
        disp_patterns = [p for p in disp_patterns if p.logic_type.value == sel_type]

    graph_col, info_col = st.columns([3, 1])

    with graph_col:
        try:
            from pyvis.network import Network as PyVisNetwork

            TYPE_COLORS = {
                "rule": "#3b82f6", "behavior": "#10b981",
                "constraint": "#f59e0b", "policy": "#8b5cf6", "workflow": "#ef4444",
            }
            net = PyVisNetwork(height="520px", bgcolor="#ffffff", font_color="#1e293b")
            net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)
            nodes_added = set()
            entities_set = set()

            for p in disp_patterns:
                color = TYPE_COLORS.get(p.logic_type.value, "#6b7280")
                label = (p.name[:25] if p.name else p.id[:15])
                title = (f"类型: {p.logic_type.value}\n描述: {p.description[:80]}\n"
                         f"置信度: {p.confidence:.0%}")
                net.add_node(p.id, label=label, color=color, size=22, title=title, shape="dot")
                nodes_added.add(p.id)

                for cond in p.conditions:
                    for key in ["subject", "object"]:
                        val = cond.get(key, "")
                        if val and not val.startswith("?") and val != "true":
                            entities_set.add(val)
                            if val not in nodes_added:
                                net.add_node(val, label=val[:15], color="#94a3b8", size=14, shape="box")
                                nodes_added.add(val)
                            net.add_edge(p.id, val, label=cond.get("predicate", "")[:10],
                                         color="#cbd5e1", arrows="to")
                for act in p.actions:
                    val = act.get("object", "")
                    if val and not val.startswith("?"):
                        entities_set.add(val)
                        if val not in nodes_added:
                            net.add_node(val, label=val[:15], color="#94a3b8", size=14, shape="box")
                            nodes_added.add(val)
                        net.add_edge(p.id, val, label=act.get("predicate", "")[:10],
                                     color="#a5b4fc", arrows="to")

            # 过滤掉 _type 元数据三元组，只展示用户级事实
            user_facts = [f for f in sdk.reasoner.facts if f.predicate != "_type"]
            for fact in user_facts:
                for entity in [fact.subject, fact.object]:
                    if entity not in nodes_added:
                        net.add_node(entity, label=entity[:15], color="#fbbf24", size=12, shape="triangle")
                        nodes_added.add(entity)
                net.add_edge(fact.subject, fact.object, label=fact.predicate[:12],
                             color="#d1d5db", arrows="to")

            if nodes_added:
                graph_path = "/tmp/clawra_ontology.html"
                net.save_graph(graph_path)
                with open(graph_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                # 使用 st.components.v1.html 替代 st.html 以兼容旧版本
                import streamlit.components.v1 as components
                components.html(f'<div style="height:550px;overflow:auto;width:100%">{html_content}</div>', height=580)
            else:
                st.warning("图谱为空 — 请先加载知识。")
        except ImportError:
            st.error("请安装 pyvis: `pip install pyvis`")

    with info_col:
        st.markdown("**图例**")
        st.markdown("🔵 Rule &nbsp;🟢 Behavior")
        st.markdown("🟠 Constraint &nbsp;🟣 Policy")
        st.markdown("⬜ Entity &nbsp;🔺 Fact")
        st.markdown("---")
        st.markdown(f"逻辑节点: **{len(disp_patterns)}**")
        st.markdown(f"实体节点: **{len(entities_set)}**")
        user_facts_count = sum(1 for f in sdk.reasoner.facts if f.predicate != "_type")
        st.markdown(f"事实数: **{user_facts_count}**")

    # 知识库浏览器
    st.markdown("---")
    st.markdown("#### 📋 知识库浏览器")

    if sdk.logic_layer.patterns:
        by_domain: Dict[str, list] = {}
        for p in sdk.logic_layer.patterns.values():
            by_domain.setdefault(p.domain, []).append(p)

        for domain, patterns in by_domain.items():
            with st.expander(f"🏷️ {domain} ({len(patterns)} 个模式)"):
                for p in patterns:
                    st.markdown(f"- **{p.name}** `{p.logic_type.value}` — {p.description[:80]}")
    else:
        st.caption("知识库为空")

    # 事实三元组表格 (过滤内部元数据)
    user_facts_all = [f for f in sdk.reasoner.facts if f.predicate != "_type"]
    if user_facts_all:
        st.markdown("#### 事实三元组")
        fact_data = [
            {"主语": f.subject, "谓语": f.predicate, "宾语": f.object,
             "置信度": f"{f.confidence:.0%}"}
            for f in user_facts_all
        ]
        st.dataframe(fact_data, use_container_width=True)

    # v2.0: Graph-RAG 检索对比
    st.markdown("---")
    st.markdown("#### 🔍 Graph-RAG 检索")
    st.caption("基于知识图谱的多路召回检索，替代旧的关键词遍历")
    rag_query = st.text_input("检索查询", placeholder="例如: 燃气调压箱维护", key="rag_query")
    if rag_query:
        resp = sdk.retrieve_knowledge(rag_query)
        if resp.results:
            st.success(f"检索到 {len(resp.results)} 条相关知识")
            for r in resp.results[:10]:
                st.markdown(
                    f"- `{r.triple.subject}` —[{r.triple.predicate}]→ `{r.triple.object}` "
                    f"(得分: {r.score:.3f}, 来源: {r.source})"
                )
            # 结构化上下文
            with st.expander("📄 LLM 结构化上下文"):
                ctx = sdk.retrieve_context(rag_query)
                st.code(ctx, language="markdown")
        else:
            st.info("未检索到相关知识")


# ==============================================
# Tab 4: 推理引擎
# ==============================================
with tab_reason:
    st.markdown("### ⚙️ 推理引擎")
    st.caption("⭐ 事实来自「自主学习」Tab 和手动添加 — 推理结论自动影响「Agent 对话」的回答质量，并同步到「本体图谱」")

    fact_col, reason_col = st.columns([1, 1])

    with fact_col:
        st.markdown("#### 添加事实")
        # 自然语言录入
        nl_fact = st.text_input(
            "📝 自然语言录入",
            placeholder="例: 燃气调压箱A是一种燃气调压箱 / 调压箱A位于三号站",
            key="nl_fact_input"
        )
        if st.button("✨ 智能提取并添加", use_container_width=True, type="primary"):
            if nl_fact and nl_fact.strip():
                # 从自然语言提取主谓宾
                text = nl_fact.strip()
                result = sdk.learn(text)
                facts_extracted = result.get('extracted_facts', [])
                facts_added = result.get('facts_added', 0)
                if facts_added > 0:
                    st.success(f"✅ 从文本中提取并添加了 {facts_added} 条事实")
                    for ef in facts_extracted:
                        st.caption(f"  `{ef['subject']}` —[{ef['predicate']}]→ `{ef['object']}`")
                else:
                    st.info("未能提取出明确的事实三元组，请尝试更具体的描述")
                safe_rerun()
            else:
                st.warning("请输入文本")

        # 高级: 手动录入
        with st.expander("🔧 手动录入 (主谓宾)"):
            fc1, fc2, fc3 = st.columns(3)
            new_subj = fc1.text_input("主语", placeholder="调压箱A")
            new_pred = fc2.text_input("谓语", placeholder="is_a")
            new_obj = fc3.text_input("宾语", placeholder="燃气调压箱")
            new_conf = st.slider("置信度", 0.0, 1.0, 0.9, 0.05)
            if st.button("➕ 添加事实", use_container_width=True):
                if new_subj and new_pred and new_obj:
                    sdk.add_fact(new_subj.strip(), new_pred.strip(), new_obj.strip(), new_conf)
                    st.success(f"已添加: {new_subj} —[{new_pred}]→ {new_obj}")
                    safe_rerun()
                else:
                    st.warning("请填写完整的主语、谓语、宾语")

        st.markdown("---")
        st.markdown("#### 当前事实")
        user_reason_facts = [f for f in sdk.reasoner.facts if f.predicate != "_type"]
        if user_reason_facts:
            for f in user_reason_facts:
                st.markdown(f"- `{f.subject}` —[{f.predicate}]→ `{f.object}` ({f.confidence:.0%})")
        else:
            st.caption("暂无事实 — 输入自然语言或在「自主学习」Tab 加载知识")

    with reason_col:
        st.markdown("#### 前向链推理")
        max_depth = st.slider("推理深度", 1, 10, 3)

        if st.button("🧠 执行推理", use_container_width=True, type="primary"):
            reason_facts = [f for f in sdk.reasoner.facts if f.predicate != "_type"]
            if reason_facts:
                with st.spinner("推理中..."):
                    result = sdk.reasoner.forward_chain(max_depth=max_depth)
                st.session_state["last_inference"] = result
                safe_rerun()
            else:
                st.warning("请先添加事实")

        result = st.session_state.get("last_inference")
        if result and result.conclusions:
            st.markdown(f"**推理结论: {len(result.conclusions)} 条**")
            st.markdown("---")
            for i, step in enumerate(result.conclusions, 1):
                c = step.conclusion
                with st.container():
                    st.markdown(
                        f"**{i}.** `{c.subject}` —[{c.predicate}]→ `{c.object}`"
                    )
                    st.caption(
                        f"置信度: {step.confidence.value:.2f} | "
                        f"规则: {step.rule.name} | "
                        f"依据: {', '.join(f'{e.subject} {e.predicate} {e.object}' for e in step.matched_facts[:3])}"
                    )
        elif result:
            st.info("未推导出新结论。")

    # 知识边界检测
    st.markdown("---")
    st.markdown("#### 🔎 知识边界检测")
    st.caption("输入查询，检测知识库能否回答")
    boundary_query = st.text_input("查询", placeholder="燃气调压箱的维护周期是多少？",
                                   key="boundary_q")
    if boundary_query:
        knowledge = _retrieve_knowledge(sdk, boundary_query)
        if knowledge["has_knowledge"]:
            st.success(
                f"✅ 知识库可回答此问题 — 匹配到 {len(knowledge['facts'])} 条事实, "
                f"{len(knowledge['patterns'])} 个模式, "
                f"{len(knowledge['inferences'])} 条推理结论"
            )
        else:
            st.warning("⚠️ 知识库无法直接回答此问题 — 建议学习相关知识")


# ==============================================
# Tab 5: 评估与统计
# ==============================================
with tab_eval:
    st.markdown("### 📊 评估与统计")

    eval_tab, stat_tab, quality_tab = st.tabs(["🔬 Benchmark 评估", "📈 成长统计", "🏅 知识质量"])

    # ── Benchmark 评估 ──
    with eval_tab:
        st.caption("基于标注数据集的科学评估 — 覆盖学习率、推理准确率、检索召回率、置信度校准")

        if st.button("▶️ 运行完整 Benchmark", use_container_width=True, type="primary"):
            from eval.benchmark import ClawraBenchmark
            bench = ClawraBenchmark()
            with st.spinner("正在运行 Benchmark（学习 / 推理 / 检索 / 置信度）..."):
                report = bench.run_full_benchmark()
            st.session_state["bench_report"] = report
            safe_rerun()

        report = st.session_state.get("bench_report")
        if report:
            # 综合评分
            score = report.overall_score
            st.markdown(f"#### 综合评分: **{score:.1%}**")
            st.progress(min(score, 1.0))

            # 四维指标
            bc1, bc2, bc3, bc4 = st.columns(4)
            if report.learning:
                bc1.metric("学习率",
                           f"{report.learning.extraction_rate:.1f}",
                           delta="目标≥2.0")
            if report.reasoning:
                bc2.metric("推理准确率",
                           f"{report.reasoning.accuracy:.0%}",
                           delta="目标≥85%")
            if report.retrieval:
                bc3.metric("检索召回率",
                           f"{report.retrieval.recall:.0%}",
                           delta="目标≥50%")
            if report.confidence:
                bc4.metric("校准误差 (ECE)",
                           f"{report.confidence.calibration_error:.3f}",
                           delta="目标≤0.15", delta_color="inverse")

            # 详情
            if report.learning:
                with st.expander("📊 学习评估详情"):
                    st.markdown(f"- 提取率: {report.learning.extraction_rate:.2f}")
                    st.markdown(f"- 覆盖度: {report.learning.coverage:.1%}")
                    st.markdown(f"- 事实生成率: {report.learning.fact_generation_rate:.2f} 条/段")
                    st.markdown(f"- 测试文本: {report.learning.total_texts}")
                    if report.learning.per_text_results:
                        for r in report.learning.per_text_results:
                            icon = "✅" if r["extracted"] > 0 else "❌"
                            facts_info = f", 事实 {r.get('facts_generated', 0)}" if r.get('facts_generated') else ""
                            st.markdown(f"  {icon} `{r['id']}` — 提取 {r['extracted']} / 预期 {r['expected']}{facts_info}")

            if report.reasoning:
                with st.expander("📊 推理评估详情"):
                    rr = report.reasoning
                    st.markdown(f"- 准确率: {rr.accuracy:.1%}")
                    st.markdown(f"- 精确率: {rr.precision:.1%}")
                    st.markdown(f"- 召回率: {rr.recall:.1%}")
                    st.markdown(f"- F1: {rr.f1:.2f}")

            if report.retrieval:
                with st.expander("📊 检索评估详情"):
                    rt = report.retrieval
                    st.markdown(f"- 精确率: {rt.precision:.1%}")
                    st.markdown(f"- 召回率: {rt.recall:.1%}")
                    st.markdown(f"- F1: {rt.f1:.2f}")

            if report.confidence:
                with st.expander("📊 置信度校准详情"):
                    cc = report.confidence
                    st.markdown(f"- ECE: {cc.calibration_error:.4f}")
                    if cc.bin_results:
                        st.markdown("**分桶校准:**")
                        for b in cc.bin_results:
                            st.markdown(
                                f"  - 区间 {b['bin']}: 平均置信 {b['avg_confidence']:.2f}, "
                                f"实际准确 {b['avg_accuracy']:.1%} (n={b['count']})")

            st.markdown(f"*评估耗时: {report.duration:.2f}s*")
        else:
            st.info("点击「运行完整 Benchmark」开始评估")

    # ── 成长统计 ──
    with stat_tab:
        stats = _get_stats()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("知识模式", stats["patterns"])
        m2.metric("事实数", stats["facts"])
        grounded_pct = (stats["grounded"] / max(stats["queries"], 1)) * 100
        m3.metric("知识命中率", f"{grounded_pct:.0f}%")
        m4.metric("覆盖领域", stats["domains"])

        st.markdown("---")
        left, right = st.columns(2)

        with left:
            st.markdown("#### 领域覆盖")
            if stats["domain_list"]:
                for domain, count in stats["domain_list"].items():
                    st.progress(min(count / 10, 1.0), text=f"{domain}: {count} 个模式")
            else:
                st.info("暂无领域数据")

            st.markdown("---")
            st.markdown("#### 知识类型分布")
            for t_name, t_count in stats.get("by_type", {}).items():
                if t_count > 0:
                    st.markdown(f"- **{t_name}**: {t_count}")

        with right:
            st.markdown("#### 学习策略效果")
            strategy_stats = stats["learning"].get("strategy_effectiveness", {})
            if strategy_stats:
                for strategy, eff in strategy_stats.items():
                    attempts = eff.get("attempts", 0)
                    if attempts > 0:
                        rate = eff.get("successes", 0) / attempts
                        st.markdown(f"- **{strategy}**: {rate:.0%} 成功率 ({attempts} 次)")
            else:
                st.info("暂无策略数据")

            st.markdown("---")
            st.markdown("#### 知识导出")
            if st.button("📤 导出知识", use_container_width=True):
                export_json = sdk.export_knowledge()
                st.download_button(
                    "💾 下载 JSON",
                    data=export_json,
                    file_name="clawra_knowledge.json",
                    mime="application/json",
                    use_container_width=True,
                )

    # ── v2.0: 知识质量评估 ──
    with quality_tab:
        st.caption("知识图谱多维质量评估 + 生命周期管理 + 反馈闭环")

        if st.button("▶️ 运行知识质量评估", use_container_width=True, type="primary", key="eval_quality"):
            with st.spinner("评估中..."):
                eval_result = sdk.evaluate_knowledge()
            st.session_state["quality_result"] = eval_result
            safe_rerun()

        qr = st.session_state.get("quality_result")
        if qr:
            q1, q2, q3, q4 = st.columns(4)
            q1.metric("评估知识数", qr.get("total_evaluated", 0))
            q2.metric("综合均分", f"{qr.get('avg_overall', 0):.2f}")
            q3.metric("一致性", f"{qr.get('avg_consistency', 0):.2f}")
            q4.metric("低质量数", qr.get("low_quality_count", 0))

            lc1, lc2 = st.columns(2)
            with lc1:
                st.markdown("#### 生命周期变更")
                changes = qr.get("lifecycle_changes", 0)
                if changes > 0:
                    st.success(f"本轮 {changes} 条知识状态变更")
                    lc_summary = sdk.evaluator.get_lifecycle_summary()
                    for evt in lc_summary.get("recent_events", []):
                        st.markdown(f"- `{evt['triple_id'][:16]}` {evt['change']}")
                else:
                    st.info("本轮无状态变更")

            with lc2:
                st.markdown("#### 置信度衰减")
                decayed = qr.get("confidence_decayed", 0)
                st.metric("受影响三元组", decayed)

            # 知识图谱统计
            st.markdown("---")
            st.markdown("#### 知识图谱概览")
            graph_stats = sdk.knowledge_graph.statistics() if sdk.knowledge_graph else {}
            if graph_stats:
                gs1, gs2, gs3, gs4 = st.columns(4)
                gs1.metric("三元组总数", graph_stats.get("total_triples", 0))
                gs2.metric("实体数", graph_stats.get("total_entities", 0))
                gs3.metric("谓词类型", graph_stats.get("total_predicates", 0))
                gs4.metric("平均置信度", f"{graph_stats.get('avg_confidence', 0):.2f}")

                status_dist = graph_stats.get("status_distribution", {})
                if status_dist:
                    st.markdown("**状态分布:**")
                    for status, count in status_dist.items():
                        st.markdown(f"- {status}: {count}")
        else:
            st.info("点击「运行知识质量评估」开始")
