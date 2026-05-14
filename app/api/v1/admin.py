from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_admin, get_db
from app.models.entities import Hackathon, Report, RoleRequest, RoleRequestStatus, User
from app.schemas.schemas import (
    AdminRoleChange,
    HackathonRead,
    HackathonStatusUpdate,
    ReportRead,
    RoleRequestRead,
    RoleRequestReview,
    UserRead,
)
from app.services.role_request_service import RoleRequestService

router = APIRouter()


@router.get("/role-requests", response_model=list[RoleRequestRead])
def list_role_requests(
    status: RoleRequestStatus = Query(default=RoleRequestStatus.pending),
    current_user: User = Depends(get_admin),
    db: Session = Depends(get_db),
) -> list[RoleRequest]:
    return db.query(RoleRequest).filter(RoleRequest.status == status).order_by(RoleRequest.created_at.desc()).all()


@router.post("/role-requests/{request_id}/approve", response_model=RoleRequestRead)
def approve_role_request(
    request_id: int,
    payload: RoleRequestReview | None = None,
    current_user: User = Depends(get_admin),
    db: Session = Depends(get_db),
) -> RoleRequest:
    request = db.get(RoleRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Role request not found")
    return RoleRequestService.approve(db, request, current_user, payload.note if payload else None)


@router.post("/role-requests/{request_id}/reject", response_model=RoleRequestRead)
def reject_role_request(
    request_id: int,
    payload: RoleRequestReview | None = None,
    current_user: User = Depends(get_admin),
    db: Session = Depends(get_db),
) -> RoleRequest:
    request = db.get(RoleRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Role request not found")
    return RoleRequestService.reject(db, request, current_user, payload.note if payload else None)


@router.get("/hackathons", response_model=list[HackathonRead])
def admin_hackathons(
    current_user: User = Depends(get_admin), db: Session = Depends(get_db)
) -> list[Hackathon]:
    return db.query(Hackathon).order_by(Hackathon.created_at.desc()).all()


@router.patch("/hackathons/{hackathon_id}/status", response_model=HackathonRead)
def update_hackathon_status(
    hackathon_id: int,
    payload: HackathonStatusUpdate,
    current_user: User = Depends(get_admin),
    db: Session = Depends(get_db),
) -> Hackathon:
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    hackathon.status = payload.status
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.get("/users", response_model=list[UserRead])
def list_users(current_user: User = Depends(get_admin), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/change-role", response_model=UserRead)
def change_user_role(
    user_id: int,
    payload: AdminRoleChange,
    current_user: User = Depends(get_admin),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/reports", response_model=list[ReportRead])
def list_reports(current_user: User = Depends(get_admin), db: Session = Depends(get_db)) -> list[Report]:
    return db.query(Report).order_by(Report.created_at.desc()).all()
