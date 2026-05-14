from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db, get_organizer
from app.models.entities import (
    ActivityLog,
    Hackathon,
    HackathonJudge,
    HackathonRegistration,
    HackathonStatus,
    Project,
    ProjectStatus,
    Team,
    User,
    UserRole,
)
from app.schemas.schemas import (
    AnalyticsRead,
    HackathonCreate,
    HackathonRead,
    HackathonUpdate,
    JudgeAssign,
    ProjectRead,
    RegistrationRead,
    TeamRead,
    WinnerDeclare,
)
from app.services.analytics_service import AnalyticsService
from app.services.export_service import ExportService
from app.services.notification_service import NotificationService

router = APIRouter()


def organizer_hackathon_or_404(db: Session, hackathon_id: int, user: User) -> Hackathon:
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon or hackathon.deleted_at:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    if user.role != UserRole.admin and hackathon.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="Organizer ownership required")
    return hackathon


@router.post("/hackathons", response_model=HackathonRead, status_code=201)
def create_hackathon(
    payload: HackathonCreate,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Hackathon:
    hackathon = Hackathon(organizer_id=current_user.id, **payload.model_dump())
    db.add(hackathon)
    db.flush()
    db.add(ActivityLog(actor_id=current_user.id, hackathon_id=hackathon.id, action="hackathon.created"))
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.get("/hackathons", response_model=list[HackathonRead])
def list_my_hackathons(current_user: User = Depends(get_organizer), db: Session = Depends(get_db)) -> list[Hackathon]:
    query = db.query(Hackathon).filter(Hackathon.deleted_at.is_(None))
    if current_user.role != UserRole.admin:
        query = query.filter(Hackathon.organizer_id == current_user.id)
    return query.order_by(Hackathon.created_at.desc()).all()


@router.get("/hackathons/{hackathon_id}", response_model=HackathonRead)
def get_my_hackathon(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Hackathon:
    return organizer_hackathon_or_404(db, hackathon_id, current_user)


@router.put("/hackathons/{hackathon_id}", response_model=HackathonRead)
def update_hackathon(
    hackathon_id: int,
    payload: HackathonUpdate,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Hackathon:
    hackathon = organizer_hackathon_or_404(db, hackathon_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(hackathon, field, value)
    db.add(ActivityLog(actor_id=current_user.id, hackathon_id=hackathon.id, action="hackathon.updated"))
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.delete("/hackathons/{hackathon_id}", response_model=HackathonRead)
def soft_delete_hackathon(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Hackathon:
    hackathon = organizer_hackathon_or_404(db, hackathon_id, current_user)
    hackathon.deleted_at = datetime.now(timezone.utc)
    hackathon.status = HackathonStatus.archived
    db.add(ActivityLog(actor_id=current_user.id, hackathon_id=hackathon.id, action="hackathon.deleted"))
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.patch("/hackathons/{hackathon_id}/publish", response_model=HackathonRead)
def publish_hackathon(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Hackathon:
    hackathon = organizer_hackathon_or_404(db, hackathon_id, current_user)
    hackathon.status = HackathonStatus.published
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.patch("/hackathons/{hackathon_id}/unpublish", response_model=HackathonRead)
def unpublish_hackathon(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Hackathon:
    hackathon = organizer_hackathon_or_404(db, hackathon_id, current_user)
    hackathon.status = HackathonStatus.draft
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.get("/hackathons/{hackathon_id}/registrations", response_model=list[RegistrationRead])
def hackathon_registrations(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> list[HackathonRegistration]:
    organizer_hackathon_or_404(db, hackathon_id, current_user)
    return db.query(HackathonRegistration).filter_by(hackathon_id=hackathon_id).all()


@router.get("/hackathons/{hackathon_id}/teams", response_model=list[TeamRead])
def hackathon_teams(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> list[Team]:
    organizer_hackathon_or_404(db, hackathon_id, current_user)
    return db.query(Team).filter_by(hackathon_id=hackathon_id).all()


@router.get("/hackathons/{hackathon_id}/projects", response_model=list[ProjectRead])
def hackathon_projects(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> list[Project]:
    organizer_hackathon_or_404(db, hackathon_id, current_user)
    return db.query(Project).filter_by(hackathon_id=hackathon_id).all()


@router.post("/hackathons/{hackathon_id}/judges", status_code=201)
def assign_judge(
    hackathon_id: int,
    payload: JudgeAssign,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    organizer_hackathon_or_404(db, hackathon_id, current_user)
    judge = db.get(User, payload.judge_user_id)
    if not judge:
        raise HTTPException(status_code=404, detail="Judge user not found")
    assignment = HackathonJudge(hackathon_id=hackathon_id, judge_id=payload.judge_user_id)
    if judge.role == UserRole.student:
        judge.role = UserRole.judge
    db.add(assignment)
    NotificationService.notify(db, judge.id, "Judge assignment", "You were assigned to judge a hackathon.", "judge")
    db.commit()
    return {"status": "assigned", "judge_user_id": judge.id}


@router.get("/hackathons/{hackathon_id}/analytics", response_model=AnalyticsRead)
def hackathon_analytics(
    hackathon_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> dict:
    organizer_hackathon_or_404(db, hackathon_id, current_user)
    return AnalyticsService.hackathon_summary(db, hackathon_id)


@router.get("/hackathons/{hackathon_id}/export/{kind}")
def export_hackathon_data(
    hackathon_id: int,
    kind: str,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
):
    organizer_hackathon_or_404(db, hackathon_id, current_user)
    if kind == "registrations":
        return ExportService.registrations_csv(db, hackathon_id)
    if kind == "teams":
        return ExportService.teams_csv(db, hackathon_id)
    if kind == "projects":
        return ExportService.projects_csv(db, hackathon_id)
    raise HTTPException(status_code=404, detail="Export type not found")


@router.patch("/projects/{project_id}/approve", response_model=ProjectRead)
def approve_project(
    project_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    organizer_hackathon_or_404(db, project.hackathon_id, current_user)
    project.status = ProjectStatus.approved
    db.commit()
    db.refresh(project)
    return project


@router.patch("/projects/{project_id}/reject", response_model=ProjectRead)
def reject_project(
    project_id: int,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    organizer_hackathon_or_404(db, project.hackathon_id, current_user)
    project.status = ProjectStatus.rejected
    db.commit()
    db.refresh(project)
    return project


@router.post("/hackathons/{hackathon_id}/declare-winners", response_model=HackathonRead)
def declare_winners(
    hackathon_id: int,
    payload: WinnerDeclare,
    current_user: User = Depends(get_organizer),
    db: Session = Depends(get_db),
) -> Hackathon:
    hackathon = organizer_hackathon_or_404(db, hackathon_id, current_user)
    hackathon.winners = payload.winners
    hackathon.status = HackathonStatus.completed
    db.commit()
    db.refresh(hackathon)
    return hackathon
