# backend/app/api/endpoints/prediction.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.api import deps
from app.models.user import User
from app.services.prediction_service import PredictionService

router = APIRouter()

@router.get("/train")
def train_prediction_model(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    force: bool = Query(False, description="إعادة التدريب")
):
    """تدريب نموذج التنبؤ (للمشرفين فقط)"""
    
    if current_user.role.value not in ["chief_paramedic", "operations_supervisor"]:
        raise HTTPException(status_code=403, detail="غير مصرح")
    
    service = PredictionService(db)
    service.train_model(force_retrain=force)
    
    return {"message": "✅ تم تدريب النموذج بنجاح"}

@router.get("/predict/day")
def predict_day(
    date_str: str = Query(..., description="التاريخ YYYY-MM-DD"),
    staff: int = Query(30, description="عدد الموظفين المتاحين"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """التنبؤ ليوم محدد"""
    
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        raise HTTPException(status_code=400, detail="صيغة التاريخ غير صحيحة")
    
    service = PredictionService(db)
    service.load_model()
    
    prediction = service.predict_day(date, staff)
    return prediction

@router.get("/predict/month")
def predict_month(
    year: int = Query(..., description="السنة"),
    month: int = Query(..., description="الشهر"),
    staff: int = Query(30, description="عدد الموظفين المتاحين"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """التنبؤ لشهر كامل"""
    
    service = PredictionService(db)
    service.load_model()
    
    predictions = service.predict_month(year, month, staff)
    return predictions

@router.get("/analyze/ramadan")
def analyze_ramadan(
    year: int = Query(2026, description="السنة"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """تحليل خاص لشهر رمضان"""
    
    # رمضان 2026 يبدأ تقريباً 18 فبراير (تقديري)
    ramadan_start = datetime(year, 2, 18)
    ramadan_end = datetime(year, 3, 19)
    
    service = PredictionService(db)
    service.load_model()
    
    predictions = []
    current = ramadan_start
    while current <= ramadan_end:
        pred = service.predict_day(current, 30)
        predictions.append(pred)
        current += timedelta(days=1)
    
    # تحليل النتائج
    avg_calls = sum(p['predicted_calls'] for p in predictions) / len(predictions)
    peak_days = [p for p in predictions if p['predicted_calls'] > 60]
    
    return {
        "ramadan_year": year,
        "start_date": ramadan_start.strftime("%Y-%m-%d"),
        "end_date": ramadan_end.strftime("%Y-%m-%d"),
        "average_daily_calls": round(avg_calls, 1),
        "peak_days_count": len(peak_days),
        "peak_days": peak_days[:5],  # أول 5 أيام ذروة
        "recommendation": f"🔴 يفضل زيادة المناوبات بنسبة 25% في {len(peak_days)} يوم"
    }