"""Configuration management for the AI Assistant."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration manager for the AI Assistant."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / "config" / "settings.yaml"
        self._settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_settings()
    
    def _default_settings(self) -> Dict[str, Any]:
        """Return default settings if config file is missing."""
        return {
            "assistant": {
                "name": "Personal AI Assistant",
                "version": "1.0.0",
                "max_tokens": 2000,
                "temperature": 0.7
            },
            "integrations": {
                "gmail": {"enabled": True, "cache_duration": 300},
                "calendar": {"enabled": True, "cache_duration": 300},
                "github": {"enabled": True, "cache_duration": 600},
                "trello": {"enabled": False, "cache_duration": 600}
            },
            "ui": {
                "theme": "dark",
                "show_icons": True,
                "max_lines": 20
            }
        }
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        return os.getenv("OPENAI_API_KEY", "")
    
    @property
    def google_client_id(self) -> str:
        """Get Google Client ID from environment."""
        return os.getenv("GOOGLE_CLIENT_ID", "")
    
    @property
    def google_client_secret(self) -> str:
        """Get Google Client Secret from environment."""
        return os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    @property
    def github_token(self) -> str:
        """Get GitHub token from environment."""
        return os.getenv("GITHUB_TOKEN", "")
    
    @property
    def trello_api_key(self) -> str:
        """Get Trello API key from environment."""
        return os.getenv("TRELLO_API_KEY", "")
    
    @property
    def trello_token(self) -> str:
        """Get Trello token from environment."""
        return os.getenv("TRELLO_TOKEN", "")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def assistant_name(self) -> str:
        """Get assistant name."""
        return self.get("assistant.name", "Personal AI Assistant")
    
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return os.getenv("DEBUG", "False").lower() == "true"

# Global configuration instance
config = Config() 