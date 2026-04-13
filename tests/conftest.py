"""
pytest 配置：自动将调用真实 LLM 的测试标记为 integration
"""
import pytest


def pytest_collection_modifyitems(config, items):
    """
    自动检测并标记调用真实 LLM 的测试。
    
    这些测试在没有 mock 的情况下会调 VolcEngine API，
    容易超时不稳定。默认跳过，保持 CI 稳定。
    """
    integration_files = {
        "test_meta_learner.py",      # test_learn_from_text 等调 LLM
        "test_clawra.py",            # test_learn_from_text 等调 LLM
        "test_sdk_hardening.py",     # 所有测试都调 SDK
        "test_benchmark.py",         # benchmark 调 LLM 评估
        "test_end_to_end.py",        # 端到端流程调 LLM
        "test_v2_modules.py",        # test_full_pipeline 等调 LLM
        "test_deep_integration.py",  # glossary_engine 调 LLM
    }
    
    for item in items:
        path_str = str(item.fspath)
        for fname in integration_files:
            if path_str.endswith(fname):
                item.add_marker(pytest.mark.integration)
                break
