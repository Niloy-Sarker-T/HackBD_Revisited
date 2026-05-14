from fastapi import APIRouter

from app.api.v1 import admin, auth, judge, organizer, public, student, talent, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(public.router, tags=["public"])
api_router.include_router(users.router, tags=["me"])
api_router.include_router(student.router, tags=["student"])
api_router.include_router(organizer.router, prefix="/organizer", tags=["organizer"])
api_router.include_router(judge.router, tags=["judge"])
api_router.include_router(talent.router, prefix="/talent", tags=["talent"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
