from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import HackathonRegistration, Project, ProjectScore, ProjectStatus, Team


class AnalyticsService:
    @staticmethod
    def hackathon_summary(db: Session, hackathon_id: int) -> dict:
        registrations = db.query(HackathonRegistration).filter_by(hackathon_id=hackathon_id).count()
        teams = db.query(Team).filter_by(hackathon_id=hackathon_id).count()
        projects = db.query(Project).filter_by(hackathon_id=hackathon_id).count()
        submitted_projects = (
            db.query(Project)
            .filter(Project.hackathon_id == hackathon_id, Project.status != ProjectStatus.draft)
            .count()
        )
        average_score = (
            db.query(func.avg(ProjectScore.total_score))
            .join(Project, Project.id == ProjectScore.project_id)
            .filter(Project.hackathon_id == hackathon_id)
            .scalar()
        )
        return {
            "registrations": registrations,
            "teams": teams,
            "projects": projects,
            "submitted_projects": submitted_projects,
            "average_score": round(float(average_score), 2) if average_score is not None else None,
        }
