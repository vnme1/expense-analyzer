"""
반복 거래 관리 모듈
구독료, 월세 등 주기적 거래 자동 생성
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd


class RecurringTransactionManager:
    """반복 거래 관리 클래스"""
    
    FREQUENCY_TYPES = {
        'daily': '매일',
        'weekly': '매주',
        'monthly': '매월',
        'yearly': '매년'
    }
    
    def __init__(self, recurring_file='data/recurring_transactions.json'):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.recurring_file = self.project_root / recurring_file
        self.recurring_list = self.load_recurring()
    
    def load_recurring(self):
        """저장된 반복 거래 불러오기"""
        if self.recurring_file.exists():
            with open(self.recurring_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_recurring(self):
        """반복 거래 저장하기"""
        self.recurring_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.recurring_file, 'w', encoding='utf-8') as f:
            json.dump(self.recurring_list, f, ensure_ascii=False, indent=2)
    
    def add_recurring(self, name, amount, category, frequency, start_date, day_of_execution=1, memo=""):
        """
        반복 거래 추가
        
        Args:
            name: 거래명 (예: 넷플릭스)
            amount: 금액 (음수면 지출, 양수면 수입)
            category: 카테고리
            frequency: 주기 ('daily', 'weekly', 'monthly', 'yearly')
            start_date: 시작 날짜
            day_of_execution: 실행일 (월별: 1-31, 주별: 0-6)
            memo: 메모
            
        Returns:
            dict: 성공 여부 및 메시지
        """
        if not name or not amount or not frequency:
            return {'success': False, 'message': '필수 항목을 입력해주세요'}
        
        if frequency not in self.FREQUENCY_TYPES:
            return {'success': False, 'message': '유효하지 않은 주기입니다'}
        
        recurring = {
            'id': len(self.recurring_list) + 1,
            'name': name,
            'amount': float(amount),
            'category': category,
            'frequency': frequency,
            'start_date': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date),
            'day_of_execution': day_of_execution,
            'memo': memo,
            'active': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.recurring_list.append(recurring)
        self.save_recurring()
        
        return {'success': True, 'message': f'"{name}" 반복 거래가 추가되었습니다'}
    
    def update_recurring(self, recurring_id, **kwargs):
        """반복 거래 수정"""
        for recurring in self.recurring_list:
            if recurring['id'] == recurring_id:
                recurring.update(kwargs)
                self.save_recurring()
                return {'success': True, 'message': '반복 거래가 수정되었습니다'}
        
        return {'success': False, 'message': '반복 거래를 찾을 수 없습니다'}
    
    def delete_recurring(self, recurring_id):
        """반복 거래 삭제"""
        self.recurring_list = [r for r in self.recurring_list if r['id'] != recurring_id]
        self.save_recurring()
        return {'success': True, 'message': '반복 거래가 삭제되었습니다'}
    
    def toggle_active(self, recurring_id):
        """활성/비활성 토글"""
        for recurring in self.recurring_list:
            if recurring['id'] == recurring_id:
                recurring['active'] = not recurring.get('active', True)
                self.save_recurring()
                status = "활성화" if recurring['active'] else "비활성화"
                return {'success': True, 'message': f'반복 거래가 {status}되었습니다'}
        
        return {'success': False, 'message': '반복 거래를 찾을 수 없습니다'}
    
    def get_active_recurring(self):
        """활성화된 반복 거래 목록"""
        return [r for r in self.recurring_list if r.get('active', True)]
    
    def generate_transactions_for_period(self, start_date, end_date):
        """
        특정 기간 동안 발생할 반복 거래 생성
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            list: 생성된 거래 목록
        """
        transactions = []
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        for recurring in self.get_active_recurring():
            recurring_start = pd.to_datetime(recurring['start_date'])
            
            # 시작일이 기간보다 늦으면 스킵
            if recurring_start > end:
                continue
            
            # 실제 시작일 (기간 시작 vs 반복 시작 중 늦은 것)
            actual_start = max(start, recurring_start)
            
            # 주기에 따라 거래 생성
            current_date = actual_start
            
            while current_date <= end:
                # 실행일 계산
                execution_date = self._calculate_execution_date(
                    current_date,
                    recurring['frequency'],
                    recurring.get('day_of_execution', 1)
                )
                
                if start <= execution_date <= end:
                    transactions.append({
                        '날짜': execution_date,
                        '적요': recurring['name'],
                        '금액': recurring['amount'],
                        '분류': recurring['category'],
                        '메모': recurring.get('memo', '') + ' (반복 거래)',
                        'recurring_id': recurring['id']
                    })
                
                # 다음 주기로 이동
                current_date = self._next_period(current_date, recurring['frequency'])
                
                # 무한 루프 방지
                if current_date > end:
                    break
        
        return transactions
    
    def _calculate_execution_date(self, base_date, frequency, day_of_execution):
        """실행일 계산"""
        if frequency == 'daily':
            return base_date
        
        elif frequency == 'weekly':
            # day_of_execution: 0(월) ~ 6(일)
            days_ahead = day_of_execution - base_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return base_date + timedelta(days=days_ahead)
        
        elif frequency == 'monthly':
            # day_of_execution: 1~31
            try:
                return base_date.replace(day=day_of_execution)
            except ValueError:
                # 해당 월에 없는 날짜면 마지막 날
                import calendar
                last_day = calendar.monthrange(base_date.year, base_date.month)[1]
                return base_date.replace(day=min(day_of_execution, last_day))
        
        elif frequency == 'yearly':
            # 매년 같은 날짜
            try:
                return base_date.replace(year=base_date.year)
            except ValueError:
                # 윤년 처리
                return base_date.replace(year=base_date.year, day=28)
        
        return base_date
    
    def _next_period(self, current_date, frequency):
        """다음 주기 계산"""
        if frequency == 'daily':
            return current_date + timedelta(days=1)
        
        elif frequency == 'weekly':
            return current_date + timedelta(weeks=1)
        
        elif frequency == 'monthly':
            # 다음 달 같은 날
            month = current_date.month
            year = current_date.year
            
            if month == 12:
                return current_date.replace(year=year + 1, month=1)
            else:
                return current_date.replace(month=month + 1)
        
        elif frequency == 'yearly':
            return current_date.replace(year=current_date.year + 1)
        
        return current_date
    
    def auto_add_to_csv(self, csv_path, start_date, end_date):
        """
        CSV 파일에 반복 거래 자동 추가
        
        Args:
            csv_path: CSV 파일 경로
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            dict: 추가 결과
        """
        transactions = self.generate_transactions_for_period(start_date, end_date)
        
        if not transactions:
            return {'success': True, 'count': 0, 'message': '추가할 반복 거래가 없습니다'}
        
        try:
            # 기존 CSV 읽기
            if os.path.exists(csv_path):
                existing_df = pd.read_csv(csv_path, encoding='utf-8-sig')
            else:
                existing_df = pd.DataFrame(columns=['날짜', '적요', '금액', '분류', '메모'])
            
            # 새 거래 추가
            new_df = pd.DataFrame(transactions)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # 날짜 정렬
            combined_df['날짜'] = pd.to_datetime(combined_df['날짜'])
            combined_df = combined_df.sort_values('날짜')
            
            # 저장
            combined_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            return {
                'success': True,
                'count': len(transactions),
                'message': f'{len(transactions)}건의 반복 거래가 추가되었습니다'
            }
        
        except Exception as e:
            return {'success': False, 'count': 0, 'message': f'오류 발생: {str(e)}'}
    
    def get_upcoming_transactions(self, days=30):
        """
        향후 N일 동안 발생할 반복 거래 미리보기
        
        Args:
            days: 미리볼 일수
            
        Returns:
            list: 예정 거래 목록
        """
        today = datetime.now()
        end_date = today + timedelta(days=days)
        
        return self.generate_transactions_for_period(today, end_date)