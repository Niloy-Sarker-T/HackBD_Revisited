from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    student = "student"
    hack_org = "hack_org"
    talent_hunter = "talent_hunter"
    judge = "judge"
    admin = "admin"


class RoleRequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class HackathonStatus(str, Enum):
    draft = "draft"
    published = "published"
    hidden = "hidden"
    archived = "archived"
    completed = "completed"


class RegistrationStatus(str, Enum):
    registered = "registered"
    waitlisted = "waitlisted"
    cancelled = "cancelled"


class TeamMemberStatus(str, Enum):
    invited = "invited"
    accepted = "accepted"
    declined = "declined"
    left = "left"


class ProjectStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class ReportStatus(str, Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.student, index=True)
    university: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    role_requests: Mapped[list["RoleRequest"]] = relationship(
    back_populates="user",
    foreign_keys="RoleRequest.user_id"
    )
    organized_hackathons: Mapped[list["Hackathon"]] = relationship(
    back_populates="organizer",
    foreign_keys="Hackathon.organizer_id"
    )


class RoleRequest(Base, TimestampMixin):
    __tablename__ = "role_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    requested_role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    university: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[RoleRequestStatus] = mapped_column(
        SQLEnum(RoleRequestStatus), default=RoleRequestStatus.pending, index=True
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="role_requests")
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_id])


class Hackathon(Base, TimestampMixin):
    __tablename__ = "hackathons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    university: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    theme: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    status: Mapped[HackathonStatus] = mapped_column(
        SQLEnum(HackathonStatus), default=HackathonStatus.draft, index=True
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_team_size: Mapped[int] = mapped_column(Integer, default=4)
    min_team_size: Mapped[int] = mapped_column(Integer, default=1)
    rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    winners: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organizer: Mapped["User"] = relationship(
    back_populates="organized_hackathons",
    foreign_keys=[organizer_id]
    )
    registrations: Mapped[list["HackathonRegistration"]] = relationship(back_populates="hackathon")
    teams: Mapped[list["Team"]] = relationship(back_populates="hackathon")
    projects: Mapped[list["Project"]] = relationship(back_populates="hackathon")
    judges: Mapped[list["HackathonJudge"]] = relationship(back_populates="hackathon")


class HackathonRegistration(Base, TimestampMixin):
    __tablename__ = "hackathon_registrations"
    __table_args__ = (UniqueConstraint("hackathon_id", "user_id", name="uq_registration_user_hackathon"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        SQLEnum(RegistrationStatus), default=RegistrationStatus.registered
    )

    hackathon: Mapped["Hackathon"] = relationship(back_populates="registrations")
    user: Mapped["User"] = relationship()


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), nullable=False, index=True)
    leader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    desired_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    looking_for_members: Mapped[bool] = mapped_column(Boolean, default=True)

    hackathon: Mapped["Hackathon"] = relationship(back_populates="teams")
    leader: Mapped["User"] = relationship()
    members: Mapped[list["TeamMember"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    project: Mapped["Project | None"] = relationship(back_populates="team")


class TeamMember(Base, TimestampMixin):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[TeamMemberStatus] = mapped_column(
        SQLEnum(TeamMemberStatus), default=TeamMemberStatus.accepted
    )

    team: Mapped["Team"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("team_id", name="uq_project_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tagline: Mapped[str | None] = mapped_column(String(280), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[ProjectStatus] = mapped_column(SQLEnum(ProjectStatus), default=ProjectStatus.draft)

    hackathon: Mapped["Hackathon"] = relationship(back_populates="projects")
    team: Mapped["Team"] = relationship(back_populates="project")
    creator: Mapped["User"] = relationship()
    scores: Mapped[list["ProjectScore"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectScore(Base, TimestampMixin):
    __tablename__ = "project_scores"
    __table_args__ = (UniqueConstraint("project_id", "judge_id", name="uq_project_judge_score"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    judge_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    criteria_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="scores")
    judge: Mapped["User"] = relationship()


class TalentInterest(Base, TimestampMixin):
    __tablename__ = "talent_interests"
    __table_args__ = (UniqueConstraint("talent_hunter_id", "student_id", name="uq_talent_interest"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    talent_hunter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    talent_hunter: Mapped["User"] = relationship(foreign_keys=[talent_hunter_id])
    student: Mapped["User"] = relationship(foreign_keys=[student_id])


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(80), default="info")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()


class HackathonJudge(Base, TimestampMixin):
    __tablename__ = "hackathon_judges"
    __table_args__ = (UniqueConstraint("hackathon_id", "judge_id", name="uq_hackathon_judge"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), nullable=False, index=True)
    judge_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    hackathon: Mapped["Hackathon"] = relationship(back_populates="judges")
    judge: Mapped["User"] = relationship()


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(SQLEnum(ReportStatus), default=ReportStatus.open)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    reporter: Mapped["User"] = relationship()


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    hackathon_id: Mapped[int | None] = mapped_column(ForeignKey("hackathons.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    actor: Mapped["User | None"] = relationship()
