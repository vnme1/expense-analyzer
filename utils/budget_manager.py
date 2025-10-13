"""
예산 관리 모듈 (고급 기능)
- 월별 예산 템플릿
- 자동 갱신
- 월별 비교 그래프
"""
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime


class BudgetManager:
    """예산 관리 클래스"""
    
    def __init__(self, budget_file='data/budgets.json'):
        """
        Args:
            budget_file: 예산 데이터 저장 파일 경로
        """
        self.project_root = Path(__file__).parent.parent
        self.budget_file = self.project_root / budget_file
        self.budgets = self.load_budgets()
    
    def load_budgets(self):
        """저장된 예산 불러오기"""
        if self.budget_file.exists():
            with open(self.budget_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 🆕 기존 형식 호환성 (단순 dict → 새 구조)
                if data and isinstance(list(data.values())[0], (int, float)):
                    return {
                        'default': data,
                        'monthly': {},
                        'auto_reset': False
                    }
                
                return data
        
        return {
            'default': {},      # 기본 예산
            'monthly': {},      # 월별 예산 {'2025-01': {'식비': 300000, ...}, ...}
            'auto_reset': False # 자동 갱신 여부
        }
    
    def save_budgets(self):
        """예산 저장하기"""
        self.budget_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.budget_file, 'w', encoding='utf-8') as f:
            json.dump(self.budgets, f, ensure_ascii=False, indent=2)
    
    def set_budget(self, category, amount, target_month=None):
        """
        카테고리별 예산 설정
        
        Args:
            category: 카테고리명
            amount: 예산 금액
            target_month: 특정 월 (None이면 기본 예산)
        """
        if target_month:
            # 🔥 월을 문자열로 강제 변환
            target_month = str(target_month)
            
            # 월별 예산
            if target_month not in self.budgets['monthly']:
                self.budgets['monthly'][target_month] = {}
            
            self.budgets['monthly'][target_month][category] = float(amount)
        else:
            # 기본 예산
            self.budgets['default'][category] = float(amount)
        
        self.save_budgets()
    
    def get_budget(self, category, target_month=None):
        """
        특정 카테고리의 예산 조회
        
        Args:
            category: 카테고리명
            target_month: 특정 월 (None이면 기본 예산)
            
        Returns:
            float: 예산 금액 (없으면 0)
        """
        if target_month and target_month in self.budgets['monthly']:
            # 월별 예산 우선
            return self.budgets['monthly'][target_month].get(category, 0)
        
        # 기본 예산
        return self.budgets['default'].get(category, 0)
    
    def get_all_budgets(self, target_month=None):
        """
        전체 예산 조회
        
        Args:
            target_month: 특정 월 (None이면 기본 예산)
            
        Returns:
            dict: 예산 딕셔너리
        """
        if target_month and target_month in self.budgets['monthly']:
            return self.budgets['monthly'][target_month].copy()
        
        return self.budgets['default'].copy()
    
    def delete_budget(self, category, target_month=None):
        """
        카테고리 예산 삭제
        
        Args:
            category: 카테고리명
            target_month: 특정 월 (None이면 기본 예산)
        """
        if target_month:
            if target_month in self.budgets['monthly'] and category in self.budgets['monthly'][target_month]:
                del self.budgets['monthly'][target_month][category]
        else:
            if category in self.budgets['default']:
                del self.budgets['default'][category]
        
        self.save_budgets()
    
    def copy_default_to_month(self, target_month):
        """
        기본 예산을 특정 월로 복사
        
        Args:
            target_month: 대상 월 (예: '2025-02')
        """
        if self.budgets['default']:
            self.budgets['monthly'][target_month] = self.budgets['default'].copy()
            self.save_budgets()
    
    def delete_monthly_budget(self, target_month):
        """
        특정 월의 예산 전체 삭제
        
        Args:
            target_month: 대상 월
        """
        if target_month in self.budgets['monthly']:
            del self.budgets['monthly'][target_month]
            self.save_budgets()
    
    def analyze_spending(self, df, target_month=None):
        """
        예산 대비 지출 분석 (전체 또는 월별)
        
        Args:
            df: 거래내역 DataFrame
            target_month: 분석할 월 (예: "2025-01", None이면 전체)
            
        Returns:
            pd.DataFrame: 카테고리별 예산 분석 결과
        """
        expense_df = df[df['구분'] == '지출']
        
        # 월별 필터링
        if target_month:
            expense_df = expense_df[expense_df['년월'] == target_month]
        
        spending = expense_df.groupby('분류')['금액_절대값'].sum()
        
        result = []
        
        # 해당 월의 예산 가져오기
        budgets = self.get_all_budgets(target_month)
        
        for category in budgets.keys():
            budget = budgets[category]
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
    
    def get_alerts(self, df, target_month=None):
        """
        예산 초과 알림 생성
        
        Args:
            df: 거래내역 DataFrame
            target_month: 분석할 월 (None이면 전체)
            
        Returns:
            list: 알림 메시지 리스트
        """
        analysis = self.analyze_spending(df, target_month)
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
    
    def get_monthly_summary(self, df, target_month=None):
        """
        월별 예산 요약
        
        Args:
            df: 거래내역 DataFrame
            target_month: 분석할 월 (None이면 전체)
            
        Returns:
            dict: 월별 예산 요약 정보
        """
        budgets = self.get_all_budgets(target_month)
        total_budget = sum(budgets.values())
        
        expense_df = df[df['구분'] == '지출']
        
        # 월별 필터링
        if target_month:
            expense_df = expense_df[expense_df['년월'] == target_month]
        
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
    
    def get_available_months(self, df):
        """
        데이터에서 사용 가능한 월 목록 조회
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            list: 월 목록 (예: ['2025-01', '2025-02', ...])
        """
        return sorted(df['년월'].unique().tolist())
    
    def get_monthly_comparison(self, df):
        """
        🆕 월별 예산 사용률 비교 데이터
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 월별 비교 데이터
        """
        months = self.get_available_months(df)
        
        comparison_data = []
        
        for month in months:
            summary = self.get_monthly_summary(df, month)
            
            comparison_data.append({
                '월': month,
                '예산': summary['총_예산'],
                '지출': summary['총_지출'],
                '잔여': summary['총_잔여'],
                '사용률(%)': round(summary['전체_사용률'], 1)
            })
        
        return pd.DataFrame(comparison_data)
    
    def set_auto_reset(self, enabled):
        """
        🆕 자동 갱신 설정
        
        Args:
            enabled: True/False
        """
        self.budgets['auto_reset'] = enabled
        self.save_budgets()
    
    def is_auto_reset_enabled(self):
        """자동 갱신 활성화 여부"""
        return self.budgets.get('auto_reset', False)
    
    def check_and_reset_if_needed(self, current_month):
        """
        🆕 자동 갱신 체크 및 실행
        
        Args:
            current_month: 현재 월 (예: '2025-02')
            
        Returns:
            bool: 갱신 실행 여부
        """
        if not self.is_auto_reset_enabled():
            return False
        
        # 해당 월에 예산이 없으면 기본 예산 복사
        if current_month not in self.budgets['monthly'] and self.budgets['default']:
            self.copy_default_to_month(current_month)
            return True
        
        return False
    
    def get_monthly_budgets_list(self):
        """
        🆕 설정된 월별 예산 목록 조회
        
        Returns:
            list: 월 목록
        """
        # 모든 키를 문자열로 변환 후 정렬
        return sorted([str(k) for k in self.budgets['monthly'].keys()])