from sqlalchemy.orm import Session

from app.models.entities import HackathonRegistration, Team, TeamMember, TeamMemberStatus, User


class TeamMatchingService:
    @staticmethod
    def recommend_members(db: Session, team: Team, limit: int = 10) -> list[User]:
        member_ids = {
            row.user_id
            for row in db.query(TeamMember).filter(
                TeamMember.team_id == team.id,
                TeamMember.status.in_([TeamMemberStatus.accepted, TeamMemberStatus.invited]),
            )
        }
        registered_users = (
            db.query(User)
            .join(HackathonRegistration, HackathonRegistration.user_id == User.id)
            .filter(HackathonRegistration.hackathon_id == team.hackathon_id, ~User.id.in_(member_ids or {0}))
            .all()
        )
        desired = {skill.lower() for skill in (team.desired_skills or [])}
        ranked = sorted(
            registered_users,
            key=lambda user: len(desired.intersection({skill.lower() for skill in (user.skills or [])})),
            reverse=True,
        )
        return ranked[:limit]
