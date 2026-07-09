"""Application configuration.

Values are read from the environment so the same image can run in different
deployments. Sensible defaults are provided for local development.
"""
import os

JWT_SECRET = os.getenv("JWT_SECRET", "cowork-dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "900"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cowork.db")
