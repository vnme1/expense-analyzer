"""
예산 관리 모듈
카테고리별 예산 설정, 추적, 알림 기능
"""
import pandas as pd
import json
import os
from pathlib import Path


class BudgetManager:
    """예산 관리 클래스"""
    
    def __init__(self, budget_file='data/budgets.json'):
        """
        Args:
            budget_file: 예산 데이터 저장 파일 경로
        """
        # 프로젝트 루트 기준 절대 경로 생성
        self.project_root = Path(__file__).parent.parent
        self.budget_file = self.project_root / budget_file
        self.budgets = self.load_budgets()
    
    def load_budgets(self):
        """저장된 예산 불러오기"""
        if self.budget_file.exists():
            with open(self.budget_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_budgets(self):
        """예산 저장하기"""
        self.budget_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.budget_file, 'w', encoding='utf-8') as f:
            json.dump(self.budgets, f, ensure_ascii=False, indent=2)
    
    def set_budget(self, category, amount):
        """
        카테고리별 예산 설정
        
        Args:
            category: 카테고리명
            amount: 예산 금액
        """
        self.budgets[category] = float(amount)
        self.save_budgets()
    
    def get_budget(self, category):
        """
        특정 카테고리의 예산 조회
        
        Args:
            category: 카테고리명
            
        Returns:
            float: 예산 금액 (없으면 0)
        """
        return self.budgets.get(category, 0)
    
    def delete_budget(self, category):
        """
        카테고리 예산 삭제
        
        Args:
            category: 카테고리명
        """
        if category in self.budgets:
            del self.budgets[category]
            self.save_budgets()
    
    def get_all_budgets(self):
        """전체 예산 조회"""
        return self.budgets.copy()
    
    def analyze_spending(self, df):
        """
        예산 대비 지출 분석
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 카테고리별 예산 분석 결과
        """
        expense_df = df[df['구분'] == '지출']
        spending = expense_df.groupby('분류')['금액_절대값'].sum()
        
        result = []
        
        for category in self.budgets.keys():
            budget = self.budgets[category]
            spent = spending.get(category, 0)
            remaining = budget - spent
            usage_rate = (spent / budget * 100) if budget > 0 else 0
            status = self._get_status(usage_rate)
            
            result.append({
                '카테고리': category,
                '예산': budget,
                '지출': spent,
                '잔여': remaining,
                '사용률(%)': round(usage_rate, 1),
                '상태': status
            })
        
        return pd.DataFrame(result)
    
    def _get_status(self, usage_rate):
        """
        사용률에 따른 상태 판정
        
        Args:
            usage_rate: 사용률 (%)
            
        Returns:
            str: 상태 (안전/주의/위험/초과)
        """
        if usage_rate >= 100:
            return '🔴 초과'
        elif usage_rate >= 80:
            return '🟡 위험'
        elif usage_rate >= 60:
            return '🟠 주의'
        else:
            return '🟢 안전'
    
    def get_alerts(self, df):
        """
        예산 초과 알림 생성
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            list: 알림 메시지 리스트
        """
        analysis = self.analyze_spending(df)
        alerts = []
        
        for _, row in analysis.iterrows():
            usage_rate = row['사용률(%)']
            category = row['카테고리']
            
            if usage_rate >= 100:
                over_amount = row['지출'] - row['예산']
                alerts.append({
                    'level': 'error',
                    'category': category,
                    'message': f"🔴 **{category}** 예산 초과! {over_amount:,.0f}원 초과"
                })
            elif usage_rate >= 80:
                alerts.append({
                    'level': 'warning',
                    'category': category,
                    'message': f"🟡 **{category}** 예산의 {usage_rate:.0f}% 사용 중 (위험)"
                })
            elif usage_rate >= 60:
                alerts.append({
                    'level': 'info',
                    'category': category,
                    'message': f"🟠 **{category}** 예산의 {usage_rate:.0f}% 사용 중 (주의)"
                })
        
        return alerts
    
    def get_monthly_summary(self, df):
        """
        월별 예산 요약
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            dict: 월별 예산 요약 정보
        """
        total_budget = sum(self.budgets.values())
        
        expense_df = df[df['구분'] == '지출']
        total_spent = expense_df['금액_절대값'].sum()
        
        total_remaining = total_budget - total_spent
        total_usage_rate = (total_spent / total_budget * 100) if total_budget > 0 else 0
        
        return {
            '총_예산': total_budget,
            '총_지출': total_spent,
            '총_잔여': total_remaining,
            '전체_사용률': total_usage_rate
        }
    
    def suggest_budget(self, df, multiplier=1.2):
        """
        과거 지출 기반 예산 추천
        
        Args:
            df: 거래내역 DataFrame
            multiplier: 평균 대비 여유 비율 (기본 1.2 = 20% 여유)
            
        Returns:
            dict: 카테고리별 추천 예산
        """
        expense_df = df[df['구분'] == '지출']
        
        # 월별 평균 지출 계산
        monthly_avg = expense_df.groupby(['년월', '분류'])['금액_절대값'].sum().groupby('분류').mean()
        
        # 여유분 추가
        suggested = {}
        for category, avg_spent in monthly_avg.items():
            suggested[category] = round(avg_spent * multiplier, -3)
        
        return suggested