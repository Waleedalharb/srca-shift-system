# backend/app/api/__init__.py
from fastapi import APIRouter
from app.api.endpoints import shifts, employees, centers, auth

api_router = APIRouter()

# ربط جميع المسارات
api_router.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(centers.router, prefix="/centers", tags=["centers"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])