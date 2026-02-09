from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_username: str
    database_name: str
    database_host: str
    database_port: str
    database_password: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    sqlalchemy_database_url: str

    model_config = {
        "env_file": ".env",
        "extra": "forbid"
    }

settings = Settings()
