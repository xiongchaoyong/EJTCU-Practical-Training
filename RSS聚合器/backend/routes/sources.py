from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import RSSSource
from schemas import RSSSourceCreate, RSSSourceUpdate, RSSSourceResponse
from services.recommendations import RECOMMENDED_SOURCES

router = APIRouter(prefix="/api/sources", tags=["sources"])


class BulkAddRequest(BaseModel):
    urls: list[str] = []


@router.get("", response_model=list[RSSSourceResponse])
def list_sources(db: Session = Depends(get_db)):
    """Get all RSS sources."""
    return db.query(RSSSource).order_by(RSSSource.created_at.desc()).all()


@router.post("", response_model=RSSSourceResponse)
def create_source(data: RSSSourceCreate, db: Session = Depends(get_db)):
    """Add a new RSS source."""
    source = RSSSource(name=data.name, url=data.url)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.put("/{source_id}", response_model=RSSSourceResponse)
def update_source(source_id: int, data: RSSSourceUpdate, db: Session = Depends(get_db)):
    """Update an RSS source."""
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS源不存在")

    if data.name is not None:
        source.name = data.name
    if data.url is not None:
        source.url = data.url
    if data.is_active is not None:
        source.is_active = data.is_active

    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Delete an RSS source and its associated articles."""
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS源不存在")

    db.delete(source)
    db.commit()
    return {"message": "删除成功"}


@router.get("/recommendations")
def get_recommendations():
    """Get recommended RSS sources grouped by category."""
    return {"categories": RECOMMENDED_SOURCES}


@router.post("/bulk-add")
def bulk_add_sources(data: BulkAddRequest, db: Session = Depends(get_db)):
    """Add multiple RSS sources from recommendations by URL."""
    added = []
    skipped = []
    existing_urls = {s.url for s in db.query(RSSSource).all()}

    for url in data.urls:
        if url in existing_urls:
            skipped.append(url)
            continue

        # Look up the name from recommendations
        name = url
        for cat_sources in RECOMMENDED_SOURCES.values():
            for src in cat_sources:
                if src["url"] == url:
                    name = src["name"]
                    break

        source = RSSSource(name=name, url=url)
        db.add(source)
        existing_urls.add(url)
        added.append(url)

    db.commit()
    return {"added": len(added), "skipped": len(skipped), "added_urls": added, "skipped_urls": skipped}
