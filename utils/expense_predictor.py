"""
지출 예측 모듈
과거 데이터 기반 다음 달 지출 예측
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta


class ExpensePredictor:
    """지출 예측 클래스"""
    
    def __init__(self):
        """초기화"""
        self.model = None
        self.last_trained = None
    
    def predict_next_month(self, df):
        """
        다음 달 총 지출 예측
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            dict: 예측 결과
        """
        expense_df = df[df['구분'] == '지출']
        
        # 월별 집계
        monthly = expense_df.groupby('년월')['금액_절대값'].sum()
        
        if len(monthly) < 3:
            return {
                'success': False,
                'message': '예측을 위해 최소 3개월의 데이터가 필요합니다',
                'prediction': 0,
                'confidence': 0
            }
        
        # 선형 회귀 모델
        X = np.arange(len(monthly)).reshape(-1, 1)
        y = monthly.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 다음 달 예측
        next_month_pred = model.predict([[len(monthly)]])[0]
        
        # 계절성 고려 (같은 월의 평균)
        current_month_num = pd.Timestamp.now().month
        next_month_num = (current_month_num % 12) + 1
        
        seasonal_avg = self._get_seasonal_average(df, next_month_num)
        
        # 가중 평균 (추세 70% + 계절성 30%)
        if seasonal_avg > 0:
            final_prediction = next_month_pred * 0.7 + seasonal_avg * 0.3
        else:
            final_prediction = next_month_pred
        
        # 신뢰도 계산 (R² 스코어)
        confidence = model.score(X, y) * 100
        
        # 최근 추세 분석
        recent_trend = self._analyze_trend(monthly)
        
        return {
            'success': True,
            'prediction': max(0, final_prediction),
            'trend_prediction': max(0, next_month_pred),
            'seasonal_prediction': seasonal_avg,
            'confidence': confidence,
            'trend': recent_trend,
            'data_points': len(monthly)
        }
    
    def predict_by_category(self, df):
        """
        카테고리별 다음 달 예측
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 카테고리별 예측
        """
        expense_df = df[df['구분'] == '지출']
        categories = expense_df['분류'].unique()
        
        predictions = []
        
        for category in categories:
            cat_df = expense_df[expense_df['분류'] == category]
            monthly = cat_df.groupby('년월')['금액_절대값'].sum()
            
            if len(monthly) < 2:
                continue
            
            # 간단한 이동 평균 예측
            if len(monthly) >= 3:
                prediction = monthly.tail(3).mean()
            else:
                prediction = monthly.mean()
            
            last_month = monthly.iloc[-1]
            change = ((prediction - last_month) / last_month * 100) if last_month > 0 else 0
            
            predictions.append({
                '카테고리': category,
                '최근 평균': monthly.tail(3).mean() if len(monthly) >= 3 else monthly.mean(),
                '예측 금액': prediction,
                '전월 대비': change
            })
        
        if not predictions:
            return pd.DataFrame()
        
        pred_df = pd.DataFrame(predictions)
        return pred_df.sort_values('예측 금액', ascending=False)
    
    def _get_seasonal_average(self, df, month_num):
        """특정 월의 과거 평균"""
        expense_df = df[df['구분'] == '지출'].copy()
        expense_df['월'] = expense_df['날짜'].dt.month
        
        same_month = expense_df[expense_df['월'] == month_num]
        
        if len(same_month) == 0:
            return 0
        
        return same_month.groupby(same_month['날짜'].dt.to_period('M'))['금액_절대값'].sum().mean()
    
    def _analyze_trend(self, series):
        """추세 분석"""
        if len(series) < 2:
            return 'stable'
        
        # 최근 3개월 평균 vs 이전 평균
        if len(series) >= 6:
            recent = series.tail(3).mean()
            previous = series.iloc[-6:-3].mean()
        else:
            recent = series.tail(2).mean()
            previous = series.iloc[:-2].mean() if len(series) > 2 else series.mean()
        
        change = ((recent - previous) / previous * 100) if previous > 0 else 0
        
        if change > 10:
            return 'increasing'
        elif change < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_prediction_accuracy(self, df):
        """
        예측 정확도 평가 (과거 데이터로 테스트)
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            dict: 정확도 정보
        """
        expense_df = df[df['구분'] == '지출']
        monthly = expense_df.groupby('년월')['금액_절대값'].sum()
        
        if len(monthly) < 4:
            return {'success': False, 'message': '평가를 위해 최소 4개월의 데이터가 필요합니다'}
        
        # 마지막 달을 제외하고 학습
        X_train = np.arange(len(monthly) - 1).reshape(-1, 1)
        y_train = monthly.values[:-1]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # 마지막 달 예측
        prediction = model.predict([[len(monthly) - 1]])[0]
        actual = monthly.values[-1]
        
        # 오차율
        error_rate = abs(prediction - actual) / actual * 100 if actual > 0 else 0
        
        return {
            'success': True,
            'predicted': prediction,
            'actual': actual,
            'error': prediction - actual,
            'error_rate': error_rate,
            'accuracy': max(0, 100 - error_rate)
        }
    
    def detect_spending_patterns(self, df):
        """
        소비 패턴 감지
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            dict: 패턴 분석 결과
        """
        expense_df = df[df['구분'] == '지출']
        
        patterns = {
            'monthly_variance': self._calculate_variance(expense_df),
            'peak_spending_day': self._get_peak_spending_day(expense_df),
            'spending_consistency': self._calculate_consistency(expense_df),
            'category_concentration': self._calculate_concentration(expense_df)
        }
        
        return patterns
    
    def _calculate_variance(self, expense_df):
        """월별 지출 변동성"""
        monthly = expense_df.groupby('년월')['금액_절대값'].sum()
        
        if len(monthly) < 2:
            return {'cv': 0, 'interpretation': 'insufficient_data'}
        
        cv = (monthly.std() / monthly.mean() * 100) if monthly.mean() > 0 else 0
        
        if cv < 20:
            interpretation = 'stable'
        elif cv < 40:
            interpretation = 'moderate'
        else:
            interpretation = 'volatile'
        
        return {'cv': cv, 'interpretation': interpretation}
    
    def _get_peak_spending_day(self, expense_df):
        """가장 지출이 많은 요일"""
        if len(expense_df) == 0:
            return None
        
        expense_df_copy = expense_df.copy()
        expense_df_copy['요일'] = expense_df_copy['날짜'].dt.day_name()
        
        weekday_spending = expense_df_copy.groupby('요일')['금액_절대값'].sum()
        
        if len(weekday_spending) == 0:
            return None
        
        peak_day = weekday_spending.idxmax()
        
        weekday_map = {
            'Monday': '월', 'Tuesday': '화', 'Wednesday': '수',
            'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'
        }
        
        return weekday_map.get(peak_day, peak_day)
    
    def _calculate_consistency(self, expense_df):
        """소비 일관성 점수 (0-100)"""
        daily_spending = expense_df.groupby('날짜')['금액_절대값'].sum()
        
        if len(daily_spending) < 7:
            return 0
        
        # 일별 지출의 변동계수가 낮을수록 일관적
        cv = (daily_spending.std() / daily_spending.mean() * 100) if daily_spending.mean() > 0 else 100
        
        consistency_score = max(0, 100 - cv)
        
        return round(consistency_score, 1)
    
    def _calculate_concentration(self, expense_df):
        """지출 집중도 (상위 3개 카테고리 비중)"""
        category_sum = expense_df.groupby('분류')['금액_절대값'].sum()
        
        if len(category_sum) == 0:
            return 0
        
        top3_sum = category_sum.nlargest(3).sum()
        total = category_sum.sum()
        
        concentration = (top3_sum / total * 100) if total > 0 else 0
        
        return round(concentration, 1)
    
    def suggest_budget_adjustments(self, df, current_budgets):
        """
        예측 기반 예산 조정 제안
        
        Args:
            df: 거래내역 DataFrame
            current_budgets: 현재 예산 딕셔너리
            
        Returns:
            list: 조정 제안
        """
        predictions = self.predict_by_category(df)
        
        if predictions.empty:
            return []
        
        suggestions = []
        
        for _, row in predictions.iterrows():
            category = row['카테고리']
            predicted = row['예측 금액']
            
            if category in current_budgets:
                current = current_budgets[category]
                
                if predicted > current * 1.2:  # 20% 이상 초과 예상
                    suggestions.append({
                        '카테고리': category,
                        '현재 예산': current,
                        '예상 지출': predicted,
                        '조정 제안': round(predicted * 1.1, -3),  # 10% 여유
                        '사유': f'최근 추세 상승 ({row["전월 대비"]:+.1f}%)'
                    })
                elif predicted < current * 0.7:  # 30% 미만 사용 예상
                    suggestions.append({
                        '카테고리': category,
                        '현재 예산': current,
                        '예상 지출': predicted,
                        '조정 제안': round(predicted * 1.2, -3),  # 20% 여유
                        '사유': '예산 여유 있음'
                    })
        
        return suggestions