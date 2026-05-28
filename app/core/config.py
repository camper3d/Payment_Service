from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    database_url: str = "postgresql+asyncpg://payment_user:payment_pass@localhost:5432/payment_db"

    rabbitmq_url: str = "amqp://payment_user:payment_pass@localhost:5672/"

    api_key: str = "test-api-key-123"

    outbox_poll_interval: int = 5
    outbox_batch_size: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
