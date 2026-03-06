# backend/app/services/kpi_service.py
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

class CenterKPIService:
    """مؤشرات أداء المراكز الإسعافية"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_chief_paramedic_kpi(self) -> Dict:
        """مؤشرات كبير المسعفين (مدير القطاع)"""
        
        # حساب متوسط تغطية جميع المراكز
        centers = self.db.query(EmergencyCenter).all()
        centers_coverage = []
        
        for center in centers:
            coverage = self._calculate_center_coverage(center.id)
            centers_coverage.append({
                'center_name': center.name,
                'coverage': coverage,
                'status': 'جيد' if coverage >= 85 else 'تحتاج تدعيم'
            })
        
        # متوسط التغطية للقطاع
        avg_coverage = sum(c['coverage'] for c in centers_coverage) / len(centers_coverage) if centers_coverage else 0
        
        return {
            'sector_overview': {
                'total_centers': len(centers),
                'avg_coverage_percentage': round(avg_coverage, 2),
                'centers_needing_support': [c for c in centers_coverage if c['coverage'] < 85],
                'centers_details': centers_coverage
            },
            'centers_readiness': self._get_centers_readiness(),
            'response_time_avg': self._get_sector_response_time(),
            'staff_distribution': self._get_staff_distribution(),
            'annual_goals_achievement': self._calculate_annual_goals(),
        }
    
    def _calculate_center_coverage(self, center_id: str) -> float:
        """حساب نسبة تغطية مركز إسعافي"""
        center = self.db.query(EmergencyCenter).get(center_id)
        
        if not center:
            return 0
        
        # العوامل المؤثرة في التغطية:
        # 1. توفر الكوادر
        staff_available = self.db.query(Employee).filter(
            and_(
                Employee.center_id == center_id,
                Employee.is_on_duty == True,
                Employee.is_available == True
            )
        ).count()
        
        required_staff = center.ideal_crew.get('paramedics', 0) + center.ideal_crew.get('emts', 0)
        staff_factor = min(100, (staff_available / required_staff * 100)) if required_staff > 0 else 0
        
        # 2. توفر السيارات
        ambulances_available = self.db.query(Ambulance).filter(
            and_(
                Ambulance.center_id == center_id,
                Ambulance.is_operational == True
            )
        ).count()
        
        required_ambulances = center.ideal_crew.get('ambulances', 2)
        ambulance_factor = min(100, (ambulances_available / required_ambulances * 100)) if required_ambulances > 0 else 0
        
        # 3. أداء الفريق (بناءً على أوقات الاستجابة)
        performance_factor = self._get_center_performance(center_id)
        
        # الوزن النسبي لكل عامل
        weights = {
            'staff': 0.5,      # 50%
            'ambulances': 0.3,  # 30%
            'performance': 0.2  # 20%
        }
        
        total_coverage = (
            staff_factor * weights['staff'] +
            ambulance_factor * weights['ambulances'] +
            performance_factor * weights['performance']
        )
        
        return round(total_coverage, 2)
    
    def get_field_leader_kpi(self, center_id: str) -> Dict:
        """مؤشرات القيادة الميدانية (مشرف المركز)"""
        center = self.db.query(EmergencyCenter).get(center_id)
        
        # نسبة اكتمال الطاقم
        crew_completeness = self._calculate_center_coverage(center_id)
        
        # تعارضات الإجازات
        leave_conflicts = self._count_leave_conflicts(center_id)
        
        # ساعات العمل الإضافية
        overtime_hours = self._calculate_overtime(center_id)
        
        # عدد البلاغات
        incidents_count = self._count_center_incidents(center_id)
        
        # جاهزية الفريق
        team_readiness = self._calculate_team_readiness(center_id)
        
        return {
            'center_name': center.name,
            'coverage_percentage': crew_completeness,
            'coverage_status': 'ممتاز' if crew_completeness >= 90 else 'جيد' if crew_completeness >= 75 else 'ضعيف',
            'leave_conflicts': leave_conflicts,
            'overtime_hours': overtime_hours,
            'monthly_incidents': incidents_count,
            'team_readiness': team_readiness,
            'recommendations': self._generate_center_recommendations(center_id, crew_completeness)
        }
    
    def get_operations_control_kpi(self) -> Dict:
        """مؤشرات التحكم العملياتي"""
        
        # متوسط زمن الاستجابة لكل مركز
        centers_response = []
        centers = self.db.query(EmergencyCenter).all()
        
        for center in centers:
            avg_time = self._get_center_avg_response_time(center.id)
            centers_response.append({
                'center': center.name,
                'avg_response_time': avg_time,
                'performance': 'ممتاز' if avg_time <= 8 else 'جيد' if avg_time <= 12 else 'ضعيف'
            })
        
        return {
            'response_times': {
                'sector_average': self._get_sector_response_time(),
                'centers_breakdown': centers_response
            },
            'missions_stats': {
                'total_today': self._count_today_missions(),
                'peak_hours': self._get_peak_hours(),
                'busiest_center': self._get_busiest_center()
            },
            'resource_utilization': self._calculate_resource_utilization(),
            'dispatch_efficiency': self._calculate_dispatch_efficiency()
        }
    
    def _generate_center_recommendations(self, center_id: str, coverage: float) -> List[str]:
        """توليد توصيات للمركز"""
        recommendations = []
        
        if coverage < 70:
            recommendations.append("🔴 نقص حاد في الكوادر - تحتاج تدعيم فوري")
        elif coverage < 85:
            recommendations.append("🟡 نقص في الكوادر - يفضل توفير مسعفين إضافيين")
        
        # تحقق من الإجازات المتعارضة
        if self._count_leave_conflicts(center_id) > 3:
            recommendations.append("⚠️ يوجد تعارض في الإجازات - مراجعة جدول الإجازات")
        
        # تحقق من ساعات العمل الإضافية
        if self._calculate_overtime(center_id) > 100:
            recommendations.append("📊 ساعات عمل إضافية مرتفعة - توزيع المهام")
        
        return recommendations