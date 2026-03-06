# backend/app/services/prediction_service.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Tuple
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle

class PredictionService:
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.scaler = None
        self.model_path = "models/prediction_model.pkl"
        
    def prepare_historical_data(self, days_back: int = 365) -> pd.DataFrame:
        """تجهيز البيانات التاريخية للتدريب"""
        
        # جلب بيانات البلاغات (إذا كانت موجودة)
        # هنا نستخدم بيانات وهمية مؤقتاً
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # توليد بيانات تجريبية
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data = []
        for date in dates:
            # عوامل مؤثرة
            month = date.month
            day_of_week = date.weekday()
            is_weekend = 1 if day_of_week >= 4 else 0
            is_ramadan = 1 if month == 9 else 0  # رمضان
            is_summer = 1 if month in [6, 7, 8] else 0
            
            # عدد الموظفين المتاحين (بيانات وهمية)
            available_staff = np.random.randint(20, 35)
            
            # عدد البلاغات (بيانات وهمية مع أنماط)
            base_calls = 40
            if is_weekend:
                base_calls += 10
            if is_ramadan:
                base_calls += 25
            if is_summer:
                base_calls += 15
            if day_of_week == 3:  # الخميس
                base_calls += 8
            
            # إضافة بعض العشوائية
            calls = int(base_calls + np.random.randint(-5, 10))
            
            data.append({
                'date': date,
                'month': month,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'is_ramadan': is_ramadan,
                'is_summer': is_summer,
                'available_staff': available_staff,
                'calls_count': calls
            })
        
        return pd.DataFrame(data)
    
    def train_model(self, force_retrain: bool = False):
        """تدريب نموذج التنبؤ"""
        
        # التحقق من وجود نموذج مدرب
        if os.path.exists(self.model_path) and not force_retrain:
            self.load_model()
            return
        
        # تجهيز البيانات
        df = self.prepare_historical_data()
        
        # تجهيز features
        features = ['month', 'day_of_week', 'is_weekend', 'is_ramadan', 'is_summer', 'available_staff']
        X = df[features]
        y = df['calls_count']
        
        # تطبيع البيانات
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # تدريب النموذج
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        
        # حفظ النموذج
        os.makedirs('models', exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'features': features
            }, f)
        
        print(f"✅ تم تدريب النموذج بدقة: {self.model.score(X_scaled, y):.2f}")
    
    def load_model(self):
        """تحميل النموذج المدرب"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                print("✅ تم تحميل النموذج")
    
    def predict_day(self, date: datetime, available_staff: int) -> Dict:
        """التنبؤ بعدد البلاغات ليوم محدد"""
        
        if not self.model:
            self.load_model()
        
        if not self.model:
            return {
                'date': date.strftime('%Y-%m-%d'),
                'predicted_calls': 0,
                'confidence': 0,
                'peak_hours': [],
                'recommendation': 'النموذج غير مدرب'
            }
        
        # تجهيز features
        features = pd.DataFrame([{
            'month': date.month,
            'day_of_week': date.weekday(),
            'is_weekend': 1 if date.weekday() >= 4 else 0,
            'is_ramadan': 1 if date.month == 9 else 0,
            'is_summer': 1 if date.month in [6, 7, 8] else 0,
            'available_staff': available_staff
        }])
        
        # تطبيع
        features_scaled = self.scaler.transform(features)
        
        # تنبؤ
        predicted = self.model.predict(features_scaled)[0]
        
        # حساب الثقة
        confidence = min(95, 70 + len(self.model.estimators_) // 10)
        
        # توقع ساعات الذروة
        peak_hours = self._predict_peak_hours(date, predicted)
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'predicted_calls': int(predicted),
            'confidence': confidence,
            'peak_hours': peak_hours,
            'recommendation': self._generate_recommendation(predicted, available_staff)
        }
    
    def predict_month(self, year: int, month: int, staff_count: int = 30) -> List[Dict]:
        """التنبؤ لشهر كامل"""
        
        predictions = []
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day)
            pred = self.predict_day(date, staff_count)
            predictions.append(pred)
        
        return predictions
    
    def _predict_peak_hours(self, date: datetime, predicted_calls: int) -> List[str]:
        """توقع ساعات الذروة"""
        
        # نمط ساعات الذروة حسب نوع اليوم
        if date.weekday() >= 4:  # نهاية الأسبوع
            return ["10:00-12:00", "16:00-18:00", "20:00-22:00"]
        else:
            return ["08:00-10:00", "12:00-14:00", "16:00-18:00"]
    
    def _generate_recommendation(self, predicted_calls: int, available_staff: int) -> str:
        """توليد توصيات بناءً على التنبؤ"""
        
        if predicted_calls > 60:
            return "🔴 ازدحام متوقع - يفضل زيادة المناوبات 30%"
        elif predicted_calls > 45:
            return "🟡 ازدحام متوسط - تجهيز فرق احتياط"
        elif predicted_calls < 25:
            return "🟢 هدوء متوقع - يمكن منح إجازات"
        else:
            return "🔵 وضع طبيعي"