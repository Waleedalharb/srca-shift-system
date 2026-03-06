# backend/app/services/prediction_service.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Tuple, Optional
import joblib
import os
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import json

class PredictionService:
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.scaler = None
        self.features = None
        self.model_path = "models/prediction_model.pkl"
        self.scaler_path = "models/scaler.pkl"
        self.features_path = "models/features.json"
        self.training_data_path = "models/training_data.csv"
        
        # إنشاء مجلد models إذا لم يكن موجودًا
        os.makedirs('models', exist_ok=True)
        
        # محاولة تحميل النموذج إذا كان موجودًا
        self.load_model()
    
    def load_model(self):
        """تحميل النموذج المدرب"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
            if os.path.exists(self.scaler_path):
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            if os.path.exists(self.features_path):
                with open(self.features_path, 'r') as f:
                    self.features = json.load(f)
            print("✅ تم تحميل النموذج")
        except Exception as e:
            print(f"⚠️ لا يمكن تحميل النموذج: {e}")
    
    def save_model(self):
        """حفظ النموذج المدرب"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            with open(self.features_path, 'w') as f:
                json.dump(self.features, f)
            print("✅ تم حفظ النموذج")
        except Exception as e:
            print(f"⚠️ خطأ في حفظ النموذج: {e}")
    
    def prepare_features(self, date: datetime, calls_data: Optional[Dict] = None) -> Dict:
        """تحضير ميزات التاريخ"""
        
        # ميزات زمنية
        features = {
            'month': date.month,
            'day_of_week': date.weekday(),
            'day_of_month': date.day,
            'is_weekend': 1 if date.weekday() >= 4 else 0,
            'is_ramadan': 1 if date.month == 9 else 0,  # تقديري
            'is_summer': 1 if date.month in [6, 7, 8] else 0,
            'is_winter': 1 if date.month in [12, 1, 2] else 0,
            'week_of_year': date.isocalendar()[1],
            'quarter': (date.month - 1) // 3 + 1,
            'days_to_ramadan': self._days_to_ramadan(date),
        }
        
        # إضافة بيانات إضافية إذا وجدت
        if calls_data:
            features.update({
                'previous_day_calls': calls_data.get('previous_day', 0),
                'previous_week_avg': calls_data.get('week_avg', 0),
                'previous_month_avg': calls_data.get('month_avg', 0),
                'staff_available': calls_data.get('staff', 30),
                'coverage_percentage': calls_data.get('coverage', 80),
            })
        
        return features
    
    def _days_to_ramadan(self, date: datetime) -> int:
        """حساب الأيام المتبقية لرمضان (تقديري)"""
        # رمضان 2026 يبدأ تقريبًا 18 فبراير
        ramadan_start = datetime(date.year, 2, 18)
        if date > ramadan_start:
            ramadan_start = datetime(date.year + 1, 2, 18)
        return (ramadan_start - date).days
    
    def add_training_data(self, data: List[Dict]) -> bool:
        """إضافة بيانات تدريب جديدة"""
        try:
            df_new = pd.DataFrame(data)
            
            # تحميل البيانات الموجودة
            if os.path.exists(self.training_data_path):
                df_existing = pd.read_csv(self.training_data_path)
                df = pd.concat([df_existing, df_new], ignore_index=True)
                df = df.drop_duplicates(subset=['date'], keep='last')
            else:
                df = df_new
            
            # حفظ البيانات
            df.to_csv(self.training_data_path, index=False)
            print(f"✅ تم إضافة {len(df_new)} سجل تدريب جديد")
            return True
        except Exception as e:
            print(f"❌ خطأ في إضافة البيانات: {e}")
            return False
    
    def train_model(self, force_retrain: bool = False) -> Dict:
        """تدريب النموذج على البيانات المتاحة"""
        
        # التحقق من وجود بيانات تدريب
        if not os.path.exists(self.training_data_path):
            return {"success": False, "message": "لا توجد بيانات تدريب", "accuracy": 0}
        
        # تحميل البيانات
        df = pd.read_csv(self.training_data_path)
        
        if len(df) < 30:
            return {"success": False, "message": f"البيانات غير كافية (لديك {len(df)} سجل، نحتاج 30 على الأقل)", "accuracy": 0}
        
        try:
            # تحويل التاريخ
            df['date'] = pd.to_datetime(df['date'])
            
            # تحضير الميزات
            feature_dfs = []
            for _, row in df.iterrows():
                features = self.prepare_features(
                    row['date'],
                    {
                        'previous_day': row.get('previous_day_calls', 0),
                        'week_avg': row.get('previous_week_avg', 0),
                        'month_avg': row.get('previous_month_avg', 0),
                        'staff': row.get('staff_available', 30),
                        'coverage': row.get('coverage_percentage', 80),
                    }
                )
                feature_dfs.append(features)
            
            X = pd.DataFrame(feature_dfs)
            y = df['calls_count']
            
            # حفظ أسماء الميزات
            self.features = list(X.columns)
            
            # تقسيم البيانات
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # تطبيع البيانات
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # تدريب النموذج
            self.model = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
            
            # تقييم النموذج
            y_pred = self.model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            accuracy = max(0, min(100, (1 - mae / y_test.mean()) * 100))
            
            # حفظ النموذج
            self.save_model()
            
            return {
                "success": True,
                "message": "✅ تم تدريب النموذج بنجاح",
                "accuracy": round(accuracy, 2),
                "mae": round(mae, 2),
                "r2": round(r2, 3),
                "samples": len(df),
                "features_used": self.features
            }
            
        except Exception as e:
            return {"success": False, "message": f"❌ خطأ في التدريب: {str(e)}", "accuracy": 0}
    
    def predict(self, date: datetime, staff: int = 30, coverage: float = 80) -> Dict:
        """التنبؤ لليوم المحدد"""
        
        if not self.model or not self.scaler:
            return {
                'success': False,
                'message': 'النموذج غير مدرب بعد',
                'predicted_calls': 0,
                'confidence': 0,
                'peak_hours': []
            }
        
        try:
            # تحضير الميزات
            features_dict = self.prepare_features(date, {
                'staff': staff,
                'coverage': coverage
            })
            
            features_df = pd.DataFrame([features_dict])[self.features]
            features_scaled = self.scaler.transform(features_df)
            
            # تنبؤ
            predicted = self.model.predict(features_scaled)[0]
            
            # حساب الثقة (كلما زادت بيانات التدريب، زادت الثقة)
            if os.path.exists(self.training_data_path):
                df = pd.read_csv(self.training_data_path)
                confidence = min(95, 70 + len(df) // 10)
            else:
                confidence = 50
            
            # توقع ساعات الذروة
            peak_hours = self._predict_peak_hours(date, predicted)
            
            # توصيات
            recommendation = self._generate_recommendation(predicted, staff, coverage)
            
            return {
                'success': True,
                'date': date.strftime('%Y-%m-%d'),
                'predicted_calls': int(predicted),
                'confidence': confidence,
                'peak_hours': peak_hours,
                'recommendation': recommendation,
                'staff_available': staff,
                'coverage': coverage
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في التنبؤ: {str(e)}',
                'predicted_calls': 0,
                'confidence': 0,
                'peak_hours': []
            }
    
    def _predict_peak_hours(self, date: datetime, predicted_calls: int) -> List[Dict]:
        """توقع ساعات الذروة مع أوقات محددة"""
        
        if date.weekday() >= 4:  # نهاية الأسبوع
            return [
                {"period": "10:00 - 12:00", "intensity": "عالية", "percentage": 25},
                {"period": "16:00 - 18:00", "intensity": "متوسطة", "percentage": 20},
                {"period": "20:00 - 22:00", "intensity": "عالية", "percentage": 30},
            ]
        else:
            return [
                {"period": "08:00 - 10:00", "intensity": "عالية", "percentage": 35},
                {"period": "12:00 - 14:00", "intensity": "متوسطة", "percentage": 25},
                {"period": "16:00 - 18:00", "intensity": "متوسطة", "percentage": 20},
            ]
    
    def _generate_recommendation(self, predicted_calls: int, staff: int, coverage: float) -> str:
        """توليد توصيات بناءً على التنبؤ"""
        
        ratio = predicted_calls / staff
        
        if ratio > 3:
            return "🔴 **ازدحام شديد متوقع** - يفضل زيادة المناوبات 50% وتجهيز فرق احتياط"
        elif ratio > 2:
            return "🟡 **ازدحام مرتفع** - يفضل زيادة المناوبات 30%"
        elif ratio > 1.5:
            return "🟠 **ازدحام متوسط** - تجهيز فرق احتياط"
        elif ratio < 0.5:
            return "🟢 **هدوء متوقع** - يمكن منح إجازات"
        else:
            return "🔵 **وضع طبيعي** - استمرار العمل كالمعتاد"
    
    def get_training_stats(self) -> Dict:
        """إحصائيات بيانات التدريب"""
        if not os.path.exists(self.training_data_path):
            return {"total_records": 0, "date_range": "لا توجد بيانات", "avg_calls": 0}
        
        df = pd.read_csv(self.training_data_path)
        df['date'] = pd.to_datetime(df['date'])
        
        return {
            "total_records": len(df),
            "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} إلى {df['date'].max().strftime('%Y-%m-%d')}",
            "avg_calls": round(df['calls_count'].mean(), 1),
            "max_calls": int(df['calls_count'].max()),
            "min_calls": int(df['calls_count'].min()),
            "features": self.features if self.features else [],
            "model_loaded": self.model is not None
        }