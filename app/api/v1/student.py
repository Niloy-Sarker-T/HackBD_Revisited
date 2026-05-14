from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_db
from app.models.entities import (
    Hackathon,
    HackathonRegistration,
    HackathonStatus,
    Project,
    ProjectStatus,
    RegistrationStatus,
    Team,
    TeamMember,
    TeamMemberStatus,
    User,
)
from app.schemas.schemas import (
    HackathonRead,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    RegistrationRead,
    TeamCreate,
    TeamInvite,
    TeamMemberRead,
    TeamRead,
    UserRead,
)
from app.services.notification_service import NotificationService
from app.services.team_matching_service import TeamMatchingService

router = APIRouter()


def require_team_member(db: Session, team_id: int, user_id: int) -> TeamMember:
    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.status == TeamMemberStatus.accepted,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Accepted team membership required")
    return member


@router.post("/hackathons/{hackathon_id}/register", response_model=RegistrationRead, status_code=201)
def register_for_hackathon(
    hackathon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HackathonRegistration:
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon or hackathon.deleted_at or hackathon.status != HackathonStatus.published:
        raise HTTPException(status_code=404, detail="Published hackathon not found")
    existing = (
        db.query(HackathonRegistration)
        .filter(HackathonRegistration.hackathon_id == hackathon_id, HackathonRegistration.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already registered")
    registration = HackathonRegistration(hackathon_id=hackathon_id, user_id=current_user.id)
    db.add(registration)
    NotificationService.notify(
        db,
        current_user.id,
        "Registration confirmed",
        f"You are registered for {hackathon.title}.",
        "hackathon_registration",
    )
    db.commit()
    db.refresh(registration)
    return registration


@router.get("/student/registrations", response_model=list[RegistrationRead])
def my_registrations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[HackathonRegistration]:
    return db.query(HackathonRegistration).filter_by(user_id=current_user.id).all()


@router.get("/student/hackathons/participated", response_model=list[HackathonRead])
def participated_hackathons(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Hackathon]:
    return (
        db.query(Hackathon)
        .join(HackathonRegistration, HackathonRegistration.hackathon_id == Hackathon.id)
        .filter(HackathonRegistration.user_id == current_user.id)
        .all()
    )


@router.post("/teams", response_model=TeamRead, status_code=201)
def create_team(
    payload: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Team:
    registration = (
        db.query(HackathonRegistration)
        .filter(
            HackathonRegistration.hackathon_id == payload.hackathon_id,
            HackathonRegistration.user_id == current_user.id,
            HackathonRegistration.status == RegistrationStatus.registered,
        )
        .first()
    )
    if not registration:
        raise HTTPException(status_code=403, detail="Hackathon registration required before creating a team")
    team = Team(
        hackathon_id=payload.hackathon_id,
        leader_id=current_user.id,
        name=payload.name,
        description=payload.description,
        desired_skills=payload.desired_skills,
        looking_for_members=payload.looking_for_members,
    )
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=current_user.id, status=TeamMemberStatus.accepted))
    db.commit()
    db.refresh(team)
    return team


@router.post("/teams/{team_id}/invite", response_model=TeamMemberRead, status_code=201)
def invite_member(
    team_id: int,
    payload: TeamInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamMember:
    team = db.get(Team, team_id)
    if not team or team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team leader can invite members")
    invite = TeamMember(team_id=team.id, user_id=payload.user_id, status=TeamMemberStatus.invited)
    db.add(invite)
    NotificationService.notify(db, payload.user_id, "Team invite", f"You were invited to join {team.name}.", "team")
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/teams/{team_id}/join", response_model=TeamMemberRead)
def join_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamMember:
    team = db.get(Team, team_id)
    if not team or not team.looking_for_members:
        raise HTTPException(status_code=404, detail="Open team not found")
    member = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id).first()
    if member:
        member.status = TeamMemberStatus.accepted
    else:
        member = TeamMember(team_id=team_id, user_id=current_user.id, status=TeamMemberStatus.accepted)
        db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.post("/teams/{team_id}/leave", response_model=TeamMemberRead)
def leave_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamMember:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.leader_id == current_user.id:
        raise HTTPException(status_code=400, detail="Team leader cannot leave without transferring ownership")
    member = require_team_member(db, team_id, current_user.id)
    member.status = TeamMemberStatus.left
    db.commit()
    db.refresh(member)
    return member


@router.get("/teams/{team_id}/recommend", response_model=list[UserRead])
def recommend_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    require_team_member(db, team.id, current_user.id)
    return TeamMatchingService.recommend_members(db, team)


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    team = db.get(Team, payload.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    require_team_member(db, team.id, current_user.id)
    project = Project(
        hackathon_id=team.hackathon_id,
        team_id=team.id,
        creator_id=current_user.id,
        title=payload.title,
        tagline=payload.tagline,
        description=payload.description,
        repo_url=payload.repo_url,
        demo_url=payload.demo_url,
        image_urls=payload.image_urls,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/projects/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_team_member(db, project.team_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/projects/{project_id}/submit", response_model=ProjectRead)
def submit_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_team_member(db, project.team_id, current_user.id)
    project.status = ProjectStatus.submitted
    db.commit()
    db.refresh(project)
    return project
