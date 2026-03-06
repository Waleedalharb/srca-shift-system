# backend/app/services/report_service.py
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime, date
from ..core.security import UserRole, Permission, check_permission

class ReportService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.user = current_user
    
    def get_dashboard_data(self) -> Dict:
        """لوحة المعلومات حسب صلاحية المستخدم"""
        
        dashboard = {
            'user_info': {
                'name': self.user.full_name,
                'role': self.user.role.name,
                'station': self.user.station.name if self.user.station else None
            }
        }
        
        # لكبير المسعفين - نظرة شاملة على القطاع
        if self.user.role == UserRole.CHIEF_PARAMEDIC:
            dashboard['sector_overview'] = self._get_sector_overview()
            dashboard['stations_comparison'] = self._compare_stations()
            dashboard['sector_kpi'] = self._calculate_sector_kpi()
        
        # للقيادة الميدانية - محطته فقط
        elif self.user.role == UserRole.FIELD_LEADER:
            dashboard['station_details'] = self._get_station_details(self.user.station_id)
            dashboard['crew_status'] = self._get_crew_status()
            dashboard['leaves_pending'] = self._get_pending_leaves()
        
        # للتحكم العملياتي - البلاغات والاستجابة
        elif self.user.role == UserRole.OPERATIONS_CONTROL:
            dashboard['active_incidents'] = self._get_active_incidents()
            dashboard['response_times'] = self._get_response_times()
            dashboard['available_crews'] = self._get_available_crews()
        
        # للمسعفين والأخصائيين - جداولهم ومهامهم
        elif self.user.role in [UserRole.PARAMEDIC, UserRole.EMT]:
            dashboard['my_schedule'] = self._get_employee_schedule()
            dashboard['my_missions'] = self._get_employee_missions()
            dashboard['leave_balance'] = self._get_leave_balance()
        
        return dashboard
    
    def _get_station_details(self, station_id: str) -> Dict:
        """تفاصيل المحطة للقيادة الميدانية"""
        return {
            'total_staff': self._count_staff(station_id),
            'on_duty': self._count_on_duty(station_id),
            'on_leave': self._count_on_leave(station_id),
            'today_roster': self._get_today_roster(station_id),
            'weekly_kpi': self._calculate_weekly_kpi(station_id)
        }
    
    def _get_available_crews(self) -> List[Dict]:
        """الفرق المتاحة للتحكم العملياتي"""
        return self.db.query(Employee).filter(
            Employee.on_duty == True,
            Employee.available == True
        ).all()