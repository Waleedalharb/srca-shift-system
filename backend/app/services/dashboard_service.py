# backend/app/services/dashboard_service.py
class CentersDashboardService:
    """لوحة معلومات المراكز الإسعافية"""
    
    def get_centers_overview(self) -> Dict:
        """نظرة عامة على جميع المراكز"""
        
        centers = self.db.query(EmergencyCenter).all()
        
        return {
            'summary': {
                'total_centers': len(centers),
                'active_centers': sum(1 for c in centers if c.is_active),
                'avg_coverage': self._calculate_avg_coverage(centers),
                'centers_above_target': self._count_centers_above_target(centers)
            },
            'centers_list': [
                {
                    'name': c.name,
                    'coverage': self._calculate_center_coverage(c.id),
                    'staff_count': self._count_center_staff(c.id),
                    'available_crews': self._count_available_crews(c.id),
                    'response_time': self._get_center_avg_response_time(c.id),
                    'status': self._get_center_status(c.id)
                }
                for c in centers
            ],
            'coverage_chart': self._generate_coverage_chart(centers),
            'bottlenecks': self._identify_bottlenecks()
        }