import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-please")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://aqsamaharvi12:woxhi7-Rovrot-zaqron@book-of-h.f5shlpc.mongodb.net/")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "hgram_db")


settings = Settings()

