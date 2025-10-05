"""
AI Provider abstraction layer for the portable chatbot.
Supports multiple AI providers through a unified interface.
"""

import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from config_manager import Config

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.api_key
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages and return response."""
        pass
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate provider-specific configuration."""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages to OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate OpenAI configuration."""
        issues = []
        if not self.api_key:
            issues.append("OpenAI API key is required")
        
        valid_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo-16k"]
        if self.model not in valid_models:
            issues.append(f"Model '{self.model}' may not be valid for OpenAI")
        
        return issues

class AnthropicProvider(AIProvider):
    """Anthropic API provider."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages to Anthropic API."""
        try:
            # Convert messages to Anthropic format
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                system=system_message,
                messages=user_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate Anthropic configuration."""
        issues = []
        if not self.api_key:
            issues.append("Anthropic API key is required")
        
        valid_models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        if self.model not in valid_models:
            issues.append(f"Model '{self.model}' may not be valid for Anthropic")
        
        return issues

class CohereProvider(AIProvider):
    """Cohere API provider."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        try:
            import cohere
            self.client = cohere.Client(self.api_key)
        except ImportError:
            raise ImportError("Cohere package not installed. Run: pip install cohere")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages to Cohere API."""
        try:
            # Convert messages to chat history
            chat_history = []
            message_text = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    continue  # Cohere handles system message differently
                elif msg["role"] == "user":
                    message_text = msg["content"]
                elif msg["role"] == "assistant":
                    chat_history.append({
                        "role": "CHATBOT",
                        "message": msg["content"]
                    })
            
            response = self.client.chat(
                model=self.model,
                message=message_text,
                chat_history=chat_history,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.text
        except Exception as e:
            raise Exception(f"Cohere API error: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate Cohere configuration."""
        issues = []
        if not self.api_key:
            issues.append("Cohere API key is required")
        
        valid_models = ["command", "command-light", "command-nightly"]
        if self.model not in valid_models:
            issues.append(f"Model '{self.model}' may not be valid for Cohere")
        
        return issues

class OllamaProvider(AIProvider):
    """Ollama local API provider."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.base_url = config.get('ollama_url', 'http://localhost:11434')
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages to Ollama API."""
        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate Ollama configuration."""
        issues = []
        try:
            # Test connection to Ollama
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()  # Fixed: Added parentheses to actually call the method
        except requests.exceptions.RequestException:
            issues.append(f"Cannot connect to Ollama at {self.base_url}")
        
        return issues

class GroqProvider(AIProvider):
    """Groq API provider - Ultra-fast inference."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        try:
            import groq
            self.client = groq.Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError("Groq package not installed. Run: pip install groq")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages to Groq API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate Groq configuration."""
        issues = []
        if not self.api_key:
            issues.append("Groq API key is required")
        
        # Updated with actual Groq models from their documentation
        valid_models = [
            "groq/compound",                                    # Recommended: No limit
            "groq/compound-mini",                               # Fast: No limit
            "llama-3.3-70b-versatile",                         # LLaMA 3.3 70B
            "llama-3.1-8b-instant",                            # Fast: 500K daily
            "gemma2-9b-it",                                    # Google Gemma2
            "deepseek-r1-distill-llama-70b",                  # DeepSeek reasoning
            "meta-llama/llama-4-maverick-17b-128e-instruct",  # LLaMA 4 Maverick
            "meta-llama/llama-4-scout-17b-16e-instruct",      # LLaMA 4 Scout
            "openai/gpt-oss-120b",                            # GPT OSS 120B
            "openai/gpt-oss-20b",                             # GPT OSS 20B
            "qwen/qwen3-32b",                                 # Qwen3 32B
            "moonshotai/kimi-k2-instruct",                    # Kimi K2
            "moonshotai/kimi-k2-instruct-0905",              # Kimi K2 (0905)
        ]
        
        # Don't show warning for valid models, just log info
        if self.model not in valid_models:
            # Note: User can still use custom models, just inform them
            issues.append(f"Note: Model '{self.model}' not in common list. If it's a new Groq model, ignore this message.")
        
        return issues

class ProviderFactory:
    """Factory class to create AI providers."""
    
    PROVIDERS = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'cohere': CohereProvider,
        'ollama': OllamaProvider,
        'groq': GroqProvider
    }
    
    @classmethod
    def create_provider(cls, config: Config) -> AIProvider:
        """Create an AI provider based on configuration."""
        provider_name = config.api_provider.lower()
        
        if provider_name not in cls.PROVIDERS:
            available = ', '.join(cls.PROVIDERS.keys())
            raise ValueError(f"Unknown provider '{provider_name}'. Available: {available}")
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider names."""
        return list(cls.PROVIDERS.keys())