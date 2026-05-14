from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import ensure_judge_for_project, get_current_user, get_db
from app.models.entities import Hackathon, HackathonJudge, Project, ProjectScore, User, UserRole
from app.schemas.schemas import HackathonRead, ProjectScoreCreate, ProjectScoreRead

router = APIRouter()


@router.get("/judge/assignments", response_model=list[HackathonRead])
def judge_assignments(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Hackathon]:
    if current_user.role == UserRole.admin:
        return db.query(Hackathon).all()
    return (
        db.query(Hackathon)
        .join(HackathonJudge, HackathonJudge.hackathon_id == Hackathon.id)
        .filter(HackathonJudge.judge_id == current_user.id)
        .all()
    )


@router.post("/projects/{project_id}/score", response_model=ProjectScoreRead)
def score_project(
    project_id: int,
    payload: ProjectScoreCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectScore:
    ensure_judge_for_project(db, current_user, project_id)
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    score = db.query(ProjectScore).filter_by(project_id=project_id, judge_id=current_user.id).first()
    if score:
        for field, value in payload.model_dump().items():
            setattr(score, field, value)
    else:
        score = ProjectScore(project_id=project_id, judge_id=current_user.id, **payload.model_dump())
        db.add(score)
    db.commit()
    db.refresh(score)
    return score


@router.get("/projects/{project_id}/my-score", response_model=ProjectScoreRead)
def my_score(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectScore:
    ensure_judge_for_project(db, current_user, project_id)
    score = db.query(ProjectScore).filter_by(project_id=project_id, judge_id=current_user.id).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    return score
