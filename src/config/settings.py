import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables or use defaults
class Settings:
    # MongoDB Settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ai_twitter_bot")
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # WebSocket Server Settings
    WS_HOST: str = os.getenv("WS_HOST", "localhost")
    WS_PORT: int = int(os.getenv("WS_PORT", "8765"))
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))
    
    # System Settings
    SYSTEM_CHECK_INTERVAL: int = int(os.getenv("SYSTEM_CHECK_INTERVAL", "60"))  # seconds
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        required_settings = [
            "MONGODB_URL",
            "OPENAI_API_KEY"
        ]
        
        for setting in required_settings:
            value = getattr(cls, setting)
            if not value:
                raise ValueError(f"Missing required setting: {setting}")
            if setting == "OPENAI_API_KEY":
                print(f"API Key loaded (first 10 chars): {value[:10]}...")
        
        return True

# Create settings instance
settings = Settings()
settings.validate()  # Validate on import 