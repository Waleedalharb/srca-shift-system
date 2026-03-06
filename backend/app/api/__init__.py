# backend/app/api/__init__.py
from fastapi import APIRouter
from .endpoints import auth, employees, centers, shifts, leaves, incidents, reports

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, prefix="/auth", tags=["المصادقة"])
api_router.include_router(employees.router, prefix="/employees", tags=["الموظفين"])
api_router.include_router(centers.router, prefix="/centers", tags=["المراكز"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["المناوبات"])
api_router.include_router(leaves.router, prefix="/leaves", tags=["الإجازات"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["البلاغات"])
api_router.include_router(reports.router, prefix="/reports", tags=["التقارير"])