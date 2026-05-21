from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field, HttpUrl
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
    provider: Literal["openai", "anthropic", "gemini"] | None = Field(default=None, alias="LLM_PROVIDER")
    api_key: SecretStr | None = Field(default=None, alias="LLM_API_KEY")
    model: str | None = Field(default=None, alias="TEXT_MODEL_NAME")
    image_model: str | None = Field(default=None, alias="IMAGE_MODEL_NAME")
    temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE", ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")
    top_p: float = Field(default=0.7, alias="LLM_TOP_p")
    stream: bool = Field(default=True, alias="MODEL_OUTPUT_STREAM")

class ImageVLMConfig(BaseSettings):
    base_url: HttpUrl = Field(..., alias="VLM_BASE_URL")
    provider: Literal["openai", "anthropic", "gemini"] | None = Field(default=None, alias="VLM_PROVIDER")
    api_key: SecretStr | None = Field(default=None, alias="VLM_API_KEY")
    model: str | None = Field(default=None, alias="IMAGE_MODEL_NAME")
    temperature: float = Field(default=0.2, alias="VLM_TEMPERATURE", ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, alias="VLM_MAX_TOKENS")
    stream: bool = Field(default=True, alias="MODEL_OUTPUT_STREAM")


class ObjectDBConfig(BaseSettings):
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY")
    aws_secret_access_key: SecretStr | None = Field(default=None, alias="AWS_SECRET_KEY")
    endpoint_url: str | None = Field(default=None, alias="OBJECT_DB_ENDPOINT")
    region_name: str = Field(default="us-east-1",alias="OBJECTDB_REGION")
    bucket_name: str | None = Field(default=None, alias="OBJECTDB_BUCKET")

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

    llm: ImageVLMConfig = ImageVLMConfig()
    vlm: ImageVLMConfig = ImageVLMConfig()
    Object_db: ObjectDBConfig = ObjectDBConfig()


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance
    """
    return Settings()


settings = get_settings()