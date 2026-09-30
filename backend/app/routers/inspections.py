from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai_client import AIClient, build_ai_client
from ..database import get_db
from ..models import Inspection
from ..schemas import (
    DashboardStats,
    InspectionCreate,
    InspectionPage,
    InspectionRead,
    InspectionUpdate,
    InspectionWithVerdict,
    SeverityCount,
    StatusCount,
)

router = APIRouter(prefix="/api/inspections", tags=["inspections"])

PASSING_SEVERITIES = {"minor"}
REVIEW_SEVERITIES = {"major"}
FAILING_SEVERITIES = {"critical"}


def derive_status(severity: str | None) -> str:
    if severity is None:
        return "pending"
    if severity in PASSING_SEVERITIES:
        return "passed"
    if severity in REVIEW_SEVERITIES:
        return "review"
    if severity in FAILING_SEVERITIES:
        return "failed"
    return "pending"


def get_ai_client() -> AIClient:
    return build_ai_client()


async def attach_verdict(
    inspection: Inspection, client: AIClient
) -> tuple[Inspection, str | None]:
    verdict, warning = await client.predict(inspection.measurement_payload)
    if verdict is not None:
        inspection.severity = verdict.severity
        inspection.confidence = verdict.confidence
        inspection.status = derive_status(verdict.severity)
    return inspection, warning


@router.get("", response_model=InspectionPage)
def list_inspections(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(
        default=None, alias="status", pattern="^(pending|passed|failed|review)$"
    ),
    severity: str | None = Query(
        default=None, pattern="^(minor|major|critical)$"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> InspectionPage:
    query = select(Inspection)
    count_query = select(func.count()).select_from(Inspection)

    if status_filter:
        query = query.where(Inspection.status == status_filter)
        count_query = count_query.where(Inspection.status == status_filter)
    if severity:
        query = query.where(Inspection.severity == severity)
        count_query = count_query.where(Inspection.severity == severity)

    total = db.execute(count_query).scalar_one()
    rows = (
        db.execute(
            query.order_by(Inspection.created_at.desc(), Inspection.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return InspectionPage(
        items=[InspectionRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=InspectionWithVerdict, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    payload: InspectionCreate,
    db: Session = Depends(get_db),
    client: AIClient = Depends(get_ai_client),
) -> InspectionWithVerdict:
    existing = db.execute(
        select(Inspection).where(Inspection.part_serial == payload.part_serial)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"part_serial '{payload.part_serial}' already exists",
        )

    inspection = Inspection(**payload.model_dump(), status="pending")
    db.add(inspection)
    db.flush()

    inspection, warning = await attach_verdict(inspection, client)
    db.commit()
    db.refresh(inspection)

    return InspectionWithVerdict(
        **InspectionRead.model_validate(inspection).model_dump(),
        ai_verdict=(
            None
            if inspection.severity is None
            else {
                "severity": inspection.severity,
                "confidence": inspection.confidence,
            }
        ),
        ai_warning=warning,
    )


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    total = db.execute(select(func.count()).select_from(Inspection)).scalar_one()

    severity_rows = db.execute(
        select(Inspection.severity, func.count())
        .where(Inspection.severity.is_not(None))
        .group_by(Inspection.severity)
    ).all()
    status_rows = db.execute(
        select(Inspection.status, func.count()).group_by(Inspection.status)
    ).all()
    avg_confidence = db.execute(
        select(func.avg(Inspection.confidence)).where(Inspection.confidence.is_not(None))
    ).scalar_one()

    severity_counts = {row[0]: row[1] for row in severity_rows}
    critical = severity_counts.get("critical", 0)
    scored = sum(severity_counts.values())

    return DashboardStats(
        total_inspections=total,
        average_confidence=round(float(avg_confidence), 4)
        if avg_confidence is not None
        else None,
        severity_breakdown=[
            SeverityCount(severity=key, count=value)
            for key, value in sorted(severity_counts.items())
        ],
        status_breakdown=[
            StatusCount(status=row[0], count=row[1]) for row in sorted(status_rows)
        ],
        critical_rate=round(critical / scored, 4) if scored else 0.0,
    )


@router.get("/{inspection_id}", response_model=InspectionRead)
def get_inspection(
    inspection_id: int, db: Session = Depends(get_db)
) -> Inspection:
    inspection = db.get(Inspection, inspection_id)
    if inspection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection {inspection_id} not found",
        )
    return inspection


@router.patch("/{inspection_id}", response_model=InspectionRead)
def update_inspection(
    inspection_id: int,
    payload: InspectionUpdate,
    db: Session = Depends(get_db),
) -> Inspection:
    inspection = get_inspection(inspection_id, db)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(inspection, field, value)
    db.commit()
    db.refresh(inspection)
    return inspection


@router.delete(
    "/{inspection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_inspection(inspection_id: int, db: Session = Depends(get_db)) -> Response:
    inspection = get_inspection(inspection_id, db)
    db.delete(inspection)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{inspection_id}/reinspect", response_model=InspectionWithVerdict)
async def reinspect(
    inspection_id: int,
    db: Session = Depends(get_db),
    client: AIClient = Depends(get_ai_client),
) -> InspectionWithVerdict:
    inspection = get_inspection(inspection_id, db)
    inspection, warning = await attach_verdict(inspection, client)
    db.commit()
    db.refresh(inspection)

    return InspectionWithVerdict(
        **InspectionRead.model_validate(inspection).model_dump(),
        ai_verdict=(
            None
            if inspection.severity is None
            else {
                "severity": inspection.severity,
                "confidence": inspection.confidence,
            }
        ),
        ai_warning=warning,
    )
