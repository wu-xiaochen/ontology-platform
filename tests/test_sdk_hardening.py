import pytest
from src.sdk import ClawraSDK


@pytest.fixture
def sdk():
    """每个测试独立的 SDK 实例"""
    s = ClawraSDK(enable_memory=False)
    yield s
    # 清理
    s = None


class TestSDKHardening:
    """SDK 硬化测试 — 确保关键 API 稳定可用"""

    def test_learn_and_reason_v4(self, sdk):
        """测试 v4.0 的 learn 与 reason (真实调用 orchestrate)"""
        sdk.learn("燃气调压器是燃气设备。")
        sdk.learn("燃气设备是工业资产。")

        result = sdk.reason("什么是燃气调压器？")

        assert "trace" in result
        assert "conclusions" in result
        assert len(result["trace"]) >= 3
        print(f"Thinking Trace: {result['trace']}")

    def test_export_graph(self, sdk):
        """测试 D3 图数据导出"""
        sdk.learn("A 是 B")
        data = sdk.get_graph_data()

        assert "nodes" in data
        assert "links" in data
        assert any(node["id"] == "A" for node in data["nodes"])

    @pytest.mark.asyncio
    async def test_evolve_v4(self):
        """测试进化闭环回调"""
        sdk = ClawraSDK(enable_memory=False)
        result = await sdk.evolve()
        assert result["status"] == "success"
        assert "results" in result
        print(f"Evolve Result: {result}")
