# backend/app/services/analytics_service.py
from sqlalchemy import func, and_, extract
from typing import Dict, List
from datetime import datetime, timedelta

class AnalyticsService:
    def __init__(self, db_session):
        self.db = db_session
    
    def calculate_shift_kpis(self, shift_id: str) -> Dict:
        """حساب مؤشرات الأداء لنوبة محددة"""
        
        # متوسط زمن الاستجابة
        avg_response_time = self.db.query(
            func.avg(Incident.response_time)
        ).filter(Incident.shift_id == shift_id).scalar()
        
        # عدد البلاغات
        incidents_count = self.db.query(
            func.count(Incident.id)
        ).filter(Incident.shift_id == shift_id).scalar()
        
        # نسبة الغياب
        total_staff = self.db.query(
            func.count(ShiftAssignment.id)
        ).filter(ShiftAssignment.shift_id == shift_id).scalar()
        
        absent_staff = self.db.query(
            func.count(Attendance.id)
        ).filter(
            and_(
                Attendance.shift_id == shift_id,
                Attendance.status == 'absent'
            )
        ).scalar()
        
        absence_rate = (absent_staff / total_staff * 100) if total_staff > 0 else 0
        
        # ساعات العمل الفعلية
        actual_hours = self.db.query(
            func.sum(Attendance.actual_hours)
        ).filter(Attendance.shift_id == shift_id).scalar() or 0
        
        planned_hours = self.db.query(
            func.sum(ShiftAssignment.planned_hours)
        ).filter(ShiftAssignment.shift_id == shift_id).scalar() or 0
        
        efficiency_rate = (actual_hours / planned_hours * 100) if planned_hours > 0 else 0
        
        return {
            'avg_response_time': round(avg_response_time, 2) if avg_response_time else 0,
            'incidents_count': incidents_count,
            'absence_rate': round(absence_rate, 2),
            'efficiency_rate': round(efficiency_rate, 2),
            'operational_completion': round(100 - absence_rate, 2)
        }
    
    def get_station_performance(self, station_id: str, days: int = 30) -> Dict:
        """تحليل أداء المحطة خلال فترة"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        shifts = self.db.query(Shift).filter(
            and_(
                Shift.station_id == station_id,
                Shift.date.between(start_date, end_date)
            )
        ).all()
        
        performance_data = []
        for shift in shifts:
            kpis = self.calculate_shift_kpis(shift.id)
            performance_data.append({
                'date': shift.date,
                **kpis
            })
        
        return {
            'station_id': station_id,
            'period': f'{days} days',
            'average': self._calculate_averages(performance_data),
            'trend': self._calculate_trends(performance_data),
            'recommendations': self._generate_recommendations(performance_data)
        }