import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database - Use SQLite for Vercel
    DATABASE_URL: str = "sqlite:///./crm_db.sqlite"
    
    # JWT
    SECRET_KEY: str = "bonhoeffer-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://crm.nakul.click",  # Your frontend domain
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
