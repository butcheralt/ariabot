"""
Configuration management for the portable chatbot.
Handles loading, validation, and management of bot settings.
"""

import json
import os
from typing import Dict, Any, Optional

class Config:
    """Manages chatbot configuration from config.json file."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file '{self.config_path}' not found. Run setup.py first.")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['bot_name', 'bot_instructions', 'api_provider', 'model']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Required field '{field}' missing from config.")
            
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    @property
    def bot_name(self) -> str:
        """Get bot name."""
        return self.get('bot_name', 'Assistant')
    
    @property
    def bot_instructions(self) -> str:
        """Get bot instructions/system prompt."""
        return self.get('bot_instructions', 'You are a helpful assistant.')
    
    @property
    def api_provider(self) -> str:
        """Get API provider name."""
        return self.get('api_provider', 'openai')
    
    @property
    def model(self) -> str:
        """Get model name."""
        return self.get('model', 'gpt-3.5-turbo')
    
    @property
    def api_key(self) -> str:
        """Get API key."""
        # Try to get from config first, then environment
        key = self.get('api_key', '')
        if not key:
            # Try common environment variable names
            provider = self.api_provider.upper()
            env_names = [
                f"{provider}_API_KEY",
                f"{provider}API_KEY",
                "API_KEY"
            ]
            for env_name in env_names:
                key = os.getenv(env_name, '')
                if key:
                    break
        
        return key
    
    @property
    def temperature(self) -> float:
        """Get temperature setting."""
        return float(self.get('temperature', 0.7))
    
    @property
    def max_tokens(self) -> int:
        """Get max tokens setting."""
        return int(self.get('max_tokens', 150))
    
    def validate(self) -> list:
        """Validate configuration and return list of issues."""
        issues = []
        
        if not self.api_key:
            issues.append(f"No API key found for {self.api_provider}. Set it in config.json or environment variable.")
        
        if self.temperature < 0 or self.temperature > 2:
            issues.append("Temperature should be between 0 and 2.")
        
        if self.max_tokens < 1:
            issues.append("Max tokens should be greater than 0.")
        
        return issues
    
    def __str__(self) -> str:
        """String representation of config."""
        return (f"Config(bot_name='{self.bot_name}', provider='{self.api_provider}', "
                f"model='{self.model}', temperature={self.temperature})")