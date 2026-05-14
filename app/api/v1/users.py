from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_db
from app.models.entities import Notification, Report, RoleRequest, RoleRequestStatus, User
from app.schemas.schemas import (
    MeRead,
    NotificationRead,
    ReportCreate,
    ReportRead,
    RoleRequestCreate,
    RoleRequestRead,
    UserProfileUpdate,
    UserRead,
)
from app.services.role_request_service import RoleRequestService

router = APIRouter()


@router.get("/me", response_model=MeRead)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeRead:
    pending = (
        db.query(RoleRequest)
        .filter(RoleRequest.user_id == current_user.id, RoleRequest.status == RoleRequestStatus.pending)
        .all()
    )
    base = UserRead.model_validate(current_user).model_dump()
    return MeRead(**base, pending_role_requests=pending)


@router.put("/me/profile", response_model=UserRead)
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/request-role", response_model=RoleRequestRead, status_code=201)
def request_role(
    payload: RoleRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoleRequest:
    return RoleRequestService.create_request(db, current_user, payload)


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/reports", response_model=ReportRead, status_code=201)
def create_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Report:
    report = Report(reporter_id=current_user.id, **payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
