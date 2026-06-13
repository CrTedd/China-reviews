from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    rank_alpha_sim: float = 0.3
    rank_beta_score: float = 0.4
    rank_gamma_relevance: float = 0.3

    auto_seed: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
