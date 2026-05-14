"""
Background task placeholder.

For the academic backend, notifications are persisted synchronously so the API is runnable
without Redis. A real deployment can wire Celery here for welcome emails, reminders,
team invites, winner announcements, and talent digests.
"""

try:
    from celery import Celery
except ImportError:  # pragma: no cover
    Celery = None


celery_app = Celery("hackbd") if Celery else None
