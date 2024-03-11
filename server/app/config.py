from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    class Config:
        env_file = ".env"


settings = Settings(
    database_hostname = "aws-0-us-west-1.pooler.supabase.com",
    database_port = "5432",
    database_password = "NHcvQRn9(G%urTB",
    database_name = "Budgeter",
    database_username = "postgres",
    secret_key = "427868.3b1Z3_266J@EwtyW*&*5b@3c9R4b.73f42_f821W5ccfe1470c5a.6d100e1ceWMzx51ed1!7b383ad5sq23XzCe5",
    algorithm = "HS256",
    access_token_expire_minutes = "30",
)
