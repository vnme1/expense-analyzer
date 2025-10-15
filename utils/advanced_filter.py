"""
고급 필터 모듈
다중 조건 필터링 및 프리셋 저장
"""
import json
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta


class AdvancedFilter:
    """고급 필터 클래스"""
    
    PRESET_FILTERS = {
        '이번 달': {
            'name': '이번 달',
            'date_from': 'current_month',
            'date_to': 'today'
        },
        '지난 달': {
            'name': '지난 달',
            'date_from': 'last_month_start',
            'date_to': 'last_month_end'
        },
        '최근 7일': {
            'name': '최근 7일',
            'date_from': 'today_minus_7',
            'date_to': 'today'
        },
        '고액 지출': {
            'name': '고액 지출 (10만원 이상)',
            'amount_min': 100000,
            'transaction_type': '지출'
        }
    }
    
    def __init__(self):
        """초기화"""
        pass
    
    def apply_filter(self, df, filter_config):
        """필터 적용"""
        result = df.copy()
        
        # 날짜 필터
        if 'date_from' in filter_config:
            date_from = self._resolve_date(filter_config['date_from'])
            if date_from:
                result = result[result['날짜'] >= date_from]
        
        if 'date_to' in filter_config:
            date_to = self._resolve_date(filter_config['date_to'])
            if date_to:
                result = result[result['날짜'] <= date_to]
        
        # 금액 필터
        if 'amount_min' in filter_config:
            result = result[result['금액_절대값'] >= filter_config['amount_min']]
        
        if 'amount_max' in filter_config:
            result = result[result['금액_절대값'] <= filter_config['amount_max']]
        
        # 카테고리 필터
        if 'categories' in filter_config and filter_config['categories']:
            result = result[result['분류'].isin(filter_config['categories'])]
        
        # 구분 필터
        if 'transaction_type' in filter_config:
            result = result[result['구분'] == filter_config['transaction_type']]
        
        # 검색어 필터
        if 'query' in filter_config and filter_config['query']:
            query = filter_config['query'].lower()
            mask = (
                result['적요'].astype(str).str.lower().str.contains(query, na=False) |
                result.get('메모', pd.Series(['']*len(result))).astype(str).str.lower().str.contains(query, na=False)
            )
            result = result[mask]
        
        return result
    
    def _resolve_date(self, date_value):
        """날짜 표현식 해석"""
        today = pd.Timestamp.now().normalize()
        
        if isinstance(date_value, str):
            if date_value == 'today':
                return today
            elif date_value.startswith('today_minus_'):
                days = int(date_value.split('_')[-1])
                return today - timedelta(days=days)
            elif date_value == 'current_month':
                return today.replace(day=1)
            elif date_value == 'last_month_start':
                first_of_month = today.replace(day=1)
                return first_of_month - pd.DateOffset(months=1)
            elif date_value == 'last_month_end':
                first_of_month = today.replace(day=1)
                return first_of_month - timedelta(days=1)
            else:
                try:
                    return pd.to_datetime(date_value)
                except:
                    return None
        
        return pd.to_datetime(date_value) if date_value else None
    
    def get_quick_filters(self):
        """빠른 필터 버튼용"""
        quick = [
            {'name': '전체', 'icon': '📊', 'config': {}},
            {'name': '이번 달', 'icon': '📅', 'config': self.PRESET_FILTERS['이번 달']},
            {'name': '지난 달', 'icon': '📆', 'config': self.PRESET_FILTERS['지난 달']},
            {'name': '최근 7일', 'icon': '🗓️', 'config': self.PRESET_FILTERS['최근 7일']},
            {'name': '고액 지출', 'icon': '💳', 'config': self.PRESET_FILTERS['고액 지출']}
        ]
        return quick
    
    def get_filter_summary(self, filter_config):
        """필터 요약 텍스트 생성"""
        parts = []
        
        # 날짜
        if 'date_from' in filter_config or 'date_to' in filter_config:
            date_from = self._resolve_date(filter_config.get('date_from'))
            date_to = self._resolve_date(filter_config.get('date_to'))
            
            if date_from and date_to:
                parts.append(f"📅 {date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d')}")
        
        # 금액
        if 'amount_min' in filter_config or 'amount_max' in filter_config:
            amount_min = filter_config.get('amount_min', 0)
            amount_max = filter_config.get('amount_max', float('inf'))
            
            if amount_min > 0 and amount_max < float('inf'):
                parts.append(f"💰 {amount_min:,.0f}원 ~ {amount_max:,.0f}원")
        
        # 카테고리
        if 'categories' in filter_config and filter_config['categories']:
            cats = ', '.join(filter_config['categories'][:3])
            parts.append(f"📂 {cats}")
        
        # 구분
        if 'transaction_type' in filter_config:
            parts.append(f"📊 {filter_config['transaction_type']}")
        
        return ' | '.join(parts) if parts else '필터 없음'
    
    def validate_filter(self, filter_config):
        """필터 설정 유효성 검사"""
        errors = []
        
        # 날짜 유효성
        if 'date_from' in filter_config and 'date_to' in filter_config:
            date_from = self._resolve_date(filter_config['date_from'])
            date_to = self._resolve_date(filter_config['date_to'])
            
            if date_from and date_to and date_from > date_to:
                errors.append('시작 날짜가 종료 날짜보다 늦습니다')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }