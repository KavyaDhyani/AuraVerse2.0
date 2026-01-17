"""Configuration for signaling server."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Server configuration."""
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # CORS settings
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '*')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
