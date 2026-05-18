from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import AppConfig
from schemas import OpenAIKeyRequest, AIConfigResponse
from config import encrypt_value, decrypt_value

router = APIRouter(prefix="/api", tags=["settings"])


def _get_or_create_config(db: Session, key: str, default: str = "") -> AppConfig:
    cfg = db.query(AppConfig).filter(AppConfig.key == key).first()
    if not cfg:
        cfg = AppConfig(key=key, value=default)
        db.add(cfg)
        db.commit()
    return cfg


@router.post("/set-openai-key")
def set_openai_key(data: OpenAIKeyRequest, db: Session = Depends(get_db)):
    """Set or update AI API configuration."""
    # API Key (encrypted)
    cfg_key = _get_or_create_config(db, "openai_api_key")
    cfg_key.value = encrypt_value(data.api_key)

    # Base URL
    cfg_url = _get_or_create_config(db, "ai_base_url", "https://api.openai.com/v1")
    cfg_url.value = data.base_url

    # Model
    cfg_model = _get_or_create_config(db, "ai_model", "gpt-3.5-turbo")
    cfg_model.value = data.model

    db.commit()

    provider = "DeepSeek" if "deepseek" in data.base_url.lower() else "OpenAI"
    return {"message": f"AI 配置已保存（{provider}）"}


@router.get("/check-openai-key", response_model=AIConfigResponse)
def check_openai_key(db: Session = Depends(get_db)):
    """Check if AI API is configured and return current settings."""
    key_cfg = db.query(AppConfig).filter(AppConfig.key == "openai_api_key").first()
    url_cfg = db.query(AppConfig).filter(AppConfig.key == "ai_base_url").first()
    model_cfg = db.query(AppConfig).filter(AppConfig.key == "ai_model").first()

    has_key = key_cfg is not None and key_cfg.value != ""
    base_url = url_cfg.value if url_cfg else ""
    model = model_cfg.value if model_cfg else ""

    provider = "DeepSeek" if "deepseek" in base_url.lower() else "OpenAI"
    if not has_key:
        provider = "未配置"

    return AIConfigResponse(
        configured=has_key,
        base_url=base_url,
        model=model,
        provider=provider,
    )
