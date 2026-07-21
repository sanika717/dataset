from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard", response_model=schemas.DashboardStatsOut)
def dashboard_stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.get_dashboard_stats(db)


@router.get("/analytics", response_model=schemas.AnalyticsOut)
def analytics(
    # `from` is a Python keyword, so the local param is `from_` — the
    # explicit alias is what actually makes FastAPI bind it to the
    # frontend's literal `?from=` query key (see dashboardService.js).
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.get_analytics(db, from_date=from_, to_date=to)
