from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import RoleRequest, RoleRequestStatus, User, UserRole
from app.schemas.schemas import RoleRequestCreate
from app.services.notification_service import NotificationService


class RoleRequestService:
    @staticmethod
    def create_request(db: Session, user: User, payload: RoleRequestCreate) -> RoleRequest:
        if payload.requested_role not in {UserRole.hack_org, UserRole.talent_hunter}:
            raise HTTPException(status_code=400, detail="Only organizer and talent hunter requests are allowed")
        if user.role == payload.requested_role:
            raise HTTPException(status_code=400, detail="User already has this role")
        existing = (
            db.query(RoleRequest)
            .filter(
                RoleRequest.user_id == user.id,
                RoleRequest.requested_role == payload.requested_role,
                RoleRequest.status == RoleRequestStatus.pending,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="A pending request already exists")

        request = RoleRequest(user_id=user.id, **payload.model_dump())
        db.add(request)
        NotificationService.notify(
            db,
            user.id,
            "Role request submitted",
            f"Your request for {payload.requested_role.value} is pending admin approval.",
            "role_request",
        )
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def approve(db: Session, request: RoleRequest, admin: User, note: str | None = None) -> RoleRequest:
        if request.status != RoleRequestStatus.pending:
            raise HTTPException(status_code=400, detail="Only pending requests can be approved")
        user = db.get(User, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Request user not found")
        request.status = RoleRequestStatus.approved
        request.reviewed_by_id = admin.id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_note = note
        user.role = request.requested_role
        NotificationService.notify(
            db,
            user.id,
            "Role request approved",
            f"You are now a {request.requested_role.value}.",
            "role_request",
        )
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def reject(db: Session, request: RoleRequest, admin: User, note: str | None = None) -> RoleRequest:
        if request.status != RoleRequestStatus.pending:
            raise HTTPException(status_code=400, detail="Only pending requests can be rejected")
        request.status = RoleRequestStatus.rejected
        request.reviewed_by_id = admin.id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_note = note
        NotificationService.notify(
            db,
            request.user_id,
            "Role request rejected",
            note or "Your role request was rejected by an admin.",
            "role_request",
        )
        db.commit()
        db.refresh(request)
        return request
