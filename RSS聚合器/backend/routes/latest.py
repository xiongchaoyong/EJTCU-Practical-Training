from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db
from models import DailyReport
from schemas import DailyReportResponse

router = APIRouter(prefix="/api", tags=["latest"])


@router.get("/latest", response_model=DailyReportResponse)
def get_latest_report(db: Session = Depends(get_db)):
    """Get the latest generated Markdown daily report."""
    report = db.query(DailyReport).order_by(DailyReport.generated_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="尚无日报，请先执行抓取任务")
    return report


@router.get("/report/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """Download a specific Markdown report as a file."""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")

    filename = f"news_daily_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.md"
    return PlainTextResponse(
        content=report.markdown_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports", response_model=list[DailyReportResponse])
def list_reports(db: Session = Depends(get_db)):
    """List all generated reports (latest 20)."""
    return (
        db.query(DailyReport)
        .order_by(DailyReport.generated_at.desc())
        .limit(20)
        .all()
    )
