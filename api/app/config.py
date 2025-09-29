from pydantic_settings import BaseSettings


class Config(BaseSettings):
    SECRET_KEY: str
    SESSION_NAME_KEY: str
    FERNET_KEY: str
    CSRF_SCRIPT_NAME: str
    SQLALCHEMY_DATABASE_URI: str
    CLUB_ID: int
    CLUB_NAME: str
    COURSE_ID: int
    CACHE_TYPE: str = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT: int = 300
    PROXY_URL: str
    PROXY_LOGIN: str
    PROXY_LOGOUT: str
    PROXY_HOME: str
    PROXY_SEARCH: str
    PROXY_PEOPLE: str
    PROXY_RESERVE: str
    PROXY_REFERER: str
    SOURCE: str
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    REQUEST_TIMEOUT: int = 10
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str
    SQLALCHEMY_ENGINE_OPTIONS: dict = {"pool_pre_ping": True, "pool_recycle": 300}
