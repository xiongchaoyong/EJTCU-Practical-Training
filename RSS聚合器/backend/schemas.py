from datetime import datetime
from pydantic import BaseModel, Field


class RSSSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=500)


class RSSSourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    url: str | None = Field(None, min_length=1, max_length=500)
    is_active: bool | None = None


class RSSSourceResponse(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleResponse(BaseModel):
    id: int
    source_id: int
    title: str
    link: str
    published_at: datetime | None
    content_summary: str
    ai_summary: str
    ai_summary_error: str

    model_config = {"from_attributes": True}


class DailyReportResponse(BaseModel):
    id: int
    generated_at: datetime
    markdown_content: str
    article_count: int
    source_count: int
    fetch_task_id: str
    trigger_source: str

    model_config = {"from_attributes": True}


class FetchResponse(BaseModel):
    task_id: str
    message: str


class OpenAIKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1)
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"


class AIConfigResponse(BaseModel):
    configured: bool
    base_url: str = ""
    model: str = ""
    provider: str = ""
