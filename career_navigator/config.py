from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    # Groq
    GROQ_API_KEY: str = ""
    
    # LinkedIn API
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""  # OAuth 2.0 access token
    
    # Database
    DATABASE_URL: str = "postgresql://career_navigator:career_navigator_password@localhost:5433/career_navigator"


settings = Settings()
