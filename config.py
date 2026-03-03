from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    sqlalchemy_database_url: str

    model_config = {
        "env_file": ".env",
        "extra": "forbid"
    }

settings = Settings()
