from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Chatwoot
    chatwoot_base_url: str
    chatwoot_account_id: int
    chatwoot_bot_token: str

    # Postgres — valores individuales, la URL se construye sola
    postgres_user: str = "kanban"
    postgres_password: str
    postgres_db: str = "kanban"
    postgres_host: str = "ruki-kanban-postgres"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Webhook
    chatwoot_webhook_secret: str = ""

    # Cloudflare Access (etapa 0, dejado listo para cuando lo conectemos)
    cf_access_team_domain: str = ""
    cf_access_aud: str = ""

    env: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
