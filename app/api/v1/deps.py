from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import HackathonJudge, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = int(subject)
    except (JWTError, ValueError):
        raise credentials_exception from None

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user

    return dependency


def get_admin(current_user: User = Depends(require_roles(UserRole.admin))) -> User:
    return current_user


def get_organizer(current_user: User = Depends(require_roles(UserRole.hack_org, UserRole.admin))) -> User:
    return current_user


def get_talent_hunter(
    current_user: User = Depends(require_roles(UserRole.talent_hunter, UserRole.admin)),
) -> User:
    return current_user


def ensure_judge_for_project(db: Session, user: User, project_id: int) -> None:
    from app.models.entities import Project

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role == UserRole.admin:
        return
    judge_assignment = (
        db.query(HackathonJudge)
        .filter(HackathonJudge.hackathon_id == project.hackathon_id, HackathonJudge.judge_id == user.id)
        .first()
    )
    if not judge_assignment:
        raise HTTPException(status_code=403, detail="Judge assignment required")
