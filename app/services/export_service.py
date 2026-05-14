import csv
import io

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.entities import HackathonRegistration, Project, Team


class ExportService:
    @staticmethod
    def csv_response(filename: str, headers: list[str], rows: list[list[str | int | float | None]]) -> StreamingResponse:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)
        writer.writerows(rows)
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @staticmethod
    def registrations_csv(db: Session, hackathon_id: int) -> StreamingResponse:
        registrations = db.query(HackathonRegistration).filter_by(hackathon_id=hackathon_id).all()
        rows = [[item.id, item.user_id, item.status.value, item.created_at.isoformat()] for item in registrations]
        return ExportService.csv_response("registrations.csv", ["id", "user_id", "status", "created_at"], rows)

    @staticmethod
    def teams_csv(db: Session, hackathon_id: int) -> StreamingResponse:
        teams = db.query(Team).filter_by(hackathon_id=hackathon_id).all()
        rows = [[team.id, team.name, team.leader_id, len(team.members)] for team in teams]
        return ExportService.csv_response("teams.csv", ["id", "name", "leader_id", "members"], rows)

    @staticmethod
    def projects_csv(db: Session, hackathon_id: int) -> StreamingResponse:
        projects = db.query(Project).filter_by(hackathon_id=hackathon_id).all()
        rows = [[project.id, project.title, project.team_id, project.status.value] for project in projects]
        return ExportService.csv_response("projects.csv", ["id", "title", "team_id", "status"], rows)
