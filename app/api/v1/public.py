from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.models.entities import Hackathon, HackathonStatus, Project, ProjectStatus, User
from app.schemas.schemas import HackathonRead, ProjectRead, UserRead

router = APIRouter()


@router.get("/hackathons", response_model=list[HackathonRead])
def list_hackathons(
    status: HackathonStatus | None = Query(default=None),
    university: str | None = None,
    theme: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> list[Hackathon]:
    public_statuses = [HackathonStatus.published, HackathonStatus.completed]
    query = db.query(Hackathon).filter(Hackathon.deleted_at.is_(None))
    if status:
        if status not in public_statuses:
            return []
        query = query.filter(Hackathon.status == status)
    else:
        query = query.filter(Hackathon.status.in_(public_statuses))
    if university:
        query = query.filter(Hackathon.university.ilike(f"%{university}%"))
    if theme:
        query = query.filter(Hackathon.theme.ilike(f"%{theme}%"))
    if search:
        query = query.filter(or_(Hackathon.title.ilike(f"%{search}%"), Hackathon.description.ilike(f"%{search}%")))
    return query.order_by(Hackathon.created_at.desc()).all()


@router.get("/hackathons/{hackathon_id}", response_model=HackathonRead)
def get_hackathon(hackathon_id: int, db: Session = Depends(get_db)) -> Hackathon:
    hackathon = (
        db.query(Hackathon)
        .filter(
            Hackathon.id == hackathon_id,
            Hackathon.deleted_at.is_(None),
            Hackathon.status.in_([HackathonStatus.published, HackathonStatus.completed]),
        )
        .first()
    )
    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return hackathon


@router.get("/hackathons/{hackathon_id}/projects", response_model=list[ProjectRead])
def get_hackathon_projects(hackathon_id: int, db: Session = Depends(get_db)) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.hackathon_id == hackathon_id, Project.status == ProjectStatus.approved)
        .order_by(Project.created_at.desc())
        .all()
    )


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.status == ProjectStatus.approved).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/users/{user_id}/profile", response_model=UserRead)
def get_user_profile(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
