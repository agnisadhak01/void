from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ausome:ausome_dev@localhost:5432/ausome"
    supabase_jwt_secret: str = ""
    ausome_auth_disabled: bool = True
    vllm_base_url: str = "http://127.0.0.1:8001/v1"
    vllm_api_key: str = "noop"
    embedding_model: str = "bge-m3"
    rerank_model: str = "bge-reranker-v2"
    ausome_sandbox_enabled: bool = False
    sandbox_service_url: str = "http://127.0.0.1:8010"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "ausome"
    minio_secret_key: str = "ausome_dev_minio"
    default_project_id: str = "00000000-0000-0000-0000-000000000001"


settings = Settings()
