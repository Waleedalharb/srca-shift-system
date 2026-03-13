# frontend/services/employee_service.py
import requests
import streamlit as st
from config import config

class EmployeeService:
    def __init__(self, auth_service):
        self.base_url = f"{config.API_URL}/employees"
        self.auth = auth_service
    
    def _ensure_center_exists(self, center_num):
        """التأكد من وجود المركز، وإنشائه إذا لم يكن موجوداً"""
        try:
            # جلب قائمة المراكز
            centers_response = requests.get(
                f"{config.API_URL}/centers/",
                headers=self.auth.get_headers(),
                timeout=10
            )
            
            if centers_response.status_code == 200:
                centers = centers_response.json().get("items", [])
                
                # التحقق من وجود المركز بالرقم المطلوب
                center_exists = any(c.get("code") == str(center_num) for c in centers)
                
                # إذا المركز غير موجود، ننشئه
                if not center_exists:
                    # تحديد اسم المركز
                    center_names = {
                        "1": "المنصورة",
                        "2": "الخالدية",
                        "3": "منفوحة",
                        "4": "الدار البيضاء",
                        "5": "العزيزية",
                        "6": "الإسكان",
                        "7": "الحائر",
                        "8": "الشفاء",
                        "9": "عكاظ",
                        "10": "ديراب",
                        "12": "التمركز"
                    }
                    
                    center_name = center_names.get(str(center_num), f"مركز {center_num}")
                    
                    center_data = {
                        "name": center_name,
                        "code": str(center_num),
                        "city": "الرياض" if center_num != "12" else "متنقل",
                        "is_active": True
                    }
                    
                    create_response = requests.post(
                        f"{config.API_URL}/centers/",
                        headers=self.auth.get_headers(),
                        json=center_data,
                        timeout=10
                    )
                    
                    if create_response.status_code == 201:
                        print(f"✅ تم إنشاء مركز {center_name} تلقائياً")
                        return True
                    else:
                        print(f"❌ فشل إنشاء المركز: {create_response.text}")
                        return False
                return True
            return False
        except Exception as e:
            print(f"خطأ في التأكد من وجود المركز: {e}")
            return False
    
    def debug_import(self, df):
        """دالة تجريبية لفحص البيانات قبل الاستيراد"""
        print("\n" + "="*60)
        print("🔍 فحص بيانات الاستيراد")
        print(f"عدد الصفوف: {len(df)}")
        print(f"الأعمدة الموجودة: {list(df.columns)}")
        print("-"*60)
        
        for idx, row in df.iterrows():
            if idx >= 5:  # أول 5 صفوف فقط
                break
                
            emp_code = str(row.get('رمز', '')).strip() if 'رمز' in df.columns else 'غير موجود'
            job_title = str(row.get('طبيعة العمل', '')).strip() if 'طبيعة العمل' in df.columns else ''
            
            print(f"\nسطر {idx+1}:")
            print(f"  - الكود: {row.get('الكود', '')}")
            print(f"  - الاسم: {row.get('الاسم', '')}")
            print(f"  - الرمز: '{emp_code}'")
            print(f"  - نوع العمل: {job_title}")
            
            # تحقق من صحة الرمز
            if emp_code and emp_code != 'nan' and emp_code != 'غير موجود':
                if len(emp_code) > 1 and emp_code[1:].isdigit():
                    print(f"  ✅ رمز صحيح: {emp_code} -> مركز {emp_code[1:]}")
                else:
                    print(f"  ⚠️ رمز غير متوقع: {emp_code}")
            else:
                print(f"  ❌ لا يوجد رمز")
        
        print("\n" + "="*60)
        return True
    
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
            return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
    
    def get_employees(self, center_id=None, search=None, employee_type=None, skip=0, limit=100):
        """قائمة الموظفين"""
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
            return {"total": 0, "items": []}
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
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
            return None
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
            return None
    
    def create_employee(self, data):
        """إضافة موظف جديد - مع إنشاء تلقائي للمركز"""
        try:
            # استخراج رقم المركز من الكود (A1 -> 1, B10 -> 10)
            emp_code = data.get('emp_code', '')
            
            if emp_code and len(emp_code) > 1 and emp_code[1:].isdigit():
                center_num = emp_code[1:]
                # التأكد من وجود المركز قبل إضافة الموظف
                self._ensure_center_exists(center_num)
            
            # طباعة البيانات للتأكد
            print(f"\n📤 إرسال بيانات موظف:")
            print(f"   - الرمز: {emp_code}")
            print(f"   - البيانات: {data}")
            
            response = requests.post(
                self.base_url,
                headers=self.auth.get_headers(),
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                print(f"   ✅ تم الإضافة بنجاح")
                return response.json()
            else:
                print(f"   ❌ خطأ {response.status_code}: {response.text}")
                st.error(f"❌ خطأ في إضافة الموظف: {response.status_code}")
                try:
                    error_detail = response.json()
                    st.error(f"التفاصيل: {error_detail}")
                except:
                    st.error(f"الرد: {response.text}")
                return None
        except Exception as e:
            st.error(f"❌ خطأ في الاتصال: {str(e)}")
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
            st.error(f"❌ خطأ في التحديث: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
            return None
    
    def delete_employee(self, employee_id):
        """حذف موظف"""
        try:
            response = requests.delete(
                f"{self.base_url}/{employee_id}",
                headers=self.auth.get_headers(),
                timeout=10
            )
            return response.status_code == 204
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
            return False
    
    def import_employees_from_excel(self, df, default_center_id=None):
        """استيراد موظفين من Excel مع إنشاء تلقائي للمراكز"""
        success = 0
        failed = 0
        errors = []
        
        # تشغيل فحص البيانات أولاً
        self.debug_import(df)
        
        for idx, row in df.iterrows():
            try:
                emp_no = str(row['الكود']).strip()
                full_name = str(row['الاسم']).strip()
                emp_code = str(row.get('رمز', '')).strip() if 'رمز' in row else ''
                
                # تنظيف emp_code من الأرقام العائمة
                if emp_code and emp_code != 'nan':
                    # إذا كان الرمز رقم عائم (مثل 0.0)
                    if '.' in emp_code:
                        emp_code = emp_code.split('.')[0]
                else:
                    emp_code = ''
                
                # استخراج رقم المركز من الكود
                if emp_code and len(emp_code) > 1 and emp_code[1:].isdigit():
                    center_num = emp_code[1:]
                    self._ensure_center_exists(center_num)
                
                # تحديد نوع الموظف من طبيعة العمل
                job_title = str(row.get('طبيعة العمل', '')).strip()
                emp_type = 'paramedic'  # افتراضي
                
                # تحويل المسميات الوظيفية
                type_mapping = {
                    'كبير مسعفين': 'chief_paramedic',
                    'مساعد كبير مسعفين': 'assistant_chief',
                    'قيادة ميدانية': 'field_leader',
                    'تحكم عملياتي': 'operations_control',
                    'تنسيق استجابة': 'response_coordinator',
                    'أخصائي اسعاف': 'paramedic',
                    'فني اسعاف': 'emt',
                    'مساعد صحي': 'health_assistant',
                    'دعم لوجستي': 'logistic_support',
                    'إداري': 'admin'
                }
                emp_type = type_mapping.get(job_title, 'paramedic')
                
                employee_data = {
                    'emp_no': emp_no,
                    'full_name': full_name,
                    'employee_type': emp_type,
                    'center_id': default_center_id,
                    'is_active': True
                }
                
                if emp_code:
                    employee_data['emp_code'] = emp_code
                
                if self.create_employee(employee_data):
                    success += 1
                else:
                    failed += 1
                    errors.append(f"سطر {idx+2}: فشل إضافة {full_name}")
                    
            except Exception as e:
                failed += 1
                errors.append(f"سطر {idx+2}: {str(e)}")
        
        return success, failed, errors