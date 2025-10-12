"""
저축 목표 관리 모듈
목표 설정, 진행률 추적, 달성 예측
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd


class SavingsGoalManager:
    """저축 목표 관리 클래스"""
    
    def __init__(self, goals_file='data/savings_goals.json'):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.goals_file = self.project_root / goals_file
        self.goals = self.load_goals()
    
    def load_goals(self):
        """저장된 목표 불러오기"""
        if self.goals_file.exists():
            with open(self.goals_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_goals(self):
        """목표 저장하기"""
        self.goals_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.goals_file, 'w', encoding='utf-8') as f:
            json.dump(self.goals, f, ensure_ascii=False, indent=2)
    
    def add_goal(self, name, target_amount, target_date, description=""):
        """
        새 목표 추가
        
        Args:
            name: 목표 이름
            target_amount: 목표 금액
            target_date: 목표 날짜
            description: 설명
            
        Returns:
            dict: 성공 여부 및 메시지
        """
        if not name or not target_amount or not target_date:
            return {'success': False, 'message': '모든 필수 항목을 입력해주세요'}
        
        # 중복 체크
        if any(g['name'] == name for g in self.goals):
            return {'success': False, 'message': f'"{name}" 목표가 이미 존재합니다'}
        
        goal = {
            'id': len(self.goals) + 1,
            'name': name,
            'target_amount': float(target_amount),
            'target_date': target_date.strftime('%Y-%m-%d') if hasattr(target_date, 'strftime') else str(target_date),
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active'
        }
        
        self.goals.append(goal)
        self.save_goals()
        
        return {'success': True, 'message': f'"{name}" 목표가 추가되었습니다', 'goal': goal}
    
    def update_goal(self, goal_id, **kwargs):
        """목표 수정"""
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal.update(kwargs)
                self.save_goals()
                return {'success': True, 'message': '목표가 수정되었습니다'}
        
        return {'success': False, 'message': '목표를 찾을 수 없습니다'}
    
    def delete_goal(self, goal_id):
        """목표 삭제"""
        self.goals = [g for g in self.goals if g['id'] != goal_id]
        self.save_goals()
        return {'success': True, 'message': '목표가 삭제되었습니다'}
    
    def get_active_goals(self):
        """활성화된 목표 목록"""
        return [g for g in self.goals if g.get('status') == 'active']
    
    def calculate_progress(self, goal, df):
        """
        목표 진행률 계산
        
        Args:
            goal: 목표 딕셔너리
            df: 거래내역 DataFrame
            
        Returns:
            dict: 진행률 정보
        """
        # 목표 생성일 이후 데이터만 필터링
        created_date = pd.to_datetime(goal['created_at'])
        target_date = pd.to_datetime(goal['target_date'])
        
        filtered_df = df[df['날짜'] >= created_date]
        
        # 순저축액 계산 (수입 - 지출)
        income = filtered_df[filtered_df['구분'] == '수입']['금액_절대값'].sum()
        expense = filtered_df[filtered_df['구분'] == '지출']['금액_절대값'].sum()
        current_savings = income - expense
        
        # 진행률
        target_amount = goal['target_amount']
        progress_rate = (current_savings / target_amount * 100) if target_amount > 0 else 0
        
        # 남은 기간
        today = datetime.now()
        remaining_days = (target_date - today).days
        
        # 일일 저축 필요액
        remaining_amount = max(0, target_amount - current_savings)
        daily_need = remaining_amount / remaining_days if remaining_days > 0 else 0
        
        # 예상 달성일 (현재 속도 기준)
        elapsed_days = (today - created_date).days
        if elapsed_days > 0 and current_savings > 0:
            daily_rate = current_savings / elapsed_days
            if daily_rate > 0:
                days_to_goal = (target_amount - current_savings) / daily_rate
                estimated_date = today + timedelta(days=days_to_goal)
            else:
                estimated_date = None
        else:
            estimated_date = None
        
        return {
            'current_savings': current_savings,
            'target_amount': target_amount,
            'remaining_amount': remaining_amount,
            'progress_rate': progress_rate,
            'remaining_days': remaining_days,
            'daily_need': daily_need,
            'estimated_date': estimated_date,
            'is_achievable': estimated_date <= target_date if estimated_date else False
        }
    
    def get_all_progress(self, df):
        """모든 활성 목표의 진행률"""
        results = []
        
        for goal in self.get_active_goals():
            progress = self.calculate_progress(goal, df)
            results.append({
                'goal': goal,
                'progress': progress
            })
        
        return results
    
    def mark_as_completed(self, goal_id):
        """목표 완료 처리"""
        return self.update_goal(goal_id, status='completed')
    
    def suggest_monthly_savings(self, goal, current_savings):
        """
        월별 저축 권장액 계산
        
        Args:
            goal: 목표 딕셔너리
            current_savings: 현재 저축액
            
        Returns:
            float: 월별 권장 저축액
        """
        target_date = pd.to_datetime(goal['target_date'])
        today = datetime.now()
        
        remaining_months = max(1, (target_date.year - today.year) * 12 + target_date.month - today.month)
        remaining_amount = goal['target_amount'] - current_savings
        
        return remaining_amount / remaining_months if remaining_months > 0 else remaining_amount