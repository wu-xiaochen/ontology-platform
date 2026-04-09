"""
配置管理测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.utils.config import (
    ConfigManager, LLMConfig, DatabaseConfig, AppConfig, 
    GraphRAGConfig, AgentToolConfig, LLMFallbackConfig,
    validate_config, get_config
)


class TestConfigManager:
    """配置管理器测试"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2
    
    def test_llm_config_defaults(self):
        """测试 LLM 配置默认值"""
        config = LLMConfig()
        # 检查配置值不为空（从环境变量读取）
        assert config.base_url is not None
        assert config.model is not None
        # 验证默认值（温度和最大 token 从环境变量或默认值）
        assert config.temperature >= 0 and config.temperature <= 2
        assert config.max_tokens > 0
        # 验证新增的重试配置
        assert config.max_retries >= 0
        assert config.retry_delay >= 0
    
    def test_llm_config_is_configured(self):
        """测试 LLM 配置检查"""
        # 未配置
        config = LLMConfig(api_key="")
        assert not config.is_configured()
        
        # mock key（现在检查 'mock' 和 'your_api_key_here' 都视为未配置）
        config = LLMConfig(api_key="mock")
        assert not config.is_configured()
        
        config = LLMConfig(api_key="your_api_key_here")
        assert not config.is_configured()
        
        # 已配置
        config = LLMConfig(api_key="sk-test123", skip_llm=False)
        assert config.is_configured()
    
    def test_database_config_defaults(self):
        """测试数据库配置默认值"""
        config = DatabaseConfig()
        # 检查配置值不为空（从环境变量读取）
        assert config.neo4j_uri is not None
        assert config.neo4j_user is not None
        assert config.neo4j_password is not None
    
    def test_database_config_is_configured(self):
        """测试数据库配置检查"""
        # 完整配置
        config = DatabaseConfig(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password"
        )
        assert config.is_configured()
        
        # 缺少密码
        config = DatabaseConfig(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password=""
        )
        assert not config.is_configured()
    
    def test_app_config_defaults(self):
        """测试应用配置默认值"""
        config = AppConfig()
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.data_dir == "./data"
        assert config.max_learning_episodes == 10000
    
    def test_config_validation(self):
        """测试配置验证"""
        config = ConfigManager()
        
        # 设置未配置的 LLM
        config.llm.api_key = ""
        
        result = config.validate()
        
        # 应该无效（缺少 API key）
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("API Key" in e for e in result["errors"])
    
    def test_config_to_dict(self):
        """测试配置导出为字典"""
        config = ConfigManager()
        config.llm.api_key = "sk-secret"  # 敏感信息
        
        data = config.to_dict()
        
        # 敏感信息不应包含
        assert "api_key" not in data["llm"]
        assert "configured" in data["llm"]
        assert "app" in data
        assert "database" in data
        # 验证新增的配置模块
        assert "graphrag" in data
        assert "agent_tools" in data
        assert "llm_fallback" in data
    
    def test_config_save_and_load(self, tmp_path):
        """测试配置保存和加载"""
        config = ConfigManager()
        config_file = tmp_path / "config.json"
        
        # 保存
        config.save_to_file(str(config_file))
        assert config_file.exists()
        
        # 验证文件内容
        import json
        with open(config_file, 'r') as f:
            data = json.load(f)
            assert "llm" in data
            assert "app" in data


class TestEnvironmentVariables:
    """环境变量测试"""
    
    def test_env_var_loading(self, monkeypatch):
        """测试环境变量加载"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo")
        monkeypatch.setenv("DEBUG", "true")
        
        # 创建新实例会读取环境变量
        config = LLMConfig()
        assert config.api_key == "test-key"
        assert config.model == "gpt-3.5-turbo"
        
        app_config = AppConfig()
        assert app_config.debug is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
