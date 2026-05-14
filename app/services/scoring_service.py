from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import Project, ProjectScore


class ScoringService:
    @staticmethod
    def average_for_project(db: Session, project_id: int) -> float | None:
        value = db.query(func.avg(ProjectScore.total_score)).filter(ProjectScore.project_id == project_id).scalar()
        return round(float(value), 2) if value is not None else None

    @staticmethod
    def rankings_for_hackathon(db: Session, hackathon_id: int) -> list[dict]:
        rows = (
            db.query(Project, func.avg(ProjectScore.total_score).label("average_score"))
            .join(ProjectScore, ProjectScore.project_id == Project.id, isouter=True)
            .filter(Project.hackathon_id == hackathon_id)
            .group_by(Project.id)
            .order_by(func.avg(ProjectScore.total_score).desc().nullslast())
            .all()
        )
        return [
            {
                "rank": index + 1,
                "project_id": project.id,
                "title": project.title,
                "average_score": round(float(avg), 2) if avg is not None else None,
            }
            for index, (project, avg) in enumerate(rows)
        ]
