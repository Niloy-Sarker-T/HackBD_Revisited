from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db, get_talent_hunter
from app.models.entities import TalentInterest, User, UserRole
from app.schemas.schemas import TalentInterestCreate, TalentInterestRead, UserRead
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/search", response_model=list[UserRead])
def search_talent(
    skills: str | None = Query(default=None, description="Comma separated skills"),
    university: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_talent_hunter),
    db: Session = Depends(get_db),
) -> list[User]:
    query = db.query(User).filter(User.role == UserRole.student, User.is_active.is_(True))
    if university:
        query = query.filter(User.university.ilike(f"%{university}%"))
    if search:
        query = query.filter(User.full_name.ilike(f"%{search}%"))
    users = query.all()
    if skills:
        wanted = {skill.strip().lower() for skill in skills.split(",") if skill.strip()}
        users = [user for user in users if wanted.intersection({skill.lower() for skill in (user.skills or [])})]
    return users


@router.get("/students/{user_id}", response_model=UserRead)
def get_student(
    user_id: int,
    current_user: User = Depends(get_talent_hunter),
    db: Session = Depends(get_db),
) -> User:
    student = db.get(User, user_id)
    if not student or student.role != UserRole.student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/interest", response_model=TalentInterestRead, status_code=201)
def save_interest(
    payload: TalentInterestCreate,
    current_user: User = Depends(get_talent_hunter),
    db: Session = Depends(get_db),
) -> TalentInterest:
    student = db.get(User, payload.student_id)
    if not student or student.role != UserRole.student:
        raise HTTPException(status_code=404, detail="Student not found")
    interest = db.query(TalentInterest).filter_by(talent_hunter_id=current_user.id, student_id=student.id).first()
    if interest:
        interest.note = payload.note
    else:
        interest = TalentInterest(talent_hunter_id=current_user.id, **payload.model_dump())
        db.add(interest)
    db.commit()
    db.refresh(interest)
    return interest


@router.get("/saved", response_model=list[TalentInterestRead])
def saved_talent(
    current_user: User = Depends(get_talent_hunter), db: Session = Depends(get_db)
) -> list[TalentInterest]:
    return db.query(TalentInterest).filter_by(talent_hunter_id=current_user.id).all()


@router.get("/export")
def export_saved_talent(
    current_user: User = Depends(get_talent_hunter), db: Session = Depends(get_db)
):
    interests = db.query(TalentInterest).filter_by(talent_hunter_id=current_user.id).all()
    rows = [[interest.student_id, interest.note, interest.created_at.isoformat()] for interest in interests]
    return ExportService.csv_response("saved_talent.csv", ["student_id", "note", "created_at"], rows)
