import logging
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from collections import defaultdict

from models import Article, RSSSource, DailyReport, ReportArticle

logger = logging.getLogger(__name__)

CST = timezone(timedelta(hours=8))


def _to_local(dt: datetime | None) -> str:
    """Convert UTC datetime to CST string for display."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(CST)
    return local.strftime('%Y-%m-%d %H:%M')


def generate_markdown_report(db: Session) -> str:
    """Generate a Markdown daily report from all articles with AI summaries."""
    sources = db.query(RSSSource).all()
    articles = (
        db.query(Article)
        .order_by(Article.published_at.desc())
        .all()
    )

    articles_by_source = defaultdict(list)
    for article in articles:
        articles_by_source[article.source_id].append(article)

    now = datetime.now()
    lines = [
        f"# 每日新闻日报 - {now.strftime('%Y-%m-%d')}",
        "",
        f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 共抓取 {len(articles)} 篇文章，来自 {len(sources)} 个 RSS 源",
        "",
    ]

    for source in sources:
        source_articles = articles_by_source.get(source.id, [])
        if not source_articles:
            continue

        lines.append(f"## {source.name}")
        lines.append("")

        for article in source_articles:
            lines.append(f"### [{article.title}]({article.link})")

            if article.ai_summary:
                lines.append(f"> 💡 **AI 要点**：{article.ai_summary}")
            elif article.ai_summary_error:
                lines.append(f"> ⚠️ **总结失败**：{article.ai_summary_error}")

            if article.published_at:
                lines.append(f"> 📅 发布时间：{_to_local(article.published_at)}")

            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def save_report(db: Session, task_id: str = "", source: str = "manual") -> DailyReport:
    """Generate and save the daily report to database."""
    markdown = generate_markdown_report(db)

    articles = db.query(Article).order_by(Article.published_at.desc()).all()
    sources = db.query(RSSSource).all()

    report = DailyReport(
        generated_at=datetime.utcnow(),
        markdown_content=markdown,
        article_count=len(articles),
        source_count=len(sources),
        fetch_task_id=task_id,
        trigger_source=source,
    )
    db.add(report)
    db.commit()

    for article in articles:
        ra = ReportArticle(report_id=report.id, article_id=article.id)
        db.add(ra)
    db.commit()

    logger.info(f"Saved daily report #{report.id} with {len(articles)} articles")
    return report


def run_fetch_and_summarize_task(db_session_factory, task_id: str = "", source: str = "manual") -> dict:
    """Full pipeline: fetch -> summarize -> generate report. Runs in background thread."""
    import time
    from services.rss_fetcher import fetch_all_sources
    from services.summarizer import summarize_all_articles
    from services.task_store import update_task

    if not task_id:
        task_id = str(uuid.uuid4())
    logger.info(f"Starting background task {task_id} (source={source})")

    db = db_session_factory()

    try:
        fetch_result = fetch_all_sources(db)
        update_task(
            task_id, "running",
            result={"stage": "抓取完成", "fetched": fetch_result}
        )
        time.sleep(0.5)

        summary_result = summarize_all_articles(db)
        update_task(
            task_id, "running",
            result={"stage": "AI 总结完成", "fetched": fetch_result, "summarized": summary_result}
        )
        time.sleep(0.5)

        report = save_report(db, task_id=task_id, source=source)

        result = {
            "task_id": task_id,
            "status": "completed",
            "report_id": report.id,
            "trigger_source": source,
            "fetched": fetch_result,
            "summarized": summary_result,
        }
        update_task(task_id, "completed", result=result)
        logger.info(f"Task {task_id} completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        update_task(task_id, "failed", error=str(e))
        return {"task_id": task_id, "status": "failed", "error": str(e)}
    finally:
        db.close()
