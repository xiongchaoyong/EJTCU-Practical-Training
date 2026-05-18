import logging
import re
from sqlalchemy.orm import Session
from openai import OpenAI

from models import Article
from config import decrypt_value

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个新闻摘要助手，请用中文将以下文章内容总结为 1-2 句话，不超过 50 字。"
    "只返回总结本身，不要加额外说明。"
)


def get_ai_config(db: Session) -> dict:
    """Get all AI configuration from database."""
    from models import AppConfig
    configs = {c.key: c.value for c in db.query(AppConfig).all()}

    api_key_enc = configs.get("openai_api_key", "")
    base_url = configs.get("ai_base_url", "https://api.openai.com/v1")
    model = configs.get("ai_model", "gpt-3.5-turbo")

    return {
        "api_key": decrypt_value(api_key_enc) if api_key_enc else "",
        "base_url": base_url or "https://api.openai.com/v1",
        "model": model or "gpt-3.5-turbo",
    }


def clean_html(text: str) -> str:
    """Strip HTML tags from text."""
    clean = re.compile(r"<.*?>")
    return re.sub(clean, "", text)


def summarize_article(db: Session, article: Article) -> None:
    """Summarize a single article using configured AI API."""
    config = get_ai_config(db)
    api_key = config["api_key"]
    if not api_key:
        article.ai_summary_error = "API Key 未配置"
        db.commit()
        return

    summary_text = article.content_summary or ""
    summary_text = clean_html(summary_text)
    if not summary_text.strip():
        summary_text = article.title

    user_content = f"标题：{article.title}\n内容：{summary_text[:500]}"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=config["base_url"],
            timeout=10.0,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=120,
            temperature=0.5,
        )
        article.ai_summary = response.choices[0].message.content.strip()
        article.ai_summary_error = ""
        logger.info(f"Successfully summarized article: {article.title[:50]}")
    except Exception as e:
        article.ai_summary_error = _clean_error(str(e))
        logger.error(f"Failed to summarize article '{article.title[:50]}': {e}")

    db.commit()


def _clean_error(msg: str) -> str:
    """Extract a concise error message from OpenAI exceptions."""
    if "401" in msg or "Incorrect API key" in msg:
        return "API Key 无效，请检查是否输入正确"
    if "429" in msg or "Rate limit" in msg:
        return "API 请求频率超限，请稍后再试"
    if "timeout" in msg.lower() or "timed out" in msg.lower():
        return "API 请求超时"
    if "connection" in msg.lower():
        return "网络连接失败，请检查网络"
    # Truncate very long messages
    if len(msg) > 200:
        return msg[:200] + "..."
    return msg


def summarize_all_articles(db: Session) -> dict:
    """Summarize all articles that don't have an AI summary yet."""
    articles = (
        db.query(Article)
        .filter(Article.ai_summary == "", Article.ai_summary_error == "")
        .all()
    )

    success = 0
    failed = 0

    for article in articles:
        summarize_article(db, article)
        if article.ai_summary_error:
            failed += 1
        else:
            success += 1

    return {"success": success, "failed": failed, "total": len(articles)}
