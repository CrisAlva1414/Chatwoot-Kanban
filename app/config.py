from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Chatwoot
    chatwoot_base_url: str
    chatwoot_account_id: int
    chatwoot_bot_token: str

    # Postgres
    database_url: str

    # Cloudflare Access (etapa 0, dejado listo para cuando lo conectemos)
    cf_access_team_domain: str = ""
    cf_access_aud: str = ""

    env: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
