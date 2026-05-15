from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import Base, SessionLocal, engine
from app.models.entities import User, UserRole


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        seed_admin()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def seed_admin() -> None:
    if not settings.FIRST_ADMIN_EMAIL or not settings.FIRST_ADMIN_PASSWORD:
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.FIRST_ADMIN_EMAIL).first()
        if existing:
            return
        admin = User(
            email=settings.FIRST_ADMIN_EMAIL,
            full_name="Platform Admin",
            hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


app = create_app()
