from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class RSSSource(Base):
    __tablename__ = "rss_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("rss_sources.id"), nullable=False)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    published_at = Column(DateTime, nullable=True)
    content_summary = Column(Text, default="")
    ai_summary = Column(Text, default="")
    ai_summary_error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("RSSSource", back_populates="articles")
    report_associations = relationship("ReportArticle", back_populates="article", cascade="all, delete-orphan")


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    markdown_content = Column(Text, default="")
    article_count = Column(Integer, default=0)
    source_count = Column(Integer, default=0)
    fetch_task_id = Column(String(100), default="")
    trigger_source = Column(String(20), default="manual")  # "manual" or "scheduled"

    articles = relationship("ReportArticle", back_populates="report", cascade="all, delete-orphan")


class ReportArticle(Base):
    __tablename__ = "report_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("daily_reports.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)

    report = relationship("DailyReport", back_populates="articles")
    article = relationship("Article", back_populates="report_associations")


class AppConfig(Base):
    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(200), unique=True, nullable=False)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
