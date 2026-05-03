from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class LLMPlatform(Enum):
    OPENAI = "openai"
    NVIDIA_NIM = "nvidia_nim"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    CUSTOM_OPENAI_COMPATIBLE = "custom_openai_compatible"


@dataclass
class LLMConfig:
    platform: LLMPlatform = LLMPlatform.OPENAI
    api_key: str = ""
    model_name: str = "gpt-3.5-turbo"
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: int = 60
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "api_key": self.api_key,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "extra_params": self.extra_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        platform = LLMPlatform(data.get("platform", "openai"))
        return cls(
            platform=platform,
            api_key=data.get("api_key", ""),
            model_name=data.get("model_name", "gpt-3.5-turbo"),
            base_url=data.get("base_url"),
            temperature=data.get("temperature", 0.0),
            max_tokens=data.get("max_tokens", 4096),
            timeout=data.get("timeout", 60),
            extra_params=data.get("extra_params", {})
        )


PRESET_MODELS = {
    LLMPlatform.OPENAI: [
        {"name": "gpt-3.5-turbo", "description": "GPT-3.5 Turbo (快速、经济)"},
        {"name": "gpt-4", "description": "GPT-4 (高性能)"},
        {"name": "gpt-4-turbo", "description": "GPT-4 Turbo (最新)"},
        {"name": "gpt-4o", "description": "GPT-4o (多模态)"},
    ],
    LLMPlatform.NVIDIA_NIM: [
        {"name": "qwen3.5-397b-a17b", "description": "通义千问3.5 397B-A17B"},
        {"name": "qwen2.5-72b-instruct", "description": "通义千问2.5 72B"},
        {"name": "llama3.1-70b-instruct", "description": "Llama 3.1 70B"},
        {"name": "mistral-large-2-instruct", "description": "Mistral Large 2"},
        {"name": "deepseek-v3", "description": "DeepSeek V3"},
    ],
    LLMPlatform.QWEN: [
        {"name": "qwen-max", "description": "通义千问 Max"},
        {"name": "qwen-plus", "description": "通义千问 Plus"},
        {"name": "qwen-turbo", "description": "通义千问 Turbo"},
        {"name": "qwen2.5-72b-instruct", "description": "Qwen 2.5 72B"},
    ],
    LLMPlatform.DEEPSEEK: [
        {"name": "deepseek-chat", "description": "DeepSeek Chat"},
        {"name": "deepseek-coder", "description": "DeepSeek Coder"},
    ],
    LLMPlatform.CUSTOM_OPENAI_COMPATIBLE: [
        {"name": "custom", "description": "自定义模型名称"},
    ],
}

PLATFORM_BASE_URLS = {
    LLMPlatform.OPENAI: "https://api.openai.com/v1",
    LLMPlatform.NVIDIA_NIM: "https://integrate.api.nvidia.com/v1",
    LLMPlatform.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    LLMPlatform.DEEPSEEK: "https://api.deepseek.com/v1",
    LLMPlatform.CUSTOM_OPENAI_COMPATIBLE: None,
}

PLATFORM_DISPLAY_NAMES = {
    LLMPlatform.OPENAI: "OpenAI",
    LLMPlatform.NVIDIA_NIM: "Nvidia NIM",
    LLMPlatform.QWEN: "阿里云 Qwen",
    LLMPlatform.DEEPSEEK: "DeepSeek",
    LLMPlatform.CUSTOM_OPENAI_COMPATIBLE: "自定义 (OpenAI兼容)",
}


class LLMConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.configs: Dict[str, LLMConfig] = {}
        self.active_config_name: str = "default"
        self._load_configs()
    
    def _get_default_config_path(self) -> str:
        user_home = os.path.expanduser("~")
        config_dir = os.path.join(user_home, ".text2sql")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "llm_configs.json")
    
    def _load_configs(self):
        if not os.path.exists(self.config_path):
            self.configs = {
                "default": LLMConfig()
            }
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.active_config_name = data.get("active", "default")
            
            configs_data = data.get("configs", {})
            self.configs = {}
            for name, config_data in configs_data.items():
                self.configs[name] = LLMConfig.from_dict(config_data)
            
            if not self.configs:
                self.configs["default"] = LLMConfig()
        
        except Exception as e:
            print(f"加载LLM配置失败: {str(e)}")
            self.configs = {"default": LLMConfig()}
    
    def _save_configs(self):
        try:
            data = {
                "active": self.active_config_name,
                "configs": {}
            }
            
            for name, config in self.configs.items():
                data["configs"][name] = config.to_dict()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"保存LLM配置失败: {str(e)}")
    
    def get_active_config(self) -> LLMConfig:
        return self.configs.get(self.active_config_name, LLMConfig())
    
    def set_active_config(self, name: str):
        if name in self.configs:
            self.active_config_name = name
            self._save_configs()
    
    def get_config_names(self) -> List[str]:
        return list(self.configs.keys())
    
    def get_config(self, name: str) -> Optional[LLMConfig]:
        return self.configs.get(name)
    
    def add_config(self, name: str, config: LLMConfig):
        self.configs[name] = config
        self._save_configs()
    
    def update_config(self, name: str, config: LLMConfig):
        if name in self.configs:
            self.configs[name] = config
            self._save_configs()
    
    def delete_config(self, name: str) -> bool:
        if name in self.configs and name != "default":
            del self.configs[name]
            if self.active_config_name == name:
                self.active_config_name = "default"
            self._save_configs()
            return True
        return False
    
    def get_preset_models(self, platform: LLMPlatform) -> List[Dict[str, str]]:
        return PRESET_MODELS.get(platform, [])
    
    def get_platform_base_url(self, platform: LLMPlatform) -> Optional[str]:
        return PLATFORM_BASE_URLS.get(platform)
    
    def get_platform_display_name(self, platform: LLMPlatform) -> str:
        return PLATFORM_DISPLAY_NAMES.get(platform, platform.value)


def create_llm_client(config: LLMConfig):
    try:
        from langchain_openai import ChatOpenAI
        
        base_url = config.base_url
        if not base_url:
            base_url = PLATFORM_BASE_URLS.get(config.platform)
        
        client_kwargs = {
            "model": config.model_name,
            "temperature": config.temperature,
            "api_key": config.api_key,
            "timeout": config.timeout,
        }
        
        if base_url:
            client_kwargs["base_url"] = base_url
        
        if config.max_tokens:
            client_kwargs["max_tokens"] = config.max_tokens
        
        client_kwargs.update(config.extra_params)
        
        return ChatOpenAI(**client_kwargs)
    
    except ImportError:
        raise ImportError("请安装 langchain-openai 库: pip install langchain-openai")
