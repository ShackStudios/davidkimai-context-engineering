"""Configuration management for the context engineering framework."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from .logger import Logger


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    name: str = "claude-3-sonnet-20241022"
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 0.9
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    

@dataclass
class AgentConfig:
    """Configuration for agents."""
    max_context_length: int = 100000
    memory_enabled: bool = True
    logging_enabled: bool = True
    auto_save: bool = True
    save_interval: int = 300  # seconds
    

@dataclass
class SystemConfig:
    """System-wide configuration."""
    debug_mode: bool = False
    log_level: str = "INFO"
    data_dir: str = "data"
    temp_dir: str = "temp"
    max_concurrent_agents: int = 10
    

@dataclass
class FrameworkConfig:
    """Main framework configuration."""
    model: ModelConfig = field(default_factory=ModelConfig)
    agent: AgentConfig = field(default_factory=AgentConfig) 
    system: SystemConfig = field(default_factory=SystemConfig)
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Manages configuration for the context engineering framework."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else Path("config.yaml")
        self.logger = Logger("ConfigManager")
        self.config = FrameworkConfig()
        
        if self.config_path.exists():
            self.load_config()
        else:
            self.save_config()  # Create default config
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> FrameworkConfig:
        """Load configuration from file."""
        if config_path:
            self.config_path = Path(config_path)
        
        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            # Update config from loaded data
            self.config = self._dict_to_config(data)
            self.logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {e}")
            self.logger.info("Using default configuration")
        
        return self.config
    
    def save_config(self, config_path: Optional[Union[str, Path]] = None):
        """Save configuration to file."""
        if config_path:
            self.config_path = Path(config_path)
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = self._config_to_dict(self.config)
            
            with open(self.config_path, 'w') as f:
                if self.config_path.suffix.lower() == '.json':
                    json.dump(data, f, indent=2)
                else:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config to {self.config_path}: {e}")
    
    def _config_to_dict(self, config: FrameworkConfig) -> Dict[str, Any]:
        """Convert config dataclass to dictionary."""
        return {
            'model': {
                'name': config.model.name,
                'max_tokens': config.model.max_tokens,
                'temperature': config.model.temperature,
                'top_p': config.model.top_p,
                'api_key': config.model.api_key,
                'base_url': config.model.base_url
            },
            'agent': {
                'max_context_length': config.agent.max_context_length,
                'memory_enabled': config.agent.memory_enabled,
                'logging_enabled': config.agent.logging_enabled,
                'auto_save': config.agent.auto_save,
                'save_interval': config.agent.save_interval
            },
            'system': {
                'debug_mode': config.system.debug_mode,
                'log_level': config.system.log_level,
                'data_dir': config.system.data_dir,
                'temp_dir': config.system.temp_dir,
                'max_concurrent_agents': config.system.max_concurrent_agents
            },
            'custom': config.custom
        }
    
    def _dict_to_config(self, data: Dict[str, Any]) -> FrameworkConfig:
        """Convert dictionary to config dataclass."""
        config = FrameworkConfig()
        
        if 'model' in data:
            model_data = data['model']
            config.model = ModelConfig(
                name=model_data.get('name', config.model.name),
                max_tokens=model_data.get('max_tokens', config.model.max_tokens),
                temperature=model_data.get('temperature', config.model.temperature),
                top_p=model_data.get('top_p', config.model.top_p),
                api_key=model_data.get('api_key'),
                base_url=model_data.get('base_url')
            )
        
        if 'agent' in data:
            agent_data = data['agent']
            config.agent = AgentConfig(
                max_context_length=agent_data.get('max_context_length', config.agent.max_context_length),
                memory_enabled=agent_data.get('memory_enabled', config.agent.memory_enabled),
                logging_enabled=agent_data.get('logging_enabled', config.agent.logging_enabled),
                auto_save=agent_data.get('auto_save', config.agent.auto_save),
                save_interval=agent_data.get('save_interval', config.agent.save_interval)
            )
        
        if 'system' in data:
            system_data = data['system']
            config.system = SystemConfig(
                debug_mode=system_data.get('debug_mode', config.system.debug_mode),
                log_level=system_data.get('log_level', config.system.log_level),
                data_dir=system_data.get('data_dir', config.system.data_dir),
                temp_dir=system_data.get('temp_dir', config.system.temp_dir),
                max_concurrent_agents=system_data.get('max_concurrent_agents', config.system.max_concurrent_agents)
            )
        
        config.custom = data.get('custom', {})
        
        return config
    
    def get_config(self) -> FrameworkConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        # Simple nested update - could be made more sophisticated
        for key, value in updates.items():
            if hasattr(self.config, key):
                if isinstance(value, dict) and hasattr(getattr(self.config, key), '__dict__'):
                    for sub_key, sub_value in value.items():
                        setattr(getattr(self.config, key), sub_key, sub_value)
                else:
                    setattr(self.config, key, value)
        
        self.logger.info(f"Configuration updated: {updates}")
        self.save_config()
    
    def get_model_config(self) -> ModelConfig:
        """Get model configuration."""
        return self.config.model
    
    def get_agent_config(self) -> AgentConfig:
        """Get agent configuration."""
        return self.config.agent
    
    def get_system_config(self) -> SystemConfig:
        """Get system configuration."""
        return self.config.system
