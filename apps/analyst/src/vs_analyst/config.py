from dotenv import load_dotenv
load_dotenv()

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, SecretStr, computed_field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# class RedisConfig(BaseSettings):
#     host: str = "localhost"
#     port: int = 6379
#     password: SecretStr | None = None
#     db: int = 0

#     @computed_field
#     @property
#     def url(self) -> str:
#         if self.password:
#             return (
#                 f"redis://:{self.password.get_secret_value()}"
#                 f"@{self.host}:{self.port}/{self.db}"
#             )

#         return f"redis://{self.host}:{self.port}/{self.db}"


class TextLLMConfig(BaseSettings):
    base_url: HttpUrl = Field(..., alias="LLM_BASE_URL")
    provider: str | None = Field(default=None, alias="LLM_PROVIDER")
    api_key: SecretStr | None = Field(default=None, alias="LLM_API_KEY")
    model: str | None = Field(default=None, alias="TEXT_MODEL_NAME")
    image_model: str | None = Field(default=None, alias="IMAGE_MODEL_NAME")
    temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE", ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")
    top_p: float = Field(default=0.7, alias="LLM_TOP_p")
    stream: bool = Field(default=True, alias="MODEL_OUTPUT_STREAM")

class ImageVLMConfig(BaseSettings):
    base_url: HttpUrl = Field(..., alias="VLM_BASE_URL")
    provider: str | None = Field(default=None, alias="VLM_PROVIDER")
    api_key: SecretStr | None = Field(default=None, alias="VLM_API_KEY")
    model: str | None = Field(default=None, alias="IMAGE_MODEL_NAME")
    temperature: float = Field(default=0.2, alias="VLM_TEMPERATURE", ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, alias="VLM_MAX_TOKENS")
    stream: bool = Field(default=True, alias="MODEL_OUTPUT_STREAM")


class StorageConfig(BaseSettings):
    access_key: str = Field(..., alias="STORAGE_ACCESS_KEY")
    secret_key: SecretStr = Field(..., alias="STORAGE_SECRET_KEY")
    endpoint_url: str = Field(..., alias="STORAGE_ENDPOINT")
    region_name: str = Field(default="us-east-1", alias="STORAGE_REGION")
    bucket_name: str = Field(..., alias="STORAGE_BUCKET")


class DatabaseConfig(BaseSettings):
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: SecretStr = Field(default="postgrespassword", alias="POSTGRES_PASSWORD")
    db: str = Field(default="vc_analyst", alias="POSTGRES_DB")

    @computed_field
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    """
    Central application settings
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="AI Platform", alias="APP_NAME")
    environment: Literal["local", "dev", "staging", "prod"] = Field(default="local", alias="DEPLOYMENT_ENVIRONMENT_TYPE")
    debug: bool = Field(default=True, alias="DEBUGGING")
    backend_callback_url: HttpUrl | None = Field(default=None, alias="BACKEND_CALLBACK_URL")

    # Web & Crawling Settings
    search_provider: Optional[Literal["tavily", "searxng"]] = Field(default=None, alias="SEARCH_PROVIDER")
    searxng_url: Optional[HttpUrl] = Field(default=None, alias="SEARXNG_URL")
    tavily_api_key: Optional[SecretStr] = Field(default=None, alias="TAVILY_API_KEY")
    search_timeout: float = Field(default=8.0, alias="SEARCH_TIMEOUT")
    crawl_depth_limit: int = Field(default=2, alias="CRAWL_DEPTH_LIMIT")
    crawl_max_pages: int = Field(default=5, alias="CRAWL_MAX_PAGES")
    market_research_max_attempts: int = Field(default=2, alias="MARKET_RESEARCH_MAX_ATTEMPTS")

    @model_validator(mode="after")
    def validate_search_provider(self) -> "Settings":
        has_tavily = self.tavily_api_key is not None and self.tavily_api_key.get_secret_value().strip() != ""
        has_searxng = self.searxng_url is not None and str(self.searxng_url).strip() != ""

        if not has_tavily and not has_searxng:
            raise ValueError("At least one of TAVILY_API_KEY or SEARXNG_URL must be provided.")

        # Determine default provider if not explicitly configured
        if not self.search_provider:
            if has_tavily:
                self.search_provider = "tavily"
            else:
                self.search_provider = "searxng"
        else:
            # Respect explicit setting, but fallback gracefully if missing config
            if self.search_provider == "tavily" and not has_tavily:
                if has_searxng:
                    self.search_provider = "searxng"
                else:
                    raise ValueError("SEARCH_PROVIDER is set to 'tavily' but TAVILY_API_KEY is not provided.")
            elif self.search_provider == "searxng" and not has_searxng:
                if has_tavily:
                    self.search_provider = "tavily"
                else:
                    raise ValueError("SEARCH_PROVIDER is set to 'searxng' but SEARXNG_URL is not provided.")

        return self

    llm: TextLLMConfig = TextLLMConfig()
    vlm: ImageVLMConfig = ImageVLMConfig()
    storage_config: StorageConfig = StorageConfig()
    db: DatabaseConfig = DatabaseConfig()



@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance
    """
    return Settings()

settings = get_settings()