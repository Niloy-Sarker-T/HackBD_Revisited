from sqlalchemy.orm import Session

from app.models.entities import Notification


class NotificationService:
    @staticmethod
    def notify(db: Session, user_id: int, title: str, message: str, type_: str = "info") -> Notification:
        notification = Notification(user_id=user_id, title=title, message=message, type=type_)
        db.add(notification)
        return notification
