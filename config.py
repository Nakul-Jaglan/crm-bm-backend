import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./data/crm_production.sqlite3"
    )
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bonhoeffer-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://localhost:3000")
    
    # CORS Origins
    @property
    def CORS_ORIGINS(self) -> list:
        if self.ENVIRONMENT == "production":
            return [
                "http://localhost:3000",  # Keep for local testing
                "http://127.0.0.1:3000",
                self.FRONTEND_URL,
                "https://*.vercel.app",
                "https://crm.nakul.click",
            ]
        else:
            return [
                "http://localhost:3000", 
                "http://127.0.0.1:3000",
                "https://crm.nakul.click",
                "https://*.vercel.app",
                "https://*.ngrok.io",
                "https://*.ngrok-free.app"
            ]
    
    # Email (for notifications)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
