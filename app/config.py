from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Chatwoot
    chatwoot_base_url: str
    chatwoot_account_id: int
    chatwoot_bot_token: str

    chatwoot_bot_email: str = "bot@example.com"
    chatwoot_frontend_url: str = ""

    # Postgres
    database_url: str = ""

    postgres_user: str = "kanban"
    postgres_password: str = ""
    postgres_db: str = "kanban"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    @property
    def resolved_db_url(self) -> str:
        if self.database_url:
            return self.database_url
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
        extra = "ignore"


settings = Settings()
