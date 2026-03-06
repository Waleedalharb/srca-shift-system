# frontend/services/employee_service.py
import requests
import streamlit as st
from config import config

class EmployeeService:
    def __init__(self, auth_service):
        self.base_url = f"{config.API_URL}/employees"
        self.auth = auth_service
    
    def get_stats(self):
        """إحصائيات الموظفين"""
        try:
            response = requests.get(
                f"{self.base_url}/stats/overview",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"خطأ في جلب الإحصائيات: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 لا يمكن الاتصال بالخادم. تأكد من تشغيل السيرفر")
            return None
        except Exception as e:
            st.error(f"خطأ في جلب الإحصائيات: {str(e)}")
            return None
    
    def get_employees(self, center_id=None, search=None, employee_type=None, skip=0, limit=100):
        """قائمة الموظفين مع إمكانية التصفية حسب المركز والبحث والنوع"""
        try:
            params = {"skip": skip, "limit": limit}
            if center_id:
                params["center_id"] = center_id
            if search:
                params["search"] = search
            if employee_type:
                params["employee_type"] = employee_type
                
            response = requests.get(
                self.base_url,
                headers=self.auth.get_headers(),
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"خطأ في جلب الموظفين: {response.status_code}")
                return {"total": 0, "items": []}
        except requests.exceptions.ConnectionError:
            st.error("🔌 لا يمكن الاتصال بالخادم. تأكد من تشغيل السيرفر")
            return {"total": 0, "items": []}
        except Exception as e:
            st.error(f"خطأ في جلب الموظفين: {str(e)}")
            return {"total": 0, "items": []}
    
    def get_employee(self, employee_id):
        """بيانات موظف محدد"""
        try:
            response = requests.get(
                f"{self.base_url}/{employee_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                st.error("الموظف غير موجود")
                return None
            else:
                st.error(f"خطأ في جلب بيانات الموظف: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 لا يمكن الاتصال بالخادم. تأكد من تشغيل السيرفر")
            return None
        except Exception as e:
            st.error(f"خطأ في جلب بيانات الموظف: {str(e)}")
            return None
    
    def create_employee(self, data):
        """إضافة موظف جديد"""
        try:
            response = requests.post(
                self.base_url,
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                st.error(f"❌ خطأ في البيانات: {error_data.get('detail', 'بيانات غير صحيحة')}")
                return None
            elif response.status_code == 403:
                st.error("❌ لا تملك صلاحية إضافة موظفين")
                return None
            else:
                st.error(f"❌ خطأ في إضافة الموظف: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 لا يمكن الاتصال بالخادم. تأكد من تشغيل السيرفر")
            return None
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
            return None
    
    def update_employee(self, employee_id, data):
        """تحديث بيانات موظف"""
        try:
            response = requests.put(
                f"{self.base_url}/{employee_id}",
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                st.error("الموظف غير موجود")
                return None
            elif response.status_code == 403:
                st.error("❌ لا تملك صلاحية تحديث بيانات الموظف")
                return None
            elif response.status_code == 400:
                error_data = response.json()
                st.error(f"❌ خطأ في البيانات: {error_data.get('detail', 'بيانات غير صحيحة')}")
                return None
            else:
                st.error(f"❌ خطأ في تحديث الموظف: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 لا يمكن الاتصال بالخادم. تأكد من تشغيل السيرفر")
            return None
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
            return None
    
    def delete_employee(self, employee_id):
        """حذف موظف (للمشرفين فقط)"""
        try:
            response = requests.delete(
                f"{self.base_url}/{employee_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                st.error("الموظف غير موجود")
                return False
            elif response.status_code == 403:
                st.error("❌ لا تملك صلاحية حذف الموظفين")
                return False
            else:
                st.error(f"❌ خطأ في حذف الموظف: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            st.error("🔌 لا يمكن الاتصال بالخادم. تأكد من تشغيل السيرفر")
            return False
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
            return False
    
    def get_employees_by_center(self, center_id):
        """جلب موظفي مركز محدد"""
        return self.get_employees(center_id=center_id)
    
    def get_available_employees(self):
        """جلب الموظفين المتاحين"""
        try:
            response = requests.get(
                f"{self.base_url}?available=true",
                headers=self.auth.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except:
            return []
    
    def update_employee_status(self, employee_id, is_on_duty=None, is_available=None):
        """تحديث حالة الموظف (على رأس العمل/متاح)"""
        data = {}
        if is_on_duty is not None:
            data["is_on_duty"] = is_on_duty
        if is_available is not None:
            data["is_available"] = is_available
        
        return self.update_employee(employee_id, data)
    
    def search_employees(self, query):
        """بحث متقدم في الموظفين"""
        return self.get_employees(search=query)