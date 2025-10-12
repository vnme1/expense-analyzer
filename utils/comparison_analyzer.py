"""
비교 분석 모듈
월별, 카테고리별, 요일별 비교 분석
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class ComparisonAnalyzer:
    """비교 분석 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def compare_months(self, df, month1, month2):
        """
        두 달 비교 분석
        
        Args:
            df: 거래내역 DataFrame
            month1: 비교할 월 1 (예: "2025-01")
            month2: 비교할 월 2 (예: "2025-02")
            
        Returns:
            dict: 비교 결과
        """
        df1 = df[df['년월'] == month1]
        df2 = df[df['년월'] == month2]
        
        # 기본 지표
        income1 = df1[df1['구분'] == '수입']['금액_절대값'].sum()
        income2 = df2[df2['구분'] == '수입']['금액_절대값'].sum()
        
        expense1 = df1[df1['구분'] == '지출']['금액_절대값'].sum()
        expense2 = df2[df2['구분'] == '지출']['금액_절대값'].sum()
        
        # 카테고리별 비교
        cat1 = df1[df1['구분'] == '지출'].groupby('분류')['금액_절대값'].sum()
        cat2 = df2[df2['구분'] == '지출'].groupby('분류')['금액_절대값'].sum()
        
        # 카테고리 증감
        all_categories = set(cat1.index) | set(cat2.index)
        category_changes = []
        
        for cat in all_categories:
            val1 = cat1.get(cat, 0)
            val2 = cat2.get(cat, 0)
            change = val2 - val1
            change_pct = (change / val1 * 100) if val1 > 0 else 0
            
            category_changes.append({
                '카테고리': cat,
                f'{month1}': val1,
                f'{month2}': val2,
                '증감액': change,
                '증감률(%)': change_pct
            })
        
        # ✅ DataFrame 생성 후 비어있는지 확인
        category_changes_df = pd.DataFrame(category_changes)
        
        # ✅ 빈 DataFrame이 아닐 때만 정렬
        if not category_changes_df.empty and '증감액' in category_changes_df.columns:
            category_changes_df = category_changes_df.sort_values('증감액', ascending=False)
        
        return {
            'summary': {
                'month1': month1,
                'month2': month2,
                'income1': income1,
                'income2': income2,
                'income_change': income2 - income1,
                'income_change_pct': ((income2 - income1) / income1 * 100) if income1 > 0 else 0,
                'expense1': expense1,
                'expense2': expense2,
                'expense_change': expense2 - expense1,
                'expense_change_pct': ((expense2 - expense1) / expense1 * 100) if expense1 > 0 else 0,
                'transaction_count1': len(df1),
                'transaction_count2': len(df2)
            },
            'category_comparison': category_changes_df
        }
    
    def compare_this_month_vs_last_month(self, df):
        """이번 달 vs 지난 달 비교"""
        current_month = pd.Timestamp.now().strftime('%Y-%m')
        last_month = (pd.Timestamp.now() - pd.DateOffset(months=1)).strftime('%Y-%m')
        
        return self.compare_months(df, last_month, current_month)
    
    def get_weekday_pattern(self, df):
        """
        요일별 소비 패턴 분석
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 요일별 통계
        """
        expense_df = df[df['구분'] == '지출'].copy()
        
        expense_df['요일'] = expense_df['날짜'].dt.day_name()
        expense_df['요일_한글'] = expense_df['요일'].map({
            'Monday': '월', 'Tuesday': '화', 'Wednesday': '수',
            'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'
        })
        
        # 요일별 집계
        weekday_stats = expense_df.groupby('요일_한글').agg({
            '금액_절대값': ['sum', 'mean', 'count']
        }).round(0)
        
        weekday_stats.columns = ['총지출', '평균지출', '거래건수']
        
        # 요일 순서 정렬
        weekday_order = ['월', '화', '수', '목', '금', '토', '일']
        weekday_stats = weekday_stats.reindex(weekday_order)
        
        return weekday_stats
    
    def get_category_trend(self, df, category, period='monthly'):
        """
        특정 카테고리의 추이
        
        Args:
            df: 거래내역 DataFrame
            category: 카테고리명
            period: 'monthly' 또는 'weekly'
            
        Returns:
            pd.DataFrame: 기간별 추이
        """
        category_df = df[df['분류'] == category].copy()
        
        if period == 'monthly':
            trend = category_df.groupby('년월').agg({
                '금액_절대값': ['sum', 'mean', 'count']
            })
        else:  # weekly
            category_df['주'] = category_df['날짜'].dt.to_period('W')
            trend = category_df.groupby('주').agg({
                '금액_절대값': ['sum', 'mean', 'count']
            })
        
        trend.columns = ['총액', '평균', '건수']
        return trend
    
    def get_top_changes(self, df, top_n=5):
        """
        이번 달 vs 지난 달 최대 증가/감소 카테고리
        
        Args:
            df: 거래내역 DataFrame
            top_n: 상위 N개
            
        Returns:
            dict: 증가/감소 카테고리
        """
        comparison = self.compare_this_month_vs_last_month(df)
        category_df = comparison['category_comparison']
        
        if category_df.empty:
            return {'increased': [], 'decreased': []}
        
        # 증가
        increased = category_df.nlargest(top_n, '증감액')[['카테고리', '증감액', '증감률(%)']].to_dict('records')
        
        # 감소
        decreased = category_df.nsmallest(top_n, '증감액')[['카테고리', '증감액', '증감률(%)']].to_dict('records')
        
        return {
            'increased': increased,
            'decreased': decreased
        }
    
    def get_time_of_day_pattern(self, df):
        """
        시간대별 소비 패턴 (시간 데이터가 있는 경우)
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 시간대별 통계
        """
        # 시간 컬럼이 있는지 확인
        if '시간' not in df.columns:
            return None
        
        expense_df = df[df['구분'] == '지출'].copy()
        
        # 시간대 분류
        def get_time_period(hour):
            if 6 <= hour < 12:
                return '오전 (06-12)'
            elif 12 <= hour < 18:
                return '오후 (12-18)'
            elif 18 <= hour < 24:
                return '저녁 (18-24)'
            else:
                return '새벽 (00-06)'
        
        expense_df['시간대'] = expense_df['시간'].apply(lambda x: get_time_period(x.hour))
        
        time_stats = expense_df.groupby('시간대').agg({
            '금액_절대값': ['sum', 'mean', 'count']
        }).round(0)
        
        time_stats.columns = ['총지출', '평균지출', '거래건수']
        
        return time_stats
    
    def get_spending_velocity(self, df):
        """
        소비 속도 분석 (월초/중/말)
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            dict: 시기별 소비 분석
        """
        expense_df = df[df['구분'] == '지출'].copy()
        
        # 일자 기준 분류
        def get_period(day):
            if day <= 10:
                return '월초 (1-10일)'
            elif day <= 20:
                return '월중 (11-20일)'
            else:
                return '월말 (21일~)'
        
        expense_df['월시기'] = expense_df['날짜'].dt.day.apply(get_period)
        
        period_stats = expense_df.groupby('월시기').agg({
            '금액_절대값': ['sum', 'mean', 'count']
        }).round(0)
        
        period_stats.columns = ['총지출', '평균지출', '거래건수']
        
        # 순서 정렬
        period_order = ['월초 (1-10일)', '월중 (11-20일)', '월말 (21일~)']
        period_stats = period_stats.reindex(period_order)
        
        return period_stats
    
    def get_year_over_year(self, df):
        """
        작년 동월 대비 분석
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 작년 대비 비교
        """
        current_year = pd.Timestamp.now().year
        last_year = current_year - 1
        
        # 현재 연도와 작년 데이터 필터링
        current_year_df = df[df['날짜'].dt.year == current_year]
        last_year_df = df[df['날짜'].dt.year == last_year]
        
        if len(last_year_df) == 0:
            return None
        
        # 월별 비교
        current_monthly = current_year_df.groupby(current_year_df['날짜'].dt.month).agg({
            '금액_절대값': 'sum'
        })
        
        last_monthly = last_year_df.groupby(last_year_df['날짜'].dt.month).agg({
            '금액_절대값': 'sum'
        })
        
        comparison = pd.DataFrame({
            f'{last_year}년': last_monthly['금액_절대값'],
            f'{current_year}년': current_monthly['금액_절대값']
        })
        
        comparison['증감액'] = comparison[f'{current_year}년'] - comparison[f'{last_year}년']
        comparison['증감률(%)'] = (comparison['증감액'] / comparison[f'{last_year}년'] * 100).round(1)
        
        comparison.index = comparison.index.map(lambda x: f'{x}월')
        
        return comparison
    
    def get_category_mix_change(self, df):
        """
        카테고리 구성 변화 (최근 3개월)
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 카테고리별 비중 변화
        """
        # 최근 3개월 데이터
        months = sorted(df['년월'].unique())[-3:]
        
        if len(months) < 2:
            return None
        
        mix_data = []
        
        for month in months:
            month_df = df[df['년월'] == month]
            expense_df = month_df[month_df['구분'] == '지출']
            
            total = expense_df['금액_절대값'].sum()
            
            category_sum = expense_df.groupby('분류')['금액_절대값'].sum()
            
            for cat, amount in category_sum.items():
                mix_data.append({
                    '월': month,
                    '카테고리': cat,
                    '금액': amount,
                    '비중(%)': (amount / total * 100) if total > 0 else 0
                })
        
        mix_df = pd.DataFrame(mix_data)
        
        # Pivot 형식으로 변환
        pivot = mix_df.pivot(index='카테고리', columns='월', values='비중(%)')
        pivot = pivot.fillna(0).round(1)
        
        return pivot
    
    def get_anomalies(self, df, threshold=2.0):
        """
        이상 거래 탐지 (통계적 방법)
        
        Args:
            df: 거래내역 DataFrame
            threshold: 표준편차 배수 (기본 2.0)
            
        Returns:
            pd.DataFrame: 이상 거래 목록
        """
        expense_df = df[df['구분'] == '지출'].copy()
        
        # 카테고리별 평균과 표준편차
        anomalies = []
        
        for category in expense_df['분류'].unique():
            cat_df = expense_df[expense_df['분류'] == category]
            
            if len(cat_df) < 3:  # 데이터가 너무 적으면 스킵
                continue
            
            mean = cat_df['금액_절대값'].mean()
            std = cat_df['금액_절대값'].std()
            
            # 평균 ± threshold * 표준편차 범위 밖
            lower = mean - threshold * std
            upper = mean + threshold * std
            
            outliers = cat_df[
                (cat_df['금액_절대값'] < lower) | 
                (cat_df['금액_절대값'] > upper)
            ]
            
            for _, row in outliers.iterrows():
                z_score = (row['금액_절대값'] - mean) / std if std > 0 else 0
                
                anomalies.append({
                    '날짜': row['날짜'],
                    '적요': row['적요'],
                    '금액': row['금액_절대값'],
                    '카테고리': category,
                    '카테고리평균': mean,
                    'Z-Score': abs(z_score),
                    '이상도': '높음' if abs(z_score) > 3 else '중간'
                })
        
        if not anomalies:
            return pd.DataFrame()
        
        anomaly_df = pd.DataFrame(anomalies)
        return anomaly_df.sort_values('Z-Score', ascending=False)