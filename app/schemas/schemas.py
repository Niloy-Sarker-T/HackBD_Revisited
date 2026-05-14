from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import (
    HackathonStatus,
    ProjectStatus,
    RegistrationStatus,
    ReportStatus,
    RoleRequestStatus,
    TeamMemberStatus,
    UserRole,
)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    university: str | None = None
    skills: list[str] = []


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    university: str | None = None
    bio: str | None = None
    skills: list[str] | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    university: str | None
    bio: str | None
    skills: list[str]
    github_url: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    is_active: bool
    created_at: datetime


class RoleRequestCreate(BaseModel):
    requested_role: Literal[UserRole.hack_org, UserRole.talent_hunter]
    reason: str = Field(min_length=10)
    university: str | None = None


class RoleRequestReview(BaseModel):
    note: str | None = None


class RoleRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    requested_role: UserRole
    reason: str
    university: str | None
    status: RoleRequestStatus
    reviewed_by_id: int | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime


class MeRead(UserRead):
    pending_role_requests: list[RoleRequestRead] = []


class HackathonBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    university: str | None = None
    theme: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    registration_deadline: datetime | None = None
    max_team_size: int = Field(default=4, ge=1, le=20)
    min_team_size: int = Field(default=1, ge=1, le=20)
    rules: str | None = None
    cover_image_url: str | None = None


class HackathonCreate(HackathonBase):
    pass


class HackathonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    university: str | None = None
    theme: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    registration_deadline: datetime | None = None
    max_team_size: int | None = Field(default=None, ge=1, le=20)
    min_team_size: int | None = Field(default=None, ge=1, le=20)
    rules: str | None = None
    cover_image_url: str | None = None


class HackathonRead(HackathonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organizer_id: int
    status: HackathonStatus
    winners: dict[str, Any] | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hackathon_id: int
    user_id: int
    status: RegistrationStatus
    created_at: datetime


class TeamCreate(BaseModel):
    hackathon_id: int
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    desired_skills: list[str] = []
    looking_for_members: bool = True


class TeamInvite(BaseModel):
    user_id: int


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hackathon_id: int
    leader_id: int
    name: str
    description: str | None
    desired_skills: list[str]
    looking_for_members: bool
    created_at: datetime


class TeamMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    user_id: int
    status: TeamMemberStatus
    created_at: datetime


class ProjectCreate(BaseModel):
    team_id: int
    title: str = Field(min_length=3, max_length=255)
    tagline: str | None = Field(default=None, max_length=280)
    description: str = Field(min_length=10)
    repo_url: str | None = None
    demo_url: str | None = None
    image_urls: list[str] = []


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    tagline: str | None = Field(default=None, max_length=280)
    description: str | None = Field(default=None, min_length=10)
    repo_url: str | None = None
    demo_url: str | None = None
    image_urls: list[str] | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hackathon_id: int
    team_id: int
    creator_id: int
    title: str
    tagline: str | None
    description: str
    repo_url: str | None
    demo_url: str | None
    image_urls: list[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectScoreCreate(BaseModel):
    criteria_scores: dict[str, float] = Field(default_factory=dict)
    total_score: float = Field(ge=0, le=100)
    feedback: str | None = None


class ProjectScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    judge_id: int
    criteria_scores: dict[str, float]
    total_score: float
    feedback: str | None
    created_at: datetime


class TalentInterestCreate(BaseModel):
    student_id: int
    note: str | None = None


class TalentInterestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    talent_hunter_id: int
    student_id: int
    note: str | None
    created_at: datetime


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    type: str
    read_at: datetime | None
    created_at: datetime


class ReportCreate(BaseModel):
    target_type: Literal["user", "project", "hackathon"]
    target_id: int
    reason: str = Field(min_length=5)


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    status: ReportStatus
    admin_note: str | None
    created_at: datetime


class JudgeAssign(BaseModel):
    judge_user_id: int


class WinnerDeclare(BaseModel):
    winners: dict[str, Any]


class AdminRoleChange(BaseModel):
    role: UserRole


class HackathonStatusUpdate(BaseModel):
    status: HackathonStatus


class AnalyticsRead(BaseModel):
    registrations: int
    teams: int
    projects: int
    submitted_projects: int
    average_score: float | None
