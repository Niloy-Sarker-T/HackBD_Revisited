
# HackBD Backend

FastAPI backend for an academic hackathon platform. It is designed to be runnable
and extendable, not just a toy scaffold.

## Tech Stack

- FastAPI + Uvicorn
- SQLAlchemy ORM
- Alembic migration scaffold
- SQLite by default, configurable with `DATABASE_URL`
- JWT authentication
- Role-based access control
- CSV exports for organizer/talent workflows

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API docs:

- `http://localhost:8000/docs`
- `http://localhost:8000/health`

## Frontend

The connected frontend lives in `frontend/`. It is a dependency-free neo-brutalist
console. In development it calls same-origin `/api/v1/...`, and the static server
proxies `/api/*` plus `/health` to FastAPI at `http://127.0.0.1:8000`.

```bash
cd frontend
npm run dev
```

Open:

- `http://localhost:5173`

The UI includes login/register, public hackathon discovery, role requests, student
actions, organizer actions, judge scoring, talent search, and admin moderation.

To point the frontend proxy at a different backend:

```bash
set BACKEND_URL=http://127.0.0.1:8000
npm run dev
```

The optional bootstrap admin is controlled by `.env`:

```env
FIRST_ADMIN_EMAIL="admin@example.com"
FIRST_ADMIN_PASSWORD="admin12345"
```

## Implemented

- `User.role`: `student`, `hack_org`, `talent_hunter`, `judge`, `admin`
- Role request and admin approval flow:
  - `POST /api/v1/me/request-role`
  - `GET /api/v1/admin/role-requests`
  - `POST /api/v1/admin/role-requests/{request_id}/approve`
  - `POST /api/v1/admin/role-requests/{request_id}/reject`
  - `GET /api/v1/me`
- Public hackathon/project/profile APIs
- Auth APIs:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
- Student registration, team, team invite/join/leave/recommendation APIs
- Project create/update/submit APIs
- Organizer hackathon CRUD, publish/unpublish, soft delete
- Organizer registrations, teams, projects, judges, analytics, CSV exports
- Organizer project approve/reject
- Winner declaration
- Judge assignments and project scoring
- Talent hunter search, saved interest, CSV export
- Admin hackathon moderation, users, direct role change, reports
- Database models requested in the plan:
  - `User`
  - `RoleRequest`
  - `Hackathon`
  - `HackathonRegistration`
  - `Team`
  - `TeamMember`
  - `Project`
  - `ProjectScore`
  - `TalentInterest`
  - `Notification`
  - `HackathonJudge`
  - `Report`
  - `ActivityLog`
- Service layer:
  - `RoleRequestService`
  - `NotificationService`
  - `TeamMatchingService`
  - `ScoringService`
  - `AnalyticsService`
  - `ExportService`

## Migrations

For quick academic demos, tables are created automatically on app startup. For a
proper migration workflow:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## Convenience Stubs / Not Fully Implemented Yet

- Celery + Redis tasks are represented by `app/tasks/celery_app.py`, but real email
  sending and scheduled reminders are not wired yet.
- Binary file uploads are not implemented yet. Projects currently accept image URLs.
- Rate limiting is not implemented yet.
- An initial Alembic revision file has not been generated yet; the Alembic scaffold
  is ready for `revision --autogenerate`.
- Hackathon templates and post-hackathon feedback are not implemented yet.
- PDF export is not implemented yet; CSV export is working at the service/API level.

## Important Flow

1. Register a user with `POST /api/v1/auth/register`.
2. Login with `POST /api/v1/auth/login`.
3. Request organizer role with `POST /api/v1/me/request-role`.
4. Login as admin and approve the request.
5. The user can immediately create hackathons at `POST /api/v1/organizer/hackathons`.

## Tests

```bash
pytest
```

The smoke test covers registration, role request approval, organizer promotion,
hackathon creation, and publishing.
